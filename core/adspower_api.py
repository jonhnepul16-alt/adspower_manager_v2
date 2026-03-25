"""
AdsPower API Client
Comunica com a API local do AdsPower (http://local.adspower.net:50325)
"""

import requests
import time
from typing import Optional

ADSPOWER_BASE = "http://127.0.0.1:50325"


class AdsPowerAPI:
    def __init__(self, base_url: str = ADSPOWER_BASE, api_key: str = ""):
        self.base_url = base_url
        self.api_key = api_key

    def _get(self, endpoint: str, params: dict = None) -> dict:
        params = params or {}
        if self.api_key:
            params["api_key"] = self.api_key
        try:
            r = requests.get(f"{self.base_url}{endpoint}", params=params, timeout=10)
            return r.json()
        except Exception as e:
            return {"code": -1, "msg": str(e)}

    def _post(self, endpoint: str, data: dict = None) -> dict:
        data = data or {}
        if self.api_key:
            data["api_key"] = self.api_key
        try:
            r = requests.post(f"{self.base_url}{endpoint}", json=data, timeout=10)
            return r.json()
        except Exception as e:
            return {"code": -1, "msg": str(e)}

    # ─── Perfis ────────────────────────────────────────────────
    def list_profiles(self, page: int = 1, page_size: int = 100) -> list[dict]:
        """Retorna lista de perfis cadastrados no AdsPower."""
        res = self._get("/api/v1/user/list", {"page": page, "page_size": page_size})
        if res.get("code") == 0:
            return res.get("data", {}).get("list", [])
        print(f"[ERRO] list_profiles: {res.get('msg')}")
        return []

    def open_browser(self, profile_id: str) -> Optional[dict]:
        """
        Abre o browser de um perfil.
        Retorna dict com 'ws' (WebSocket URL) e 'webdriver' (caminho do chromedriver).
        """
        res = self._get("/api/v1/browser/start", {"user_id": profile_id})
        if res.get("code") == 0:
            return res.get("data")
        print(f"[ERRO] open_browser({profile_id}): {res.get('msg')}")
        return None

    def close_browser(self, profile_id: str) -> bool:
        """Fecha o browser de um perfil."""
        res = self._get("/api/v1/browser/stop", {"user_id": profile_id})
        return res.get("code") == 0

    def browser_status(self, profile_id: str) -> str:
        """Retorna 'Active' ou 'Inactive'."""
        res = self._get("/api/v1/browser/active", {"user_id": profile_id})
        if res.get("code") == 0:
            return res.get("data", {}).get("status", "Inactive")
        return "Inactive"

    def is_running(self) -> bool:
        """Verifica se o AdsPower está rodando."""
        try:
            r = requests.get(f"{self.base_url}/api/v1/browser/active", timeout=5)
            return r.status_code == 200
        except Exception:
            return False
