"""
Facebook Post Task - Versão instantânea
Clica assim que o elemento aparecer, zero sleeps fixos desnecessários.
"""

import os
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

from core.browser_controller import BrowserController


SEL_CAIXA_POST = [
    "[aria-label='No que você está pensando?']",
    "[aria-label='O que você está pensando?']",
    "[aria-label=\"What's on your mind?\"]",
]

SEL_LEGENDA = [
    "div[aria-label='No que você está pensando?'][contenteditable='true']",
    "div[aria-label='O que você está pensando?'][contenteditable='true']",
    "div[aria-label=\"What's on your mind?\"][contenteditable='true']",
    "div[contenteditable='true'][role='textbox']",
    "div[contenteditable='true']",
]

SEL_AVANCAR = [
    "div[aria-label='Avançar']",
    "div[aria-label='Next']",
    "//div[@aria-label='Avançar']",
    "//span[text()='Avançar']",
]

SEL_POSTAR = [
    "div[aria-label='Postar']",
    "div[aria-label='Post']",
    "//div[@aria-label='Postar']",
    "//span[text()='Postar']",
]


def _click(driver, seletores: list, timeout: int = 8) -> bool:
    for sel in seletores:
        try:
            by = By.XPATH if sel.startswith("//") else By.CSS_SELECTOR
            el = WebDriverWait(driver, timeout).until(
                EC.element_to_be_clickable((by, sel))
            )
            driver.execute_script("arguments[0].click();", el)
            return True
        except Exception:
            continue
    return False


def _find(driver, seletores: list, timeout: int = 8):
    for sel in seletores:
        try:
            by = By.XPATH if sel.startswith("//") else By.CSS_SELECTOR
            return WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((by, sel))
            )
        except Exception:
            continue
    return None


def _digitar_legenda(driver, legenda: str):
    campo = _find(driver, SEL_LEGENDA, timeout=6)
    if not campo:
        return False
    driver.execute_script("arguments[0].click();", campo)
    linhas = legenda.split("\n")
    for i, linha in enumerate(linhas):
        ActionChains(driver).send_keys(linha).perform()
        if i < len(linhas) - 1:
            ActionChains(driver).key_down(Keys.SHIFT).send_keys(Keys.ENTER).key_up(Keys.SHIFT).perform()
    return True


def postar_no_facebook(
    browser: BrowserController,
    arquivo: str,
    legenda: str = "",
    timeout_upload: int = 5,
    screenshot_path: str = None,
) -> dict:
    driver = browser.driver

    if not os.path.isabs(arquivo):
        arquivo = os.path.abspath(arquivo)
    if not os.path.exists(arquivo):
        return {"ok": False, "error": f"Arquivo não encontrado: {arquivo}"}

    extensao = os.path.splitext(arquivo)[1].lower()
    tipo = "video" if extensao in [".mp4", ".mov", ".avi", ".mkv", ".webm"] else "foto"

    try:
        # 1. Navega só se não estiver no Facebook
        if "facebook.com" not in driver.current_url:
            print("  → Acessando Facebook...")
            driver.get("https://www.facebook.com/")
        else:
            driver.execute_script("window.scrollTo(0, 0);")

        # 2. Clica na caixa assim que aparecer — sem sleep fixo
        print("  → Abrindo post...")
        if not _click(driver, SEL_CAIXA_POST, timeout=12):
            return {"ok": False, "error": "Caixa de postagem não encontrada."}

        # 3. Upload imediato — expõe input e envia arquivo
        print(f"  → Upload: {os.path.basename(arquivo)}")
        driver.execute_script("""
            document.querySelectorAll('input[type="file"]').forEach(el => {
                el.style.cssText = 'display:block!important;visibility:visible!important;opacity:1!important;';
            });
        """)
        inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='file']")
        if not inputs:
            return {"ok": False, "error": "Input de upload não encontrado."}
        inputs[0].send_keys(arquivo)

        # 4. Aguarda preview da foto aparecer (confirma que upload terminou)
        print("  → Aguardando upload...")
        try:
            WebDriverWait(driver, timeout_upload + 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "img[src*='blob'], img[src*='fbcdn']"))
            )
        except Exception:
            time.sleep(timeout_upload)  # fallback

        # 5. Legenda — digita assim que o campo estiver disponível
        if legenda:
            print("  → Legenda...")
            _digitar_legenda(driver, legenda)

        # 6. Avançar — clica assim que aparecer
        print("  → Avançar...")
        if not _click(driver, SEL_AVANCAR, timeout=8):
            return {"ok": False, "error": "Botão 'Avançar' não encontrado."}

        # 7. Postar — clica assim que aparecer
        print("  → Postar...")
        if not _click(driver, SEL_POSTAR, timeout=8):
            return {"ok": False, "error": "Botão 'Postar' não encontrado."}

        # 8. Aguarda modal fechar (confirma que postou)
        try:
            WebDriverWait(driver, 5).until(
                EC.invisibility_of_element_located((By.CSS_SELECTOR, "div[aria-label='Criar post']"))
            )
        except Exception:
            time.sleep(2)

        # 9. Screenshot opcional
        if screenshot_path:
            os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)
            driver.save_screenshot(screenshot_path)

        print("  ✓ Publicado!")
        return {
            "ok": True,
            "tipo": tipo,
            "arquivo": os.path.basename(arquivo),
            "legenda": legenda[:80] + "..." if len(legenda) > 80 else legenda,
            "url": driver.current_url,
        }

    except Exception as e:
        return {"ok": False, "error": str(e)}
