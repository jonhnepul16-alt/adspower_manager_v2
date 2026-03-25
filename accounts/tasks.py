"""
Tarefas prontas para usar com o AccountManager.

Cada função recebe um BrowserController e retorna um dict com o resultado.
Passe-as para manager.run_task() ou manager.run_on_profiles().

Exemplo de uso:
    from tasks import facebook_check_notifications, capture_page_info
    results = manager.run_on_profiles(["id1", "id2"], facebook_check_notifications)
"""

import time
from core.browser_controller import BrowserController


# ─── Facebook ──────────────────────────────────────────────────────────────────

def facebook_check_notifications(browser: BrowserController) -> dict:
    """Navega para o Facebook e captura o título e URL atual."""
    browser.navigate("https://www.facebook.com/")
    time.sleep(2)
    return {
        "title": browser.get_title(),
        "url": browser.get_url(),
    }


def facebook_open_ads_manager(browser: BrowserController) -> dict:
    """Abre o Gerenciador de Anúncios do Facebook."""
    browser.navigate("https://adsmanager.facebook.com/")
    time.sleep(3)
    return {
        "title": browser.get_title(),
        "url": browser.get_url(),
    }


def facebook_go_to_page(browser: BrowserController, page_url: str) -> dict:
    """Navega para uma página específica do Facebook."""
    browser.navigate(page_url)
    time.sleep(2)
    return {
        "title": browser.get_title(),
        "url": browser.get_url(),
    }


# ─── Captura de dados ──────────────────────────────────────────────────────────

def capture_page_info(browser: BrowserController) -> dict:
    """Captura título, URL e cookies da página atual."""
    return {
        "title": browser.get_title(),
        "url": browser.get_url(),
        "cookies_count": len(browser.get_cookies()),
    }


def capture_screenshot(browser: BrowserController, path: str = "screenshot.png") -> dict:
    """Tira um screenshot da página atual."""
    browser.capture_screenshot(path)
    return {"screenshot": path}


# ─── Formulários ───────────────────────────────────────────────────────────────

def fill_form_example(browser: BrowserController, form_data: dict) -> dict:
    """
    Exemplo genérico de preenchimento de formulário.
    form_data = {"css_selector": "valor_a_digitar", ...}
    """
    for selector, value in form_data.items():
        try:
            browser.type_text("css", selector, value)
        except Exception as e:
            return {"ok": False, "error": f"Erro em '{selector}': {e}"}
    return {"ok": True, "fields_filled": len(form_data)}


# ─── Utilitário: fábrica de tarefas com parâmetros ─────────────────────────────

def task_navigate_to(url: str):
    """Retorna uma task function que navega para a URL informada."""
    def _task(browser: BrowserController) -> dict:
        browser.navigate(url)
        time.sleep(2)
        return {"title": browser.get_title(), "url": browser.get_url()}
    return _task
