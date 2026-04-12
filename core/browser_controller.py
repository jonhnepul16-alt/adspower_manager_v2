"""
Browser Controller
Conecta ao browser aberto pelo AdsPower via Selenium (CDP/WebSocket).
"""

import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class BrowserController:
    def __init__(self, ws_url: str, driver_path: str):
        """
        ws_url      — WebSocket URL retornado pelo AdsPower (ex: ws://127.0.0.1:PORT/devtools/...)
        driver_path — Caminho do chromedriver retornado pelo AdsPower
        """
        opts = Options()
        opts.add_experimental_option("debuggerAddress", ws_url.replace("ws://", "").split("/devtools")[0])

        service = Service(executable_path=driver_path)
        self.driver = webdriver.Chrome(service=service, options=opts)
        self.wait = WebDriverWait(self.driver, 15)

    def navigate(self, url: str):
        """Navega para uma URL."""
        self.driver.get(url)
        time.sleep(1.5)

    def get_title(self) -> str:
        return self.driver.title

    def get_url(self) -> str:
        return self.driver.current_url

    def find(self, by: str, value: str):
        """Aguarda e retorna um elemento."""
        by_map = {
            "css": By.CSS_SELECTOR,
            "xpath": By.XPATH,
            "id": By.ID,
            "name": By.NAME,
            "class": By.CLASS_NAME,
        }
        return self.wait.until(EC.presence_of_element_located((by_map.get(by, By.CSS_SELECTOR), value)))

    def click(self, by: str, value: str):
        el = self.find(by, value)
        el.click()
        time.sleep(0.5)

    def type_text(self, by: str, value: str, text: str, clear_first: bool = True):
        el = self.find(by, value)
        if clear_first:
            el.clear()
        el.send_keys(text)
        time.sleep(0.3)

    def capture_screenshot(self, path: str):
        self.driver.save_screenshot(path)

    def execute_js(self, script: str, *args):
        return self.driver.execute_script(script, *args)

    def get_cookies(self) -> list[dict]:
        return self.driver.get_cookies()

    def scroll_to_bottom(self):
        self.execute_js("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)

    def minimize(self):
        """
        Move a janela para fora da área visível.
        Usado como alternativa ao minimize_window() que causa queda de sessão no AdsPower.
        """
        try:
            print(f"DEBUG: Movendo janela para fora da tela (off-screen workaround)...")
            self.driver.set_window_position(-10000, 0)
        except Exception as e:
            print(f"DEBUG: Erro ao tentar mover janela: {e}")
            pass

    def wait_for_url_contains(self, fragment: str, timeout: int = 15):
        WebDriverWait(self.driver, timeout).until(EC.url_contains(fragment))

    def close(self):

        try:
            self.driver.quit()
        except Exception:
            pass
