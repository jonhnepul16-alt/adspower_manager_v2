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
    def open_account(self, profile_id: str, profile_name: str = "", minimized: bool = False) -> Optional[AccountSession]:
        """Abre o browser de um perfil e retorna a sessão com lógica de retry robusta."""
        log.info(f"🚀 [Manager] Iniciando abertura do perfil {profile_id} ({profile_name}) [Min: {minimized}]")

        # 1. Tentar abrir o browser
        data = self.api.open_browser(profile_id, minimized=minimized)
        
        ws_url = None
        driver_path = None
        
        # 2. Loop de Retry/Captura (6 ciclos de 2s = 10s totais)
        for attempt in range(6):
            log.info(f"🔍 [Manager] DEBUG RAW Resposta AdsPower (Tentativa {attempt}): {data}")
            
            if isinstance(data, dict):
                # Caso comum: os dados estão em data['data']
                chunk = data.get("data")
                if isinstance(chunk, dict) and "ws" in chunk:
                    ws_url = chunk.get("ws", {}).get("selenium")
                    driver_path = chunk.get("webdriver")
                
                # Caso alternativo: o AdsPower retornou os dados no nível raiz (flattened)
                elif "ws" in data:
                    ws_url = data.get("ws", {}).get("selenium")
                    driver_path = data.get("webdriver")

                # Verificações de mensagens de erro
                msg = str(data.get("msg", "")).lower()
                if "limit" in msg:
                    raise Exception("Exceeding AdsPower daily open limit")

            # FALLBACK: Se ainda não temos os dados, consultamos o endpoint /active explicitamente
            if not ws_url or not driver_path:
                if attempt > 0: # Não precisa na primeira tentativa se o start já resolveu
                    log.info(f"⏳ [Manager] Dados incompletos. Consultando endpoint /active como fallback...")
                    active_data = self.api.browser_status(profile_id)
                    log.info(f"🔍 [Manager] DEBUG RAW Fallback /active: {active_data}")
                    
                    if isinstance(active_data, dict) and "ws" in active_data:
                        ws_url = active_data.get("ws", {}).get("selenium")
                        driver_path = active_data.get("webdriver")

            if ws_url and driver_path:
                log.info(f"✅ [Manager] Dados de conexão capturados com sucesso.")
                break
            
            if attempt < 5:
                log.warning(f"⚠️ [Manager] Socket Selenium não disponível para {profile_id}. Aguardando 2s... ({attempt+1}/5)")
                time.sleep(2)
                # Na próxima tentativa o loop usará o retorno do status mais recente se disponível
                # ou repetirá a consulta ao start no primeiro loop (já feito acima via fallback)
            else:
                log.error(f"❌ [Manager] Falha definitiva ao obter socket para o perfil {profile_id}.")
                return None

        # 3. Conectar o Selenium
        max_retries = 3
        for attempt_conn in range(max_retries):
            try:
                log.info(f"🔌 [Manager] Conectando Selenium (Tentativa {attempt_conn + 1}/{max_retries})...")
                session = AccountSession(profile_id, profile_name or profile_id)
                session.browser = BrowserController(ws_url, driver_path)
                session.status = "idle"
                self.sessions[profile_id] = session
                
                # Verify connection
                title = session.browser.get_title()
                log.info(f"✨ [Manager] Perfil {profile_id} CONECTADO. Título: {title}")

                if minimized:
                    log.info(f"📉 [Manager] Garantindo janela minimizada...")
                    time.sleep(1)
                    session.browser.minimize()

                return session
            except Exception as e:
                log.warning(f"⚠️ [Manager] Erro na conexão Selenium: {e}")
                if attempt_conn < max_retries - 1:
                    time.sleep(3)
                else:
                    log.error(f"❌ [Manager] Falha final na conexão: {e}")
                    return None
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
