"""
Account Manager
Orquestra múltiplas contas: abre perfis no AdsPower, conecta o Selenium,
executa tarefas e fecha com segurança.
"""

import json
import os
import time
import logging
import sys
from datetime import datetime
from typing import Callable, Optional

from core.adspower_api import AdsPowerAPI
from core.browser_controller import BrowserController

# Configure log saving safely for Pyinstaller environments
if getattr(sys, 'frozen', False):
    application_path = os.path.dirname(sys.executable)
else:
    application_path = os.path.join(os.path.dirname(__file__), "..")

LOG_DIR = os.path.join(application_path, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(LOG_DIR, "manager.log"), encoding="utf-8"),
    ],
)
log = logging.getLogger("AccountManager")


class AccountSession:
    """Representa uma sessão ativa de uma conta."""

    def __init__(self, profile_id: str, profile_name: str):
        self.profile_id = profile_id
        self.profile_name = profile_name
        self.browser: Optional[BrowserController] = None
        self.opened_at = datetime.now()
        self.status = "idle"  # idle | running | done | error

    def __repr__(self):
        return f"<AccountSession id={self.profile_id} name={self.profile_name} status={self.status}>"


class AccountManager:
    def __init__(self, base_url: str = "http://127.0.0.1:50325", api_key: str = ""):
        self.api = AdsPowerAPI(base_url, api_key)
        self.sessions: dict[str, AccountSession] = {}

    # ─── Verificações ──────────────────────────────────────────────
    def check_adspower(self) -> bool:
        if not self.api.is_running():
            log.error("AdsPower não está rodando. Inicie o AdsPower antes de continuar.")
            return False
        log.info("AdsPower detectado e ativo.")
        return True

    # ─── Perfis ───────────────────────────────────────────────────
    def list_profiles(self) -> list[dict]:
        profiles = self.api.list_profiles()
        log.info(f"{len(profiles)} perfis encontrados.")
        return profiles

    # ─── Abrir conta ──────────────────────────────────────────────
    def open_account(self, profile_id: str, profile_name: str = "") -> Optional[AccountSession]:
        """Abre o browser de um perfil e retorna a sessão."""
        log.info(f"Abrindo perfil {profile_id} ({profile_name})...")

        data = self.api.open_browser(profile_id)
        
        # Check for specific AdsPower rate limits / fail-safe
        if data is None:
            log.error(f"Falha ao abrir perfil {profile_id}. Unknown API error.")
            return None
            
        # Often raw api returns something if it fails. The apic in `adspower_api.py` returns `res.get("data")` 
        # Wait, if code != 0, it logs and returns None. We need to catch this. Let's fix adspower_api.py to return the full dict if possible, or we raise exception here if None, but we need to know the MSG.
        # For now, if data is None, we'll try to guess or use the new adspower_api format we will implement.
        if isinstance(data, dict) and data.get("code") == -1 and "limit" in str(data.get("msg", "")).lower():
            raise Exception("Exceeding open daily limit")
            
        if not data or (isinstance(data, dict) and "ws" not in data):
            log.error(f"Falha ao abrir perfil {profile_id}. {data}")
            return None

        ws_url = data.get("ws", {}).get("selenium")
        driver_path = data.get("webdriver")

        if not ws_url or not driver_path:
            log.error(f"Dados de conexão incompletos para {profile_id}: {data}")
            return None

        try:
            session = AccountSession(profile_id, profile_name or profile_id)
            session.browser = BrowserController(ws_url, driver_path)
            session.status = "idle"
            self.sessions[profile_id] = session
            log.info(f"Perfil {profile_id} conectado. Título: {session.browser.get_title()}")
            return session
        except Exception as e:
            log.error(f"Erro ao conectar Selenium ao perfil {profile_id}: {e}")
            self.api.close_browser(profile_id)
            return None

    # ─── Fechar conta ─────────────────────────────────────────────
    def close_account(self, profile_id: str):
        session = self.sessions.get(profile_id)
        if session and session.browser:
            session.browser.close()
        self.api.close_browser(profile_id)
        self.sessions.pop(profile_id, None)
        log.info(f"Perfil {profile_id} fechado.")

    def close_all(self):
        for pid in list(self.sessions.keys()):
            self.close_account(pid)

    # ─── Executar tarefa em uma conta ─────────────────────────────
    def run_task(self, profile_id: str, task_fn: Callable[[BrowserController], dict]) -> dict:
        """
        Executa uma função de tarefa numa sessão aberta.
        task_fn recebe o BrowserController e deve retornar dict com resultado.
        """
        session = self.sessions.get(profile_id)
        if not session or not session.browser:
            return {"ok": False, "error": "Sessão não encontrada ou browser fechado."}

        session.status = "running"
        try:
            result = task_fn(session.browser)
            session.status = "done"
            log.info(f"[{profile_id}] Tarefa concluída: {result}")
            return {"ok": True, **result}
        except Exception as e:
            session.status = "error"
            log.error(f"[{profile_id}] Erro na tarefa: {e}")
            return {"ok": False, "error": str(e)}

    # ─── Executar em múltiplos perfis ─────────────────────────────
    def run_on_profiles(
        self,
        profile_ids: list[str],
        task_fn: Callable[[BrowserController], dict],
        delay_between: float = 2.0,
        close_after: bool = True,
    ) -> dict[str, dict]:
        """
        Abre cada perfil, executa a tarefa e opcionalmente fecha.
        Retorna dict {profile_id: resultado}.
        """
        profiles_map = {p["user_id"]: p.get("name", p["user_id"]) for p in self.list_profiles()}
        results = {}

        for pid in profile_ids:
            name = profiles_map.get(pid, pid)
            session = self.open_account(pid, name)
            if not session:
                results[pid] = {"ok": False, "error": "Não foi possível abrir o perfil."}
                continue

            results[pid] = self.run_task(pid, task_fn)

            if close_after:
                self.close_account(pid)

            if delay_between > 0 and pid != profile_ids[-1]:
                log.info(f"Aguardando {delay_between}s antes do próximo perfil...")
                time.sleep(delay_between)

        return results

    # ─── Relatório ────────────────────────────────────────────────
    def save_report(self, results: dict, filename: str = None):
        filename = filename or f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        path = os.path.join(LOG_DIR, filename)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        log.info(f"Relatório salvo em: {path}")
        return path
