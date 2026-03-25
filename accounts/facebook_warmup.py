import json
import os
import sys
import time
import random
import datetime

from core.account_manager import AccountManager

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

# ═══════════════════════════════════════════════════════════════
#  BANNER E CONSTANTES
# ═══════════════════════════════════════════════════════════════
BANNER = """
╔══════════════════════════════════════════════════════╗
║        FACEBOOK WARMUP BOT — CONTINGÊNCIA PRO        ║
║     [ADSPOWER + SELENIUM  |  v3.4 — FAST SCROLL]     ║
╚══════════════════════════════════════════════════════╝
"""

FRASES_STATUS = [
    "O sucesso é a soma de pequenos esforços! 🙏",
    "Foco e determinação todos os dias.",
    "Progredindo um pouco de cada vez.",
    "Que a semana seja de muita produtividade! 💪",
    "Seguimos firmes no objetivo. 🚀",
    "Cada dia é uma nova oportunidade de crescer!",
    "Consistência é a chave do sucesso. 🔑",
    "Trabalho duro sempre vale a pena! 💼",
]

PALAVRAS_BUSCA = [
    "viagens", "tecnologia", "saúde", "receitas", "futebol",
    "música", "cinema", "natureza", "empreendedorismo", "fitness",
    "fotografia", "culinária", "games", "ciência", "animais",
]

CATEGORIAS_MARKETPLACE = [
    "vehicles", "propertyrentals", "electronics",
    "furniture", "clothing", "garden", "sports", "hobbies",
]

FRASES_DISPONIVEL = [
    "Olá, isso ainda está disponível?",
    "Hi, is this still available?",
    "Hola, ¿esto todavía está disponible?",
]

LIVE_TEMPO_POR_MODO = {
    "Rápido":  (1 * 60,   2 * 60),
    "Padrão":  (8 * 60,  12 * 60),
    "Intenso": (18 * 60, 25 * 60),
}

MARKETPLACE_TEMPO_POR_MODO = {
    "Rápido":  (50,      80),
    "Padrão":  (2 * 60,  4 * 60),
    "Intenso": (4 * 60,  6 * 60),
}

GAMING_TEMPO_POR_MODO = {
    "Rápido":  (1 * 60,   2 * 60),
    "Padrão":  (5 * 60,   7 * 60),
    "Intenso": (15 * 60, 20 * 60),
}

CTA_AD_TEXTOS = [
    "Saiba mais", "Saiba más", "Learn More",
    "Comprar", "Shop Now", "Reservar",
]

FEED_TEMPO_POR_MODO = {
    "Rápido":  (4 * 60,   5 * 60),
    "Padrão":  (12 * 60, 15 * 60),
    "Intenso": (25 * 60, 30 * 60),
}

BUSCA_SCROLL_DURACAO = (30, 45)

MODOS_TEMPO = {
    "1": ("Rápido",   10 * 60),
    "2": ("Padrão",   30 * 60),
    "3": ("Intenso",  60 * 60),
}

FAST_PULL_MIN_PX          = 1500
FAST_PULL_MAX_PX          = 2000
POSTS_ANTES_REVERSO_MIN   = 10
POSTS_ANTES_REVERSO_MAX   = 15
REVERSO_MAX_PX            = 300
PROB_LEITURA_LONGA        = 0.05
LEITURA_LONGA_MIN         = 3.0
LEITURA_LONGA_MAX         = 5.0
PROB_CURTIR_FAST          = 0.10


# ═══════════════════════════════════════════════════════════════
#  UTILITÁRIOS BASE
# ═══════════════════════════════════════════════════════════════

def extrair_driver(controller):
    for attr in ("driver", "browser"):
        candidate = getattr(controller, attr, None)
        if candidate and hasattr(candidate, "get"):
            return candidate
    if hasattr(controller, "get"):
        return controller
    raise AttributeError(
        f"Não foi possível extrair o WebDriver de {type(controller).__name__}."
    )


def human_type(element, texto: str, delay_min=0.05, delay_max=0.22):
    for char in texto:
        element.send_keys(char)
        time.sleep(random.uniform(delay_min, delay_max))


def micro_move_before_click(driver, element):
    try:
        ac = ActionChains(driver)
        ac.move_to_element_with_offset(
            element, random.randint(-8, 8), random.randint(-5, 5)
        )
        time.sleep(random.uniform(0.15, 0.4))
        ac.move_to_element(element)
        time.sleep(random.uniform(0.1, 0.3))
        ac.click().perform()
    except Exception:
        driver.execute_script("arguments[0].click();", element)


def _clicar_robusto(driver, elemento):
    try:
        micro_move_before_click(driver, elemento)
        return True
    except Exception:
        pass
    try:
        driver.execute_script("arguments[0].click();", elemento)
        return True
    except Exception:
        pass
    try:
        elemento.send_keys(Keys.RETURN)
        return True
    except Exception:
        return False


def micro_movimentos_sobre_elemento(driver, elemento, duracao: float):
    try:
        ActionChains(driver).move_to_element(elemento).perform()
        fim = time.time() + duracao
        while time.time() < fim:
            dx, dy = random.randint(-5, 5), random.randint(-4, 4)
            try:
                ActionChains(driver).move_by_offset(dx, dy).perform()
            except Exception:
                pass
            time.sleep(random.uniform(0.3, 1.0))
        ActionChains(driver).move_to_element(elemento).perform()
    except Exception:
        pass


def barra_progresso(elapsed: float, total: float, largura: int = 40):
    progresso = min(elapsed / total, 1.0)
    preenchido = int(largura * progresso)
    barra = "█" * preenchido + "░" * (largura - preenchido)
    restante = max(total - elapsed, 0)
    m, s = int(restante // 60), int(restante % 60)
    print(
        f"\r  ⏱  [{barra}] {progresso*100:5.1f}%  |  Restam: {m:02d}m{s:02d}s   ",
        end="", flush=True,
    )


# ═══════════════════════════════════════════════════════════════
#  RELATÓRIO
# ═══════════════════════════════════════════════════════════════

def salvar_relatorio(pid: str, resultado: dict, modo: str):
    os.makedirs("relatorios", exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    nome_arquivo = os.path.join("relatorios", f"relatorio_{pid}_{ts}.txt")

    live_s    = resultado.get("tempo_live_total", 0)
    live_fmt  = f"{int(live_s // 60)}m{int(live_s % 60):02d}s"
    gaming_s  = resultado.get("tempo_gaming_real", 0)
    gaming_fmt = f"{int(gaming_s // 60)}m{int(gaming_s % 60):02d}s"
    feed_s   = resultado.get("tempo_total_feed", 0)
    feed_fmt = f"{int(feed_s // 60)}m{int(feed_s % 60):02d}s"
    busca_s  = resultado.get("tempo_gasto_na_busca", 0)
    busca_fmt = f"{int(busca_s // 60)}m{int(busca_s % 60):02d}s"
    dist_px = resultado.get("distancia_total_scrollada", 0)
    dist_cm = dist_px / 96 / 0.393701

    linhas = [
        "=" * 56,
        f"  RELATÓRIO DE AQUECIMENTO — {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
        "=" * 56,
        f"  Perfil (ID)              : {pid}",
        f"  Modo selecionado         : {modo}",
        f"  Status geral             : {'✓ OK' if resultado.get('ok') else '✗ ERRO'}",
        "-" * 56,
        f"  Tempo total no Feed      : {feed_fmt}",
        f"  Curtidas no Feed         : {resultado.get('curtidas_feed', 0)}",
        f"  Reels assistidos         : {resultado.get('reels_assistidos', 0)}",
        f"  Reels curtidos           : {resultado.get('reels_curtidos', 0)}",
        f"  Busca nicho concluída    : {'Sim' if resultado.get('busca_nicho_concluida') else 'Não'}",
        f"  Tempo gasto na busca     : {busca_fmt}",
        f"  Tempo assistindo Live    : {live_fmt}",
        f"  Tempo FB Gaming          : {gaming_fmt}",
        f"  Ads clicados (feed)      : {resultado.get('ads_clicados', 0)}",
        f"  Ads clicados por CTA     : {resultado.get('ads_clicados_por_cta', 0)}",
        f"  Ads clicados na varredura: {resultado.get('anuncios_clicados_na_varredura', 0)}",
        f"  Distância total scrollada: {dist_px:,} px (~{dist_cm:.0f} cm)",
        f"  Itens Marketplace vistos : {resultado.get('itens_marketplace_vistos', 0)}",
        f"  Interação Comercial      : {'Sim' if resultado.get('interacao_comercial_messenger') else 'Não'}",
        f"  Postagem feita           : {'Sim' if resultado.get('postagem') else 'Não'}",
        f"  Ciclos completos         : {resultado.get('ciclos', 0)}",
    ]
    if not resultado.get("ok"):
        linhas.append(f"  Erro registrado          : {resultado.get('error', 'N/A')}")
    linhas.append("=" * 56 + "\n")

    with open(nome_arquivo, "w", encoding="utf-8") as f:
        f.write("\n".join(linhas))

    print(f"\n  📄 Relatório salvo em: {nome_arquivo}")


# ═══════════════════════════════════════════════════════════════
#  HC-1 — CHECK DE NOTIFICAÇÕES
# ═══════════════════════════════════════════════════════════════

def check_notificacoes(driver, wait):
    print("\n  🔔 [HC-1] Verificando notificações...")
    try:
        sino = None
        try:
            sino = WebDriverWait(driver, 6).until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, '/notifications')]"))
            )
        except Exception:
            pass

        if sino is None:
            for sel in [
                "//div[@aria-label='Notificações']",
                "//div[@aria-label='Notifications']",
                "//a[@aria-label='Notificações']",
                "//a[@aria-label='Notifications']",
            ]:
                try:
                    sino = WebDriverWait(driver, 3).until(
                        EC.element_to_be_clickable((By.XPATH, sel))
                    )
                    break
                except Exception:
                    continue

        if sino is None:
            try:
                svg_elem = driver.find_element(By.CSS_SELECTOR, "a[href*='notifications'] svg")
                sino = driver.execute_script(
                    "return arguments[0].closest('a, [role=\"button\"]');", svg_elem
                )
            except Exception:
                pass

        if sino is None:
            print("    ✗ Sininho não encontrado. Pulando.")
            return

        if not _clicar_robusto(driver, sino):
            print("    ✗ Clique no sininho falhou.")
            return

        print("    ✓ Painel de notificações aberto.")
        time.sleep(random.uniform(4, 7))

        fechou = False
        for sel_fora in [
            "//a[@aria-label='Facebook']",
            "//div[@data-pagelet='LeftRail']",
        ]:
            try:
                fora = driver.find_element(By.XPATH, sel_fora)
                ActionChains(driver).move_to_element(fora).click().perform()
                fechou = True
                break
            except Exception:
                continue

        if not fechou:
            try:
                ActionChains(driver).move_by_offset(65, 65).click().perform()
                ActionChains(driver).move_by_offset(-65, -65).perform()
            except Exception:
                pass

        print("    ✓ Notificações fechadas.")
        time.sleep(random.uniform(1.5, 3.0))
    except Exception as e:
        print(f"    ✗ Falha no check de notificações: {e}")


# ═══════════════════════════════════════════════════════════════
#  HC-2 — SCROLL COM LEITURA SIMULADA
# ═══════════════════════════════════════════════════════════════

def scroll_com_leitura_simulada(driver):
    print("\n  👁  [HC-2] Scroll com simulação de leitura...")
    contador_scrolls = 0
    try:
        for _ in range(random.randint(4, 7)):
            driver.execute_script(f"window.scrollBy(0, {random.randint(300, 600)});")
            contador_scrolls += 1
            time.sleep(random.uniform(1.2, 2.5))

            if contador_scrolls % 3 == 0:
                reverso_px = random.randint(300, 500)
                driver.execute_script(f"window.scrollBy(0, -{reverso_px});")
                time.sleep(random.uniform(1.5, 3.0))
                try:
                    ver_mais_btns = driver.find_elements(
                        By.XPATH,
                        "//div[@role='button' and (contains(text(),'Ver mais') or contains(text(),'See more'))]",
                    )
                    if ver_mais_btns:
                        micro_move_before_click(driver, random.choice(ver_mais_btns[:3]))
                        time.sleep(random.uniform(3.0, 6.0))
                except Exception:
                    pass
                driver.execute_script(f"window.scrollBy(0, {random.randint(300, 500)});")
                time.sleep(random.uniform(1.0, 2.0))

            try:
                posts_texto = driver.find_elements(
                    By.XPATH,
                    "//div[@data-ad-comet-preview='message' or @data-ad-preview='message']",
                )
                posts_longos = [p for p in posts_texto if len(p.text.strip()) > 120]
                if posts_longos and random.random() < 0.65:
                    alvo = random.choice(posts_longos[:3])
                    micro_movimentos_sobre_elemento(driver, alvo, random.uniform(4.0, 9.0))
            except Exception:
                pass

            time.sleep(random.uniform(0.8, 1.8))
        print("    ✓ Scroll com leitura concluído.")
    except Exception as e:
        print(f"    ✗ Falha no scroll com leitura: {e}")


# ═══════════════════════════════════════════════════════════════
#  DEEP COMMENTS
# ═══════════════════════════════════════════════════════════════

def task_deep_comments(driver, wait, resultados: dict, **_):
    if random.random() > 0.40:
        return
    print("\n  ▶ [HC-DC] Deep Comments — explorando comentários...")
    try:
        driver.get("https://www.facebook.com/")
        time.sleep(random.uniform(4, 6))
        for _ in range(3):
            driver.execute_script(f"window.scrollBy(0, {random.randint(400, 700)});")
            time.sleep(random.uniform(1.5, 2.5))

        contador_cmts = None
        for sel in [
            "//span[contains(text(),' comentário')]",
            "//span[contains(text(),' comment')]",
            "//a[contains(@href, 'comment')]",
        ]:
            try:
                elementos = driver.find_elements(By.XPATH, sel)
                candidatos = [e for e in elementos if any(c.isdigit() for c in e.text)]
                if candidatos:
                    contador_cmts = random.choice(candidatos[:3])
                    break
            except Exception:
                continue

        if contador_cmts is None:
            print("    · Nenhum post com comentários encontrado. Pulando.")
            return

        micro_move_before_click(driver, contador_cmts)
        time.sleep(random.uniform(3, 5))

        fim_cmt = time.time() + random.uniform(18, 23)
        while time.time() < fim_cmt:
            driver.execute_script(f"window.scrollBy(0, {random.randint(100, 250)});")
            time.sleep(random.uniform(1.8, 3.5))

        try:
            ActionChains(driver).send_keys(Keys.ESCAPE).perform()
        except Exception:
            pass
        print("    ✓ Comentários explorados.")
    except Exception as e:
        print(f"    ✗ Falha no Deep Comments: {e}")


# ═══════════════════════════════════════════════════════════════
#  UTILITÁRIO CTA
# ═══════════════════════════════════════════════════════════════

def _tentar_cta_em_tela(driver, resultados: dict) -> bool:
    condicoes_cta = " or ".join([f"normalize-space(text())='{t}'" for t in CTA_AD_TEXTOS])
    xpath_cta = (
        f"//div[@role='button' and ({condicoes_cta})]"
        f" | //a[@role='button' and ({condicoes_cta})]"
        f" | //span[{condicoes_cta}]/ancestor::div[@role='button'][1]"
    )
    try:
        candidatos = driver.find_elements(By.XPATH, xpath_cta)
        visiveis = [c for c in candidatos if c.is_displayed() and c.size.get("height", 0) > 0]
        if not visiveis:
            return False

        btn_cta = random.choice(visiveis[:3])
        driver.execute_script(
            "arguments[0].scrollIntoView({behavior:'smooth',block:'center'});", btn_cta
        )
        time.sleep(random.uniform(1.2, 2.0))
        print("    👁  Anúncio CTA detectado — lendo por 5s...")
        try:
            ActionChains(driver).move_to_element(btn_cta).perform()
        except Exception:
            pass
        time.sleep(random.uniform(4.5, 5.5))

        url_antes = driver.current_url
        micro_move_before_click(driver, btn_cta)
        time.sleep(random.uniform(2, 4))

        if driver.current_url != url_antes:
            print("    ✓ Navegando ~20s no site do anúncio...")
            fim_ext = time.time() + random.uniform(18, 24)
            while time.time() < fim_ext:
                driver.execute_script(f"window.scrollBy(0, {random.randint(200, 420)});")
                time.sleep(random.uniform(2.0, 4.0))
            driver.back()
            time.sleep(random.uniform(3, 5))
            resultados["ads_clicados_por_cta"] = resultados.get("ads_clicados_por_cta", 0) + 1
            return True
    except Exception:
        pass
    return False


# ═══════════════════════════════════════════════════════════════
#  TAREFA A — FAST-SCROLL DE FEED
# ═══════════════════════════════════════════════════════════════

def task_curtir_feed(driver, wait, resultados: dict, nome_modo: str = "Padrão", **_):
    t_min, t_max = FEED_TEMPO_POR_MODO.get(nome_modo, (4 * 60, 5 * 60))
    duracao_feed = random.uniform(t_min, t_max)
    print(f"\n  ▶ [A] Fast-Scroll Feed ({nome_modo}) — {duracao_feed / 60:.1f} min...")

    inicio_feed     = time.time()
    scroll_contador = 0
    limite_reverso  = random.randint(POSTS_ANTES_REVERSO_MIN, POSTS_ANTES_REVERSO_MAX)
    distancia_total = 0
    ads_varredura   = 0

    try:
        driver.get("https://www.facebook.com/")
        time.sleep(random.uniform(4, 7))

        while time.time() - inicio_feed < duracao_feed:
            if random.random() < 0.30:
                px = random.randint(FAST_PULL_MIN_PX, FAST_PULL_MAX_PX)
                driver.execute_script(f"window.scrollBy(0, {px});")
                distancia_total += px
                print(f"    ⚡ Puxada rápida: {px}px")
                time.sleep(random.uniform(0.6, 1.2))
            else:
                px = random.randint(400, 700)
                driver.execute_script(f"window.scrollBy(0, {px});")
                distancia_total += px
                time.sleep(random.uniform(0.8, 1.5))

            scroll_contador += 1
            dado = random.random()

            if dado < PROB_CURTIR_FAST:
                try:
                    like_btns = driver.find_elements(
                        By.XPATH,
                        "//div[@aria-label='Curtir' or @aria-label='Like' or @aria-label='Me gusta']",
                    )
                    nao_curtidos = [b for b in like_btns if b.get_attribute("aria-pressed") in (None, "false", "")]
                    if nao_curtidos:
                        micro_move_before_click(driver, random.choice(nao_curtidos[:3]))
                        resultados["curtidas_feed"] = resultados.get("curtidas_feed", 0) + 1
                        print(f"    ❤  Post curtido (total: {resultados['curtidas_feed']})")
                        time.sleep(random.uniform(0.8, 1.5))
                except Exception:
                    pass
            elif dado < PROB_CURTIR_FAST + PROB_LEITURA_LONGA:
                pausa = random.uniform(LEITURA_LONGA_MIN, LEITURA_LONGA_MAX)
                time.sleep(pausa)

            clicou = _tentar_cta_em_tela(driver, resultados)
            if clicou:
                ads_varredura += 1
                resultados["anuncios_clicados_na_varredura"] = resultados.get("anuncios_clicados_na_varredura", 0) + 1

            if scroll_contador >= limite_reverso:
                px_up = random.randint(150, REVERSO_MAX_PX)
                driver.execute_script(f"window.scrollBy(0, -{px_up});")
                distancia_total += px_up
                print(f"    ↑ Reverso curto: {px_up}px")
                time.sleep(random.uniform(0.8, 1.5))
                scroll_contador = 0
                limite_reverso = random.randint(POSTS_ANTES_REVERSO_MIN, POSTS_ANTES_REVERSO_MAX)

        tempo_feed = time.time() - inicio_feed
        resultados["tempo_total_feed"] = resultados.get("tempo_total_feed", 0) + tempo_feed
        resultados["distancia_total_scrollada"] = resultados.get("distancia_total_scrollada", 0) + distancia_total
        print(f"    ✓ Feed encerrado: {tempo_feed / 60:.1f} min | {distancia_total:,} px")
    except Exception as e:
        print(f"    ✗ Falha no Feed: {e}")


# ═══════════════════════════════════════════════════════════════
#  TAREFA B — REELS
# ═══════════════════════════════════════════════════════════════

def task_reels_watch(driver, wait, resultados: dict, **_):
    print("\n  ▶ [B] Assistindo Reels...")
    try:
        driver.get("https://www.facebook.com/reel/")
        time.sleep(random.uniform(7, 10))
        qtd = random.randint(2, 4)
        for i in range(qtd):
            watch_time = random.uniform(11, 20)
            print(f"    ► Reel {i+1}/{qtd} — {watch_time:.0f}s...")
            try:
                like_reel = driver.find_elements(
                    By.XPATH,
                    "//div[@aria-label='Curtir' or @aria-label='Like' or @aria-label='Me gusta']",
                )
                if like_reel and random.random() < 0.30:
                    micro_move_before_click(driver, like_reel[-1])
                    resultados["reels_curtidos"] = resultados.get("reels_curtidos", 0) + 1
            except Exception:
                pass
            time.sleep(watch_time)
            resultados["reels_assistidos"] = resultados.get("reels_assistidos", 0) + 1
            try:
                driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ARROW_DOWN)
                time.sleep(random.uniform(1.5, 3.0))
            except Exception:
                driver.execute_script("window.scrollBy(0, 650);")
                time.sleep(random.uniform(1.5, 3.0))
    except Exception as e:
        print(f"    ✗ Falha nos Reels: {e}")


# ═══════════════════════════════════════════════════════════════
#  TAREFA C — BUSCA RÁPIDA POR NICHO
# ═══════════════════════════════════════════════════════════════

def task_busca_aleatoria(driver, wait, resultados: dict, **_):
    if resultados.get("busca_nicho_concluida"):
        return
    termo = random.choice(PALAVRAS_BUSCA)
    print(f"\n  ▶ [C] Busca por '{termo}'...")
    inicio_busca = time.time()
    try:
        driver.get("https://www.facebook.com/")
        time.sleep(random.uniform(3, 5))

        barra = None
        for sel in [
            "//input[@aria-label='Pesquisar no Facebook']",
            "//input[@aria-label='Search Facebook']",
            "//input[@placeholder='Pesquisar no Facebook']",
            "//input[@type='search']",
        ]:
            try:
                barra = wait.until(EC.element_to_be_clickable((By.XPATH, sel)))
                break
            except Exception:
                continue

        if barra is None:
            print("    ✗ Barra de busca não encontrada.")
            return

        micro_move_before_click(driver, barra)
        human_type(barra, termo)
        time.sleep(random.uniform(0.8, 1.5))
        barra.send_keys(Keys.RETURN)
        time.sleep(random.uniform(4, 6))

        duracao_varredura = random.uniform(*BUSCA_SCROLL_DURACAO)
        fim_varredura = time.time() + duracao_varredura
        scroll_busca = 0
        limite_rev_bus = random.randint(8, 12)
        dist_busca = 0

        while time.time() < fim_varredura:
            px = random.randint(350, 600)
            driver.execute_script(f"window.scrollBy(0, {px});")
            dist_busca += px
            scroll_busca += 1
            time.sleep(random.uniform(0.5, 1.0))
            _tentar_cta_em_tela(driver, resultados)
            if scroll_busca >= limite_rev_bus:
                driver.execute_script(f"window.scrollBy(0, -{random.randint(100, 200)});")
                scroll_busca = 0
                limite_rev_bus = random.randint(8, 12)

        resultados["busca_nicho_concluida"] = True
        resultados["tempo_gasto_na_busca"] = time.time() - inicio_busca
        resultados["distancia_total_scrollada"] = resultados.get("distancia_total_scrollada", 0) + dist_busca
        print(f"    ✓ Busca '{termo}' concluída.")
    except Exception as e:
        print(f"    ✗ Falha na busca: {e}")


# ═══════════════════════════════════════════════════════════════
#  TAREFA D — WATCH LIVE
# ═══════════════════════════════════════════════════════════════

def task_watch_live(driver, wait, resultados: dict, nome_modo: str = "Padrão", **_):
    print(f"\n  ▶ [D] Assistindo Live ({nome_modo})...")
    try:
        driver.get("https://www.facebook.com/watch/live/")
        time.sleep(random.uniform(6, 9))
        t_min, t_max = LIVE_TEMPO_POR_MODO.get(nome_modo, (3 * 60, 5 * 60))
        duracao_live = random.uniform(t_min, t_max)
        print(f"    ⏱  {duracao_live / 60:.1f} min...")

        player = None
        for sel in ["//video", "//div[@data-pagelet='WatchLiveFeed']"]:
            try:
                player = driver.find_element(By.XPATH, sel)
                break
            except Exception:
                continue

        inicio_live = time.time()
        ultimo_move = inicio_live
        while time.time() - inicio_live < duracao_live:
            if time.time() - ultimo_move >= 40:
                if player:
                    micro_movimentos_sobre_elemento(driver, player, 3.0)
                ultimo_move = time.time()
            time.sleep(random.uniform(4, 8))

        resultados["tempo_live_total"] = resultados.get("tempo_live_total", 0) + (time.time() - inicio_live)
        print(f"    ✓ Live assistida.")
    except Exception as e:
        print(f"    ✗ Falha na live: {e}")


# ═══════════════════════════════════════════════════════════════
#  TAREFA E — MARKETPLACE + MESSENGER
# ═══════════════════════════════════════════════════════════════

def task_marketplace_messenger(driver, wait, resultados: dict, **_):
    if resultados.get("interacao_comercial_messenger"):
        return
    if random.random() > 0.20:
        return
    print("\n    💬 [MKT-MSG] Tentando contato com vendedor...")
    try:
        btn_msg = None
        for sel in [
            "//div[@aria-label='Enviar mensagem ao vendedor']",
            "//a[@aria-label='Enviar mensagem ao vendedor']",
            "//div[@aria-label='Send message to seller']",
        ]:
            try:
                btn_msg = WebDriverWait(driver, 4).until(EC.element_to_be_clickable((By.XPATH, sel)))
                break
            except Exception:
                continue

        if btn_msg is None:
            return

        micro_move_before_click(driver, btn_msg)
        time.sleep(random.uniform(3.0, 5.0))

        input_chat = None
        for sel_chat in [
            "//div[@role='textbox' and @contenteditable='true']",
            "//div[@aria-label='Mensagem' and @role='textbox']",
            "//div[@aria-label='Message' and @role='textbox']",
        ]:
            try:
                input_chat = WebDriverWait(driver, 6).until(EC.element_to_be_clickable((By.XPATH, sel_chat)))
                break
            except Exception:
                continue

        if input_chat is None:
            return

        idioma = driver.execute_script("return document.documentElement.lang;")
        frase = "Hi, is this still available?" if idioma and "en" in idioma.lower() else "Olá, isso ainda está disponível?"
        micro_move_before_click(driver, input_chat)
        human_type(input_chat, frase)
        time.sleep(random.uniform(1.0, 2.0))
        input_chat.send_keys(Keys.RETURN)
        time.sleep(random.uniform(10, 15))
        resultados["interacao_comercial_messenger"] = True
        print(f'    ✓ Mensagem enviada: "{frase}"')
        try:
            ActionChains(driver).send_keys(Keys.ESCAPE).perform()
        except Exception:
            pass
    except Exception as e:
        print(f"    ✗ Falha no Messenger: {e}")


def task_marketplace_browse(driver, wait, resultados: dict, nome_modo: str = "Padrão", **_):
    categoria = random.choice(CATEGORIAS_MARKETPLACE)
    print(f"\n  ▶ [E] Marketplace — '{categoria}'...")
    try:
        driver.get(f"https://www.facebook.com/marketplace/category/{categoria}/")
        time.sleep(random.uniform(5, 8))
        itens = driver.find_elements(By.XPATH, "//a[contains(@href, '/marketplace/item/')]")
        if not itens:
            return
        item = random.choice(itens[:10])
        _clicar_robusto(driver, item)
        time.sleep(random.uniform(4, 7))

        t_min, t_max = MARKETPLACE_TEMPO_POR_MODO.get(nome_modo, (60, 180))
        fim_mp = time.time() + random.uniform(t_min, t_max)
        while time.time() < fim_mp:
            driver.execute_script(f"window.scrollBy(0, {random.randint(200, 450)});")
            time.sleep(random.uniform(2.0, 4.5))

        task_marketplace_messenger(driver, wait, resultados)
        resultados["itens_marketplace_vistos"] = resultados.get("itens_marketplace_vistos", 0) + 1
        print("    ✓ Item visualizado.")
    except Exception as e:
        print(f"    ✗ Falha no Marketplace: {e}")


# ═══════════════════════════════════════════════════════════════
#  TAREFA F — CONSUMIDOR VIP (CTA)
# ═══════════════════════════════════════════════════════════════

def task_interact_ad(driver, wait, resultados: dict, **_):
    if random.random() > 0.30:
        return
    print("\n  ▶ [F] Procurando anúncio por CTA...")
    try:
        driver.get("https://www.facebook.com/")
        time.sleep(random.uniform(5, 7))
        condicoes_cta = " or ".join([f"normalize-space(text())='{t}'" for t in CTA_AD_TEXTOS])
        xpath_cta = f"//div[@role='button' and ({condicoes_cta})] | //span[{condicoes_cta}]/ancestor::div[@role='button'][1]"

        btn_cta = None
        for _ in range(5):
            driver.execute_script(f"window.scrollBy(0, {random.randint(400, 700)});")
            time.sleep(random.uniform(1.5, 2.5))
            try:
                candidatos = driver.find_elements(By.XPATH, xpath_cta)
                visiveis = [c for c in candidatos if c.is_displayed() and c.size.get("height", 0) > 0]
                if visiveis:
                    btn_cta = random.choice(visiveis[:3])
                    break
            except Exception:
                continue

        if btn_cta is None:
            print("    · Nenhum CTA encontrado.")
            return

        driver.execute_script("arguments[0].scrollIntoView({behavior:'smooth',block:'center'});", btn_cta)
        time.sleep(random.uniform(1.5, 2.5))
        try:
            ActionChains(driver).move_to_element(btn_cta).perform()
        except Exception:
            pass
        time.sleep(random.uniform(4.5, 5.5))

        url_antes = driver.current_url
        micro_move_before_click(driver, btn_cta)
        time.sleep(random.uniform(2, 4))

        if driver.current_url != url_antes:
            fim_ad = time.time() + random.uniform(18, 24)
            while time.time() < fim_ad:
                driver.execute_script(f"window.scrollBy(0, {random.randint(200, 420)});")
                time.sleep(random.uniform(2.0, 4.0))
            driver.back()
            time.sleep(random.uniform(3, 5))
            resultados["ads_clicados_por_cta"] = resultados.get("ads_clicados_por_cta", 0) + 1
            print(f"    ✓ CTA clicado (total: {resultados['ads_clicados_por_cta']}).")
    except Exception as e:
        print(f"    ✗ Falha no CTA: {e}")


# ═══════════════════════════════════════════════════════════════
#  TAREFA G — POSTAGEM DE STATUS
# ═══════════════════════════════════════════════════════════════

def task_postagem_status(driver, wait, resultados: dict, **_):
    print("\n  ▶ [G] Publicando status...")
    try:
        driver.get("https://www.facebook.com/")
        time.sleep(random.uniform(5, 7))
        texto = random.choice(FRASES_STATUS)

        post_box = None
        for sel in [
            "//span[contains(text(), 'pensando')]",
            "//span[contains(text(), 'thinking')]",
            "//div[@aria-label='Criar publicação']",
        ]:
            try:
                post_box = wait.until(EC.element_to_be_clickable((By.XPATH, sel)))
                break
            except Exception:
                continue

        if post_box is None:
            print("    ✗ Caixa de postagem não encontrada.")
            return

        micro_move_before_click(driver, post_box)
        time.sleep(random.uniform(1.5, 2.5))
        txt_area = wait.until(EC.presence_of_element_located((By.XPATH, "//div[@role='textbox']")))
        human_type(txt_area, texto)
        time.sleep(random.uniform(2.0, 3.5))

        btn_pub = None
        for sel in ["//div[@aria-label='Publicar']", "//div[@aria-label='Post']"]:
            try:
                btn_pub = driver.find_element(By.XPATH, sel)
                break
            except Exception:
                continue

        if btn_pub:
            micro_move_before_click(driver, btn_pub)
            resultados["postagem"] = True
            print(f'    ✓ Status publicado: "{texto}"')
        time.sleep(random.uniform(4, 7))
    except Exception as e:
        print(f"    ✗ Falha na postagem: {e}")


# ═══════════════════════════════════════════════════════════════
#  TAREFA H — FACEBOOK GAMING
# ═══════════════════════════════════════════════════════════════

def task_facebook_gaming(driver, wait, resultados: dict, nome_modo: str = "Padrão", **_):
    print(f"\n  ▶ [H] Facebook Gaming ({nome_modo})...")
    try:
        driver.get("https://www.facebook.com/gaming")
        time.sleep(random.uniform(6, 9))

        live_card = None
        for sel in [
            "//a[.//span[contains(translate(text(),'live','LIVE'),'LIVE')]]",
            "//a[.//span[contains(text(),'AO VIVO')]]",
            "//a[contains(@href,'/live/') and contains(@href,'gaming')]",
            "//a[contains(@href,'/videos/')]",
        ]:
            try:
                candidatos = driver.find_elements(By.XPATH, sel)
                if candidatos:
                    live_card = random.choice(candidatos[:5])
                    break
            except Exception:
                continue

        if live_card is None:
            print("    · Nenhuma live encontrada. Pulando.")
            return

        _clicar_robusto(driver, live_card)
        time.sleep(random.uniform(5, 8))

        player = None
        for sel_p in ["//video", "//div[@data-pagelet='VideoContainer']"]:
            try:
                player = driver.find_element(By.XPATH, sel_p)
                break
            except Exception:
                continue

        t_min, t_max = GAMING_TEMPO_POR_MODO.get(nome_modo, (2 * 60, 4 * 60))
        duracao_gaming = random.uniform(t_min, t_max)
        print(f"    ⏱  {duracao_gaming / 60:.1f} min...")

        inicio_g = time.time()
        ultimo_move_g = inicio_g
        while time.time() - inicio_g < duracao_gaming:
            if time.time() - ultimo_move_g >= 40:
                if player:
                    micro_movimentos_sobre_elemento(driver, player, 3.0)
                ultimo_move_g = time.time()
            time.sleep(random.uniform(4, 8))

        resultados["tempo_gaming_real"] = resultados.get("tempo_gaming_real", 0) + (time.time() - inicio_g)
        print(f"    ✓ Gaming concluído.")
    except Exception as e:
        print(f"    ✗ Falha no Gaming: {e}")


# ═══════════════════════════════════════════════════════════════
#  LOOP PRINCIPAL DE AQUECIMENTO
# ═══════════════════════════════════════════════════════════════

def facebook_warmup_por_tempo(controller, duracao_segundos: int, nome_modo: str):
    driver = extrair_driver(controller)
    wait   = WebDriverWait(driver, 25)

    resultados = {
        "curtidas_feed": 0, "reels_assistidos": 0, "reels_curtidos": 0,
        "buscas": 0, "busca_nicho_concluida": False, "tempo_gasto_na_busca": 0,
        "tempo_live_total": 0, "tempo_gaming_real": 0, "tempo_total_feed": 0,
        "ads_clicados": 0, "ads_clicados_por_cta": 0, "anuncios_clicados_na_varredura": 0,
        "distancia_total_scrollada": 0, "itens_marketplace_vistos": 0,
        "interacao_comercial_messenger": False, "postagem": False, "ciclos": 0, "ok": True,
    }

    ctx = {"nome_modo": nome_modo}
    tarefas_ciclicas = [
        task_curtir_feed, task_reels_watch, task_busca_aleatoria,
        task_watch_live, task_marketplace_browse, task_interact_ad,
        task_deep_comments, task_facebook_gaming,
    ]

    postagem_feita = False
    inicio = time.time()
    print(f"\n  🕐 Modo {nome_modo} — {duracao_segundos // 60} min")
    print("  " + "─" * 54)

    try:
        driver.get("https://www.facebook.com/")
        time.sleep(random.uniform(4, 6))
        check_notificacoes(driver, wait)
        time.sleep(random.uniform(2, 4))

        while True:
            elapsed = time.time() - inicio
            if elapsed >= duracao_segundos:
                break

            barra_progresso(elapsed, duracao_segundos)
            random.shuffle(tarefas_ciclicas)
            resultados["ciclos"] += 1

            for tarefa in tarefas_ciclicas:
                elapsed = time.time() - inicio
                if elapsed >= duracao_segundos:
                    break
                barra_progresso(elapsed, duracao_segundos)
                tarefa(driver, wait, resultados, **ctx)
                time.sleep(random.uniform(3, 8))

            elapsed = time.time() - inicio
            if not postagem_feita and (duracao_segundos - elapsed) <= duracao_segundos * 0.20:
                task_postagem_status(driver, wait, resultados)
                postagem_feita = True

        barra_progresso(duracao_segundos, duracao_segundos)
        print()
    except Exception as e:
        resultados["ok"] = False
        resultados["error"] = str(e)
        print(f"\n  ✗ Erro: {e}")

    return resultados
