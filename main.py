import json
import os
import sys
import time
import random
import datetime
from typing import Callable

# ── GLOBAL CLOUD BRIDGE (v5.0 Native Redirect) ──────────────────────────
# O print agora é capturado globalmente pelo gui_agent.py via sys.stdout redirect.

_LOG_CALLBACK = None

def set_log_callback(callback: Callable[[str], None]):
    """Define o callback para enviar logs ao dashboard/painel."""
    global _LOG_CALLBACK
    _LOG_CALLBACK = callback

def log(msg: str, **kwargs):
    """Printa no console e envia para o callback do painel se existir."""
    print(msg, **kwargs)
    if _LOG_CALLBACK:
        try:
            # Garante que seja string e remove caracteres excedentes
            clean_msg = str(msg).strip()
            if clean_msg:
                _LOG_CALLBACK(clean_msg)
        except:
            pass
# ────────────────────────────────────────────────────────────────────────

from core.account_manager import AccountManager  # type: ignore


from selenium.webdriver.common.by import By  # type: ignore
from selenium.webdriver.common.keys import Keys  # type: ignore
from selenium.webdriver.support.ui import WebDriverWait  # type: ignore
from selenium.webdriver.support import expected_conditions as EC  # type: ignore
from selenium.webdriver.common.action_chains import ActionChains  # type: ignore

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

# ── CONSTANTES DE FAST SCROLLING (v3.4) ─────────────────────────────────────
FAST_PULL_MIN_PX          = 1500   # px mínimo de puxada rápida
FAST_PULL_MAX_PX          = 2000   # px máximo de puxada rápida
POSTS_ANTES_REVERSO_MIN   = 10     # mín. de descidas antes de 1 reverso
POSTS_ANTES_REVERSO_MAX   = 15     # máx. de descidas antes de 1 reverso
REVERSO_MAX_PX            = 300    # reverso máximo (px) — muito curto
PROB_LEITURA_LONGA        = 0.05   # 5 % de chance de parar p/ leitura
LEITURA_LONGA_MIN         = 3.0    # pausa mínima de leitura (s)
LEITURA_LONGA_MAX         = 5.0    # pausa máxima de leitura (s)
PROB_CURTIR_FAST          = 0.10   # 10 % de chance de curtir no scroll

# ── REAÇÕES (distribuição baseada em dados reais — Quintly/Facebook) ──────────
# Like ~50%, Love ~30%, Haha ~10%, Wow ~5%, Sad ~3%, Angry ~2%
REACOES_POPULACAO = (
    ["Like"]  * 50 +
    ["Love"]  * 30 +
    ["Haha"]  * 10 +
    ["Wow"]   * 5  +
    ["Sad"]   * 3  +
    ["Angry"] * 2
)

# aria-label do botão de cada reação (PT-BR, EN, ES)
REACAO_ARIA = {
    "Like":  ["Curtir",   "Like",   "Me gusta"],
    "Love":  ["Amei",     "Love",   "Me encanta"],
    "Haha":  ["Haha",     "Haha",   "Haha"],
    "Wow":   ["Uau",      "Wow",    "Asombrado"],
    "Sad":   ["Triste",   "Sad",    "Triste"],
    "Angry": ["Grr",      "Angry",  "Enfadado"],
}

# ── COMENTÁRIOS ────────────────────────────────────────────────────────────────
COMENTARIOS_POSTS = [
    "Que incrível! 😍", "Adorei isso!", "Muito bom mesmo! 👏",
    "Hahaha que situação kkkk", "Que coisa linda!", "Top demais! 🔥",
    "Isso é real demais 😂", "Mandou bem!", "Que legal isso!",
    "Perfeito! ✨", "Vai fundo! 💪", "Sensacional!", "Que momento lindo!",
    "Não tava preparado pra isso kkkk", "Amei! ❤️", "Muito fofo!",
    "Que notícia boa!", "Isso mesmo! 👊", "Compartilhei com os amigos!",
    "Boa sorte! 🍀", "Demais! 😄", "Que saudade dessa época 😅",
    "Perfeito, exatamente o que eu precisava ver hoje!", "Kkkkk que exagero 😂",
]

# ── GRUPOS ─────────────────────────────────────────────────────────────────────
GRUPOS_NICHO = [
    "empreendedorismo brasil", "receitas caseiras", "fitness e saúde",
    "tecnologia brasil", "viagens baratas", "mães de primeira viagem",
    "games brasil", "música independente", "fotografia digital",
    "finanças pessoais", "culinária saudável", "carros e motos brasil",
]

GRUPOS_TEMPO_POR_MODO = {
    "Rápido":  (40,  80),
    "Padrão":  (90,  150),
    "Intenso": (180, 240),
}

# ═══════════════════════════════════════════════════════════════
#  HUMAN ENGINE — PERSONA & BEHAVIOR
# ═══════════════════════════════════════════════════════════════

class SessionPersona:
    def __init__(self, profile_id):
        # Semente baseada no ID e data para consistência diária com mutação sutil
        seed_str = f"{profile_id}_{datetime.datetime.now().strftime('%Y%p')}" # Muda a cada 12h (AM/PM)
        self.rng = random.Random(seed_str)
        
        self.profile_id = profile_id
        self.mood = self.rng.random()      # 0=Ranzinza/Inativo, 1=Feliz/Interativo
        self.energy = self.rng.random()    # 0=Lento/Preguiçoso, 1=Rápido/Ativo
        self.curiosity = self.rng.random() # 0=Superficial, 1=Explorador
        
        # Métricas de execução avançadas
        self.misclick_rate = self.rng.uniform(0.01, 0.05)
        self.indecision_rate = self.rng.uniform(0.05, 0.12)
        self.contradiction_index = self.rng.uniform(0.1, 0.15) # Chance de agir contra a 'lógica'
        
        # Estilo de Bootstrap (LIGHT, MEDIUM, HEAVY)
        self.bootstrap_type = self.rng.choice(["LIGHT", "MEDIUM", "HEAVY"])
        self.bootstrap_intensity = {"LIGHT": 0.2, "MEDIUM": 0.5, "HEAVY": 0.9}[self.bootstrap_type]
        
        self.early_exit_chance = 0.03 if self.rng.random() < 0.1 else 0.0
        self.patience = self.rng.uniform(0.5, 1.6)
        
        # Interesses (amostra de palavras-chave)
        num_int = self.rng.randint(2, 5)
        self.interests = self.rng.sample(PALAVRAS_BUSCA, min(num_int, len(PALAVRAS_BUSCA)))

    def get_delay(self, base_delay):
        """Ajusta um delay fixo pela paciência da persona e variação randômica."""
        return base_delay * self.patience * random.uniform(0.8, 1.2)

    def check_misclick(self):
        """Retorna True se deve ocorrer um erro de clique nesta ação."""
        return random.random() < self.misclick_rate

    def check_indecision(self):
        """Retorna True se deve hesitar ou desistir de uma ação."""
        return random.random() < self.indecision_rate

    def should_contradict(self):
        """Retorna True se deve agir de forma 'não-lógica' agora."""
        return random.random() < self.contradiction_index

def human_sleep(duration, driver=None):
    """Substitui o time.sleep por uma pausa 'viva', com micro-movimentos."""
    if duration <= 0: return
    start_t = time.time()
    
    # Se a pausa for curta, apenas dorme
    if duration < 3:
        time.sleep(duration)
        return

    while time.time() - start_t < duration:
        remaining = duration - (time.time() - start_t)
        if remaining <= 0: break
        
        # Atividade visual (mouse drift ou micro-scroll)
        dice = random.random()
        if driver and dice < 0.20:
            try:
                ac = ActionChains(driver)
                if dice < 0.15: # Mouse Drift
                    ac.move_by_offset(random.randint(-2, 2), random.randint(-1, 1)).perform()
                else: # Micro-scroll (tremidinha de leitura)
                    offset = random.choice([-15, 15])
                    driver.execute_script(f"window.scrollBy({{top: {offset}, behavior: 'smooth'}});")
                    time.sleep(0.3)
                    driver.execute_script(f"window.scrollBy({{top: {-offset}, behavior: 'smooth'}});")
            except: pass
            
        # Dorme em pequenos chunks para manter responsividade e atividade
        sleep_chunk = min(remaining, random.uniform(1.2, 3.5))
        time.sleep(sleep_chunk)

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
        f"Não foi possível extrair o WebDriver de {type(controller).__name__}. "
        "Verifique os atributos disponíveis no objeto retornado pelo AdsPower."
    )


def human_type(element, texto: str, delay_min=0.05, delay_max=0.22):
    """Digita letra por letra com pausas aleatórias (anti-ban)."""
    # Filtra caracteres fora do range BMP (Chrome/Selenium limit)
    safe_text = "".join(c for c in texto if ord(c) <= 0xFFFF)
    for char in safe_text:
        element.send_keys(char)
        time.sleep(random.uniform(delay_min, delay_max))


def micro_move_before_click(driver, element, persona=None):
    """Micro-movimentos de mouse antes de clicar num elemento (com noise engine avançado)."""
    try:
        # Hesitação ou Desistência (Persona indecisa)
        if persona and persona.check_indecision():
            print(f"    🤔 [Noise] Hesitando sobre a ação...")
            ac = ActionChains(driver)
            ac.move_to_element_with_offset(element, random.randint(-10, 10), random.randint(-10, 10))
            ac.perform()
            time.sleep(random.uniform(1.2, 2.5))
            if random.random() < 0.3: # 30% de chance de desistir da ação após hesitar
                print("    ↪️ [Noise] Desistiu da ação por indecisão.")
                return False

        # Se a persona estiver presente e o RNG de misclick bater
        if persona and persona.check_misclick():
            print(f"    🌪️ [Noise] Erro de precisão (Misclick)...")
            ac = ActionChains(driver)
            ac.move_to_element_with_offset(element, random.randint(18, 28), random.randint(12, 22))
            ac.click().perform()
            time.sleep(random.uniform(0.6, 1.4))
            print(f"    🤔 [Noise] Corrigindo e clicando novamente...")
            
        ac = ActionChains(driver)
        ac.move_to_element_with_offset(element, random.randint(-5, 5), random.randint(-3, 3))
        time.sleep(random.uniform(0.2, 0.4))
        ac.click().perform()
        return True
    except Exception:
        try:
            driver.execute_script("arguments[0].click();", element)
            return True
        except: return False


def _clicar_robusto(driver, elemento, persona=None):
    """3 camadas de clique em cascata com integração de persona e desidência."""
    try:
        success = micro_move_before_click(driver, elemento, persona)
        if not success: return False # Foi uma desistência proposital
        return True
    except Exception: pass
    # ... fallback via JS
    try:
        driver.execute_script("arguments[0].click();", elemento)
        return True
    except: return False


def micro_movimentos_sobre_elemento(driver, elemento, duracao: float):
    """
    Mantém o mouse sobre um elemento com micro-movimentos aleatórios
    durante `duracao` segundos.
    """
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
    """Barra de progresso visual no console."""
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
    """Salva relatório detalhado em relatorios/relatorio_<pid>_<ts>.txt"""
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
    dist_cm = dist_px / 96 / 0.393701   # px → pol → cm

    linhas = [
        "=" * 56,
        f"  RELATÓRIO DE AQUECIMENTO — "
        f"{datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
        "=" * 56,
        f"  Perfil (ID)              : {pid}",
        f"  Modo selecionado         : {modo}",
        f"  Status geral             : "
        f"{'✓ OK' if resultado.get('ok') else '✗ ERRO'}",
        "-" * 56,
        f"  Tempo total no Feed      : {feed_fmt}",
        f"  Curtidas no Feed         : {resultado.get('curtidas_feed', 0)}",
        f"  Reações no Feed          : {resultado.get('reacoes_dadas', 0)}",
        f"  Comentários feitos       : {resultado.get('comentarios_feitos', 0)}",
        f"  Reels assistidos         : {resultado.get('reels_assistidos', 0)}",
        f"  Reels curtidos           : {resultado.get('reels_curtidos', 0)}",
        f"  Busca nicho concluída    : "
        f"{'Sim' if resultado.get('busca_nicho_concluida') else 'Não'}",
        f"  Tempo gasto na busca     : {busca_fmt}",
        f"  Tempo assistindo Live    : {live_fmt}",
        f"  Tempo FB Gaming          : {gaming_fmt}",
        f"  Ads clicados (feed)      : {resultado.get('ads_clicados', 0)}",
        f"  Ads clicados por CTA     : {resultado.get('ads_clicados_por_cta', 0)}",
        f"  Ads clicados na varredura: {resultado.get('anuncios_clicados_na_varredura', 0)}",
        f"  Distância total scrollada: {dist_px:,} px (~{dist_cm:.0f} cm)",
        f"  Itens Marketplace vistos : "
        f"{resultado.get('itens_marketplace_vistos', 0)}",
        f"  Exploração de Grupos     : {resultado.get('grupos_visitados', 0)}",
        f"  Amigos adicionados       : {resultado.get('amigos_adicionados', 0)}",
        f"  Interação Comercial      : "
        f"{'Sim' if resultado.get('interacao_comercial_messenger') else 'Não'}",
        f"  Postagem feita           : "
        f"{'Sim' if resultado.get('postagem') else 'Não'}",
        f"  Ciclos completos         : {resultado.get('ciclos', 0)}",
    ]
    if not resultado.get("ok"):
        linhas.append(f"  Erro registrado          : {resultado.get('error', 'N/A')}")
    linhas.append("=" * 56 + "\n")

    with open(nome_arquivo, "w", encoding="utf-8") as f:
        f.write("\n".join(linhas))

    print(f"\n  📄 Relatório salvo em: {nome_arquivo}")


# ═══════════════════════════════════════════════════════════════
#  HC-1 — CHECK DE NOTIFICAÇÕES (SININHO)
# ═══════════════════════════════════════════════════════════════

def check_notificacoes(driver, wait):
    log("\n  🔔 [HC-1] Verificando notificações...")
    try:
        sino = None

        try:
            sino = WebDriverWait(driver, 6).until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//a[contains(@href, '/notifications')]")
                )
            )
        except Exception:
            pass

        if sino is None:
            for sel in [
                "//a[contains(@href, 'notifications')]",
                "//div[contains(@aria-label, 'Notific')]",
                "//a[contains(@aria-label, 'Notific')]",
                "//div[contains(@aria-label, 'Notification')]",
                "//a[contains(@aria-label, 'Notification')]",
                "//div[@role='button']//span[contains(text(), 'Notifica')]/ancestor::div[@role='button'][1]",
                "//a//span[contains(text(), 'Notifica')]/ancestor::a[1]",
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
                svg_elem = driver.find_element(
                    By.CSS_SELECTOR, "a[href*='notifications'] svg"
                )
                sino = driver.execute_script(
                    "return arguments[0].closest('a, [role=\"button\"]');",
                    svg_elem,
                )
            except Exception:
                pass

        if sino is None:
            log("    ✗ Sininho não encontrado. Pulando.")
            return

        if not _clicar_robusto(driver, sino):
            log("    ✗ Clique no sininho falhou.")
            return

        log("    ✓ Painel de notificações aberto.")
        time.sleep(random.uniform(4, 7))

        fechou = False
        for sel_fora in [
            "//a[@aria-label='Facebook']",
            "//div[@data-pagelet='LeftRail']",
            "//div[@aria-label='Facebook']",
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

        log("    ✓ Notificações fechadas.")
        time.sleep(random.uniform(1.5, 3.0))

    except Exception as e:
        log(f"    ✗ Falha no check de notificações: {e}")


# ═══════════════════════════════════════════════════════════════
#  ADVANCED HC HELPERS (POOL OF 9)
# ═══════════════════════════════════════════════════════════════

def ruido_humano(driver, intensidade="media"):
    """HC-8: Simula distração humana com atividade visual persistente."""
    pausas = {"baixa": (3, 6), "media": (6, 12), "alta": (12, 25)}
    t_min, t_max = pausas.get(intensidade, (5, 10))
    duracao = random.uniform(t_min, t_max)
    
    print(f"    ⏳ [Distração] Pausa humana de {duracao:.1f}s...")
    human_sleep(duracao, driver)

def scroll_humano_avancado(driver, pixels_objetivo=None):
    """HC-2: Scroll realista com variação de velocidade, pausa e reverso."""
    if pixels_objetivo is None:
        pixels_objetivo = random.randint(1500, 3000)
    
    print(f"    ↕  [Scroll] Realizando scroll avançado (~{pixels_objetivo}px)...")
    scrollado = 0
    while scrollado < pixels_objetivo:
        # Define um passo (chunk) de scroll
        passo = random.randint(300, 700)
        # 15% de chance de ser um scroll rápido (puxada)
        if random.random() < 0.15:
            passo = random.randint(1000, 1500)
            
        driver.execute_script(f"window.scrollBy(0, {passo});")
        scrollado += passo
        time.sleep(random.uniform(1.0, 2.5))
        
        # 10% de chance de "Over-scroll" (Erro de scroll exagerado)
        if random.random() < 0.10:
            over = random.randint(800, 1500)
            print(f"      🔃 [Noise] Over-scroll: +{over}px")
            driver.execute_script(f"window.scrollBy(0, {over});")
            time.sleep(random.uniform(1.2, 2.2))
            # Corrige o over-scroll
            driver.execute_script(f"window.scrollBy(0, -{over - random.randint(50, 200)});")
            print(f"      🔧 [Noise] Corrigindo posição após over-scroll.")
            time.sleep(random.uniform(1.0, 2.0))

        # 20% de chance de scroll reverso (releitura ou dúvida)
        if random.random() < 0.20:
            voltar = random.randint(200, 450)
            print(f"      ↑ [Dúvida] Scroll reverso: -{voltar}px")
            driver.execute_script(f"window.scrollBy(0, -{voltar});")
            scrollado -= voltar
            time.sleep(random.uniform(2.0, 4.0))
            
        # 30% de chance de "Parada Contemplativa" (olhando algo)
        if random.random() < 0.30:
            pausa = random.uniform(3.0, 6.0)
            print(f"      👀 [Foco] Parada contemplativa ({pausa:.1f}s)")
            human_sleep(pausa, driver)

def gestao_indecisao(driver, prob=0.15):
    """HC-1: Simula indecisão (entrar e sair rápido ou quase clicar)."""
    if random.random() < prob:
        print("    🤔 [Indecisão] Usuário desistiu da ação rápido.")
        time.sleep(random.uniform(1, 3))
        try:
            # Simula um clique fora ou tecla ESC para cancelar algo aberto
            ActionChains(driver).send_keys(Keys.ESCAPE).perform()
        except: pass
        return True
    return False

def simular_leitura_texto(driver, elemento):
    """HC-5: Pausa o fluxo baseado na densidade de texto do elemento."""
    try:
        texto = elemento.text.strip()
        if not texto: return
        
        # 1s para cada 70 caracteres, limitado a 15s
        segundos = min(len(texto) / 70, 15)
        if segundos < 2: return
        
        print(f"    📖 [Leitura] Focando em conteúdo por {segundos:.1f}s...")
        # Move o mouse sobre o texto para simular leitura focada
        micro_movimentos_sobre_elemento(driver, elemento, segundos)
    except: pass



def scroll_com_leitura_simulada(driver):
    print("\n  👁  [HC-2] Scroll com simulação de leitura...")
    contador_scrolls = 0

    try:
        for _ in range(random.randint(4, 7)):
            driver.execute_script(
                f"window.scrollBy(0, {random.randint(300, 600)});"
            )
            contador_scrolls += 1
            time.sleep(random.uniform(1.2, 2.5))

            if contador_scrolls % 3 == 0:
                reverso_px = random.randint(300, 500)
                print(f"    ↑ Scroll reverso de {reverso_px}px (releitura)...")
                driver.execute_script(f"window.scrollBy(0, -{reverso_px});")
                time.sleep(random.uniform(1.5, 3.0))

                try:
                    ver_mais_btns = driver.find_elements(
                        By.XPATH,
                        "//div[@role='button' and ("
                        "contains(text(),'Ver mais') or "
                        "contains(text(),'See more') or "
                        "contains(text(),'Ver más')"
                        ")]",
                    )
                    if ver_mais_btns:
                        alvo_ver = random.choice(ver_mais_btns[:3])
                        micro_move_before_click(driver, alvo_ver)
                        print("    📖 'Ver mais' clicado — simulando releitura.")
                        time.sleep(random.uniform(3.0, 6.0))
                except Exception:
                    pass

                driver.execute_script(
                    f"window.scrollBy(0, {random.randint(300, 500)});"
                )
                time.sleep(random.uniform(1.0, 2.0))

            try:
                posts_texto = driver.find_elements(
                    By.XPATH,
                    "//div[@data-ad-comet-preview='message' or "
                    "@data-ad-preview='message']",
                )
                posts_longos = [p for p in posts_texto if len(p.text.strip()) > 120]

                if posts_longos and random.random() < 0.65:
                    alvo = random.choice(posts_longos[:3])  # type: ignore
                    tempo_leitura = random.uniform(4.0, 9.0)
                    print(f"    📖 Lendo post longo por ~{tempo_leitura:.0f}s...")
                    micro_movimentos_sobre_elemento(driver, alvo, tempo_leitura)
            except Exception:
                pass

            time.sleep(random.uniform(0.8, 1.8))

        print("    ✓ Scroll com leitura concluído.")
    except Exception as e:
        print(f"    ✗ Falha no scroll com leitura: {e}")


# ═══════════════════════════════════════════════════════════════
#  DEEP COMMENTS (QUEBRA DE PADRÃO)
# ═══════════════════════════════════════════════════════════════

def task_deep_comments(driver, wait, resultados: dict, stop_check=None, **kwargs):
    """40% de prob por ciclo. Explora comentários de um post por ~20s."""
    if stop_check and stop_check(): return
    if random.random() > 0.40:
        return

    print("\n  ▶ [HC-DC] Deep Comments — explorando comentários...")
    try:
        driver.get("https://www.facebook.com/")
        time.sleep(random.uniform(4, 6))

        for _ in range(3):
            driver.execute_script(
                f"window.scrollBy(0, {random.randint(400, 700)});"
            )
            time.sleep(random.uniform(1.5, 2.5))

        contador_cmts = None
        for sel in [
            "//span[contains(text(),' comentário')]",
            "//span[contains(text(),' comment')]",
            "//span[contains(text(),' comentario')]",
            "//a[contains(@href, 'comment')]",
        ]:
            try:
                elementos = driver.find_elements(By.XPATH, sel)
                candidatos = [
                    e for e in elementos
                    if any(c.isdigit() for c in e.text)
                ]
                if candidatos:
                    contador_cmts = random.choice(candidatos[:3])  # type: ignore
                    break
            except Exception:
                continue

        if contador_cmts is None:
            print("    · Nenhum post com comentários encontrado. Pulando.")
            return

        print("    → Abrindo seção de comentários...")
        micro_move_before_click(driver, contador_cmts)
        time.sleep(random.uniform(3, 5))

        print("    👁  Lendo comentários por ~20s...")
        fim_cmt = time.time() + random.uniform(18, 23)
        while time.time() < fim_cmt:
            if stop_check and stop_check(): break
            driver.execute_script(
                f"window.scrollBy(0, {random.randint(100, 250)});"
            )
            time.sleep(random.uniform(1.8, 3.5))

        try:
            ActionChains(driver).send_keys(Keys.ESCAPE).perform()
            time.sleep(random.uniform(1.0, 2.0))
        except Exception:
            pass

        print("    ✓ Seção de comentários explorada e fechada.")
    except Exception as e:
        print(f"    ✗ Falha no Deep Comments: {e}")


# ═══════════════════════════════════════════════════════════════
#  UTILITÁRIO CTA (compartilhado)
# ═══════════════════════════════════════════════════════════════

def _tentar_cta_em_tela(driver, resultados: dict) -> bool:
    """
    Varre CTAs visíveis na viewport atual.
    Se encontrar: centraliza, lê 5s, clica, navega ~20s e volta.
    Retorna True se clicou com sucesso.
    """
    condicoes_cta = " or ".join(
        [f"normalize-space(text())='{t}'" for t in CTA_AD_TEXTOS]
    )
    xpath_cta = (
        f"//div[@role='button' and ({condicoes_cta})]"
        f" | //a[@role='button' and ({condicoes_cta})]"
        f" | //span[{condicoes_cta}]/ancestor::div[@role='button'][1]"
    )
    try:
        candidatos = driver.find_elements(By.XPATH, xpath_cta)
        visiveis = [
            c for c in candidatos
            if c.is_displayed() and c.size.get("height", 0) > 0
        ]
        if not visiveis:
            return False

        btn_cta = random.choice(visiveis[:3])  # type: ignore
        driver.execute_script(
            "arguments[0].scrollIntoView({behavior:'smooth',block:'center'});",
            btn_cta,
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
                driver.execute_script(
                    f"window.scrollBy(0, {random.randint(200, 420)});"
                )
                time.sleep(random.uniform(2.0, 4.0))
            driver.back()
            time.sleep(random.uniform(3, 5))
            resultados["ads_clicados_por_cta"] = (
                resultados.get("ads_clicados_por_cta", 0) + 1
            )
            print(
                f"    ✓ CTA clicado (total: {resultados['ads_clicados_por_cta']}). Voltou."
            )
            return True
    except Exception:
        pass
    return False


# ═══════════════════════════════════════════════════════════════
#  TAREFA A — SUPER-SCROLL DE FEED (v3.4 — FAST SCROLLING)
# ═══════════════════════════════════════════════════════════════

def task_curtir_feed(
    driver, wait, resultados: dict, nome_modo: str = "Padrão", stop_check=None, **kwargs
):
    """
    Tarefa A — Fast-Scroll de Feed (v3.4).
    Upgrade: Persona & Context Awareness
    """
    persona = kwargs.get("persona")
    t_min, t_max = FEED_TEMPO_POR_MODO.get(nome_modo, (4 * 60, 5 * 60))
    duracao_feed = random.uniform(t_min, t_max)
    if persona:
        duracao_feed = persona.get_delay(duracao_feed)

    print(f"\n  ▶ [A] Scroll Feed ({nome_modo}) — {duracao_feed / 60:.1f} min...")

    inicio_feed     = time.time()
    scroll_contador = 0
    limite_reverso  = random.randint(POSTS_ANTES_REVERSO_MIN, POSTS_ANTES_REVERSO_MAX)
    distancia_total = 0
    ads_varredura   = 0

    try:
        driver.get("https://www.facebook.com/")
        time.sleep(random.uniform(4, 7))

        while time.time() - inicio_feed < duracao_feed:
            # ── SCROLL AVANÇADO (HC-2) ──────────────────────────────────
            pixels = random.randint(800, 1600)
            scroll_humano_avancado(driver, pixels)
            distancia_total += pixels
            
            # Chance de ruído humano aleatório (HC-8)
            if random.random() < 0.25:
                ruido_humano(driver, "baixa")

            scroll_contador += 1

            # ── AÇÃO NO POST VISÍVEL ────────────────────────────────────
            context_bonus = 0.0
            if persona:
                try:
                    # Tenta ler o texto do post mais próximo no topo
                    posts_visiveis = driver.find_elements(By.XPATH, "//div[@data-ad-comet-preview='message' or @data-ad-preview='message']")
                    if posts_visiveis:
                        texto_post = posts_visiveis[0].text.lower()
                        if any(interesse.lower() in texto_post for interesse in persona.interests):
                            context_bonus = 0.20 # 20% de bônus de interesse
                            print(f"    ⭐ [Context] Conteúdo de interesse detectado ({persona.interests[0]}...)!")
                except: pass

            dado = random.random()
            prob_curtir = PROB_CURTIR_FAST + context_bonus

            # Inconsistência na decisão (Ajuste 2.1)
            if persona and persona.should_contradict():
                prob_curtir = random.uniform(0.02, 0.25)
                print(f"    ➰ [Contradict] Agindo de forma inconsistente ({prob_curtir:.1%}).")

            if dado < prob_curtir:
                # 10% — CURTIR
                try:
                    like_btns = driver.find_elements(
                        By.XPATH,
                        "//div[@aria-label='Curtir' or @aria-label='Like' "
                        "or @aria-label='Me gusta']",
                    )
                    nao_curtidos = [
                        b for b in like_btns
                        if b.get_attribute("aria-pressed") in (None, "false", "")
                    ]
                    if nao_curtidos:
                        alvo = random.choice(nao_curtidos[:3])  # type: ignore
                        micro_move_before_click(driver, alvo)
                        resultados["curtidas_feed"] = resultados.get("curtidas_feed", 0) + 1
                        print(f"    ❤  Post curtido (total: {resultados['curtidas_feed']})")
                        time.sleep(random.uniform(0.8, 1.5))
                except Exception:
                    pass

            elif dado < PROB_CURTIR_FAST + PROB_LEITURA_LONGA:
                # 5% — PAUSA CURTA DE LEITURA (3–5s)
                pausa = random.uniform(LEITURA_LONGA_MIN, LEITURA_LONGA_MAX)
                print(f"    📖 Pausa rápida de leitura: {pausa:.0f}s...")
                try:
                    posts = driver.find_elements(
                        By.XPATH,
                        "//div[@data-ad-comet-preview='message' or "
                        "@data-ad-preview='message']",
                    )
                    longos = [p for p in posts if len(p.text.strip()) > 120]
                    if longos:
                        micro_movimentos_sobre_elemento(
                            driver, random.choice(longos[:3]), pausa  # type: ignore
                        )
                    else:
                        time.sleep(pausa)
                except Exception:
                    time.sleep(pausa)

            # ── RASTREAMENTO DE CTA NA VIEWPORT ────────────────────────
            clicou = _tentar_cta_em_tela(driver, resultados)
            if clicou:
                ads_varredura += 1
                resultados["anuncios_clicados_na_varredura"] = (
                    resultados.get("anuncios_clicados_na_varredura", 0) + 1
                )
                print(
                    f"    ✓ CTA clicado na varredura "
                    f"(total varredura: {ads_varredura}). Retomando..."
                )

            # ── SCROLL REVERSO: só após 10–15 descidas ─────────────────
            if scroll_contador >= limite_reverso:
                px_up = random.randint(150, REVERSO_MAX_PX)
                driver.execute_script(f"window.scrollBy(0, -{px_up});")
                distancia_total += px_up
                print(f"    ↑ Reverso curto: {px_up}px — retomando descida")
                time.sleep(random.uniform(0.8, 1.5))
                scroll_contador = 0
                limite_reverso = random.randint(
                    POSTS_ANTES_REVERSO_MIN, POSTS_ANTES_REVERSO_MAX
                )

        # ── REGISTROS FINAIS ────────────────────────────────────────────
        tempo_feed = time.time() - inicio_feed
        resultados["tempo_total_feed"] = (
            resultados.get("tempo_total_feed", 0) + tempo_feed
        )
        resultados["distancia_total_scrollada"] = (
            resultados.get("distancia_total_scrollada", 0) + distancia_total
        )
        print(
            f"    ✓ Fast-Scroll Feed encerrado: {tempo_feed / 60:.1f} min "
            f"| {distancia_total:,} px | CTAs varredura: {ads_varredura}"
        )

    except Exception as e:
        print(f"    ✗ Falha no Fast-Scroll Feed: {e}")


# ═══════════════════════════════════════════════════════════════
#  TAREFA B — REELS
# ═══════════════════════════════════════════════════════════════

def task_reels_watch(driver, wait, resultados: dict, stop_check=None, **kwargs):
    """Tarefa B — Reels com estratégia tripla de avanço e curtida 30%."""
    if stop_check and stop_check(): return
    print("\n  ▶ [B] Assistindo Reels...")
    try:
        driver.get("https://www.facebook.com/reel/")
        time.sleep(random.uniform(7, 10))

        # 15% de chance de Indecisão (HC-1)
        if gestao_indecisao(driver, 0.15):
            return

        qtd = random.randint(2, 5)
        for i in range(qtd):
            if stop_check and stop_check(): break
            # 25% de chance de pular o reel rápido (indecisão) nos primeiros (HC-1)
            if i < 2 and random.random() < 0.25:
                watch_time = random.uniform(1, 3)
                print(f"    ⏩ [Indecisão] Reel {i+1} pulado rápido ({watch_time:.1f}s)...")
            else:
                watch_time = random.uniform(11, 22)
                print(f"    ► Reel {i+1}/{qtd} — assistindo {watch_time:.1f}s...")

            try:
                like_reel = driver.find_elements(
                    By.XPATH,
                    "//div[@aria-label='Curtir' or @aria-label='Like' "
                    "or @aria-label='Me gusta']",
                )
                if like_reel and random.random() < 0.30:
                    micro_move_before_click(driver, like_reel[-1])
                    resultados["reels_curtidos"] = resultados.get("reels_curtidos", 0) + 1
                    print(f"    ✓ Reel {i+1} curtido.")
            except Exception:
                pass

            # Responsive sleep for reels
            sleep_end = time.time() + watch_time
            while time.time() < sleep_end:
                if stop_check and stop_check(): break
                time.sleep(0.5)
            
            resultados["reels_assistidos"] = resultados.get("reels_assistidos", 0) + 1

            avancou = False
            try:
                driver.find_element(By.TAG_NAME, "body").click()
                time.sleep(0.4)
                ac = ActionChains(driver)
                ac.move_by_offset(
                    random.randint(200, 400), random.randint(200, 400)
                ).click()
                time.sleep(0.3)
                ac.send_keys(Keys.ARROW_DOWN).perform()
                ac.move_by_offset(
                    -random.randint(200, 400), -random.randint(200, 400)
                ).perform()
                avancou = True
                time.sleep(random.uniform(1.5, 3.0))
            except Exception:
                pass

            if not avancou:
                try:
                    driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ARROW_DOWN)
                    avancou = True
                    time.sleep(random.uniform(1.5, 3.0))
                except Exception:
                    pass

            if not avancou:
                try:
                    driver.execute_script("window.scrollBy(0, 650);")
                    time.sleep(random.uniform(1.5, 3.0))
                except Exception:
                    pass

    except Exception as e:
        print(f"    ✗ Falha nos Reels: {e}")


# ═══════════════════════════════════════════════════════════════
#  TAREFA C — BUSCA RÁPIDA POR NICHO (v3.4)
# ═══════════════════════════════════════════════════════════════

def task_busca_aleatoria(driver, wait, resultados: dict, stop_check=None, **kwargs):
    """
    Tarefa C — Busca Rápida por Nicho (v3.4).

    Roda apenas 1 vez por sessão (flag 'busca_nicho_concluida').

    Varredura de resultados (30–45s):
      • Scroll rápido (350–600 px) sem paradas programadas.
      • Para SOMENTE se encontrar CTA (Saiba mais / Learn More):
          → lê 5s, clica, navega 20s, volta e retoma.
      • Reverso curto (100–200 px) a cada 8–12 scrolls.

    Registra: busca_nicho_concluida | tempo_gasto_na_busca |
              distancia_total_scrollada | anuncios_clicados_na_varredura
    """
    if resultados.get("busca_nicho_concluida"):
        return

    termo = random.choice(PALAVRAS_BUSCA)
    print(f"\n  ▶ [C] Busca Rápida por Nicho: '{termo}'...")
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
        time.sleep(random.uniform(0.4, 0.9))
        human_type(barra, termo)
        time.sleep(random.uniform(0.8, 1.5))
        barra.send_keys(Keys.RETURN)  # type: ignore

        print("    ✓ Pesquisa enviada. Carregando resultados...")
        time.sleep(random.uniform(4, 6))

        duracao_varredura = random.uniform(*BUSCA_SCROLL_DURACAO)
        print(f"    ⚡ Varrendo resultados em {duracao_varredura:.0f}s...")

        fim_varredura  = time.time() + duracao_varredura
        scroll_busca   = 0
        limite_rev_bus = random.randint(8, 12)
        dist_busca     = 0

        while time.time() < fim_varredura:
            if stop_check and stop_check(): break
            px = random.randint(350, 600)
            driver.execute_script(f"window.scrollBy(0, {px});")
            dist_busca   += px
            scroll_busca += 1
            time.sleep(random.uniform(0.5, 1.0))

            # Para SOMENTE se encontrar CTA
            clicou = _tentar_cta_em_tela(driver, resultados)
            if clicou:
                resultados["anuncios_clicados_na_varredura"] = (
                    resultados.get("anuncios_clicados_na_varredura", 0) + 1
                )
                print("    ✓ CTA encontrado na busca — retomando varredura...")

            if scroll_busca >= limite_rev_bus:
                px_up = random.randint(100, 200)
                driver.execute_script(f"window.scrollBy(0, -{px_up});")
                dist_busca   += px_up
                scroll_busca  = 0
                limite_rev_bus = random.randint(8, 12)
                time.sleep(random.uniform(0.6, 1.0))

        tempo_busca = time.time() - inicio_busca
        resultados["busca_nicho_concluida"]     = True
        resultados["tempo_gasto_na_busca"]      = tempo_busca
        resultados["buscas"]                    = resultados.get("buscas", 0) + 1
        resultados["distancia_total_scrollada"] = (
            resultados.get("distancia_total_scrollada", 0) + dist_busca
        )
        print(
            f"    ✓ Busca rápida por '{termo}' concluída "
            f"({tempo_busca:.0f}s | {dist_busca:,} px)."
        )

    except Exception as e:
        print(f"    ✗ Falha na busca rápida: {e}")


# ═══════════════════════════════════════════════════════════════
#  TAREFA D — WATCH LIVE
# ═══════════════════════════════════════════════════════════════

def task_watch_live(driver, wait, resultados: dict, nome_modo: str = "Padrão", stop_check=None, **kwargs):
    """Tarefa D — Assiste live. Tempo proporcional ao modo."""
    if stop_check and stop_check(): return
    print(f"\n  ▶ [D] Assistindo Live ({nome_modo})...")
    try:
        driver.get("https://www.facebook.com/watch/live/")
        time.sleep(random.uniform(6, 9))

        t_min, t_max = LIVE_TEMPO_POR_MODO.get(nome_modo, (3 * 60, 5 * 60))
        duracao_live = random.uniform(t_min, t_max)
        print(f"    ⏱  Assistindo por {duracao_live / 60:.1f} min...")

        player = None
        for sel in [
            "//video",
            "//div[@data-pagelet='WatchLiveFeed']",
            "//div[contains(@class,'video')]",
        ]:
            try:
                player = driver.find_element(By.XPATH, sel)
                break
            except Exception:
                continue

        inicio_live  = time.time()
        ultimo_move  = inicio_live

        while time.time() - inicio_live < duracao_live:
            if stop_check and stop_check(): break
            agora = time.time()
            if agora - ultimo_move >= 40:
                if player:
                    micro_movimentos_sobre_elemento(driver, player, 3.0)
                else:
                    try:
                        ActionChains(driver).move_by_offset(
                            random.randint(-10, 10), random.randint(-5, 5)
                        ).perform()
                    except Exception:
                        pass
                ultimo_move = time.time()
                print("    · Micro-movimento no player (anti-inatividade).")
            # Responsive sleep for live
            sleep_end_l = time.time() + random.uniform(4, 8)
            while time.time() < sleep_end_l:
                if stop_check and stop_check(): break
                time.sleep(0.5)
 
        tempo_assistido = time.time() - inicio_live
        resultados["tempo_live_total"] = (
            resultados.get("tempo_live_total", 0) + tempo_assistido
        )
        print(f"    ✓ Live assistida: {tempo_assistido / 60:.1f} min.")
    except Exception as e:
        print(f"    ✗ Falha na live: {e}")


# ═══════════════════════════════════════════════════════════════
#  TAREFA E — MARKETPLACE + MESSENGER
# ═══════════════════════════════════════════════════════════════

def task_marketplace_messenger(driver, wait, resultados: dict, stop_check=None, **kwargs):
    """Sub-tarefa: intenção de compra via Messenger (20% / 1x por sessão)."""
    if stop_check and stop_check(): return
    if resultados.get("interacao_comercial_messenger"):
        return
    if random.random() > 0.20:
        return

    print("\n    💬 [MKT-MSG] Tentando contato com vendedor via Messenger...")
    try:
        btn_msg = None
        seletores_btn = [
            "//div[@aria-label='Enviar mensagem ao vendedor']",
            "//a[@aria-label='Enviar mensagem ao vendedor']",
            "//div[contains(text(),'Enviar mensagem ao vendedor')]",
            "//span[contains(text(),'Enviar mensagem ao vendedor')]",
            "//div[@aria-label='Send message to seller']",
            "//a[@aria-label='Send message to seller']",
            "//div[contains(text(),'Send message to seller')]",
            "//span[contains(text(),'Send message to seller')]",
            "//div[@aria-label='Enviar mensaje al vendedor']",
            "//span[contains(text(),'Enviar mensaje al vendedor')]",
        ]

        for sel in seletores_btn:
            try:
                btn_msg = WebDriverWait(driver, 4).until(
                    EC.element_to_be_clickable((By.XPATH, sel))
                )
                break
            except Exception:
                continue

        if btn_msg is None:
            print("    · Botão de mensagem ao vendedor não encontrado. Pulando.")
            return

        micro_move_before_click(driver, btn_msg)
        print("    ✓ Botão 'Enviar mensagem ao vendedor' clicado.")
        time.sleep(random.uniform(3.0, 5.0))

        input_chat = None
        for sel_chat in [
            "//div[@role='textbox' and @contenteditable='true']",
            "//div[@aria-label='Mensagem' and @role='textbox']",
            "//div[@aria-label='Message' and @role='textbox']",
            "//div[@aria-label='Mensaje' and @role='textbox']",
        ]:
            try:
                input_chat = WebDriverWait(driver, 6).until(
                    EC.element_to_be_clickable((By.XPATH, sel_chat))
                )
                break
            except Exception:
                continue

        if input_chat is None:
            print("    · Caixa de chat não encontrada. Pulando envio.")
            return

        idioma_pagina = driver.execute_script("return document.documentElement.lang;")
        if idioma_pagina and "es" in idioma_pagina.lower():
            frase = "Hola, ¿esto todavía está disponible?"
        elif idioma_pagina and "en" in idioma_pagina.lower():
            frase = "Hi, is this still available?"
        else:
            frase = "Olá, isso ainda está disponível?"

        micro_move_before_click(driver, input_chat)
        time.sleep(random.uniform(0.8, 1.5))
        human_type(input_chat, frase)
        time.sleep(random.uniform(1.0, 2.0))
        input_chat.send_keys(Keys.RETURN)  # type: ignore

        print(f'    ✓ Mensagem enviada: "{frase}"')
        print("    ⏳ Aguardando resposta do vendedor (simulação)...")
        time.sleep(random.uniform(10, 15))

        resultados["interacao_comercial_messenger"] = True
        print("    ✓ Interação comercial registrada. Chat será fechado.")

        try:
            ActionChains(driver).send_keys(Keys.ESCAPE).perform()
        except Exception:
            pass
        time.sleep(random.uniform(1.5, 2.5))

    except Exception as e:
        print(f"    ✗ Falha no Marketplace Messenger: {e}")


def task_marketplace_browse(
    driver, wait, resultados: dict, nome_modo: str = "Padrão", stop_check=None, **kwargs
):
    """Tarefa E — Navega no Marketplace. Integra Messenger com 20% de chance."""
    if stop_check and stop_check(): return
    categoria = random.choice(CATEGORIAS_MARKETPLACE)
    print(f"\n  ▶ [E] Marketplace — categoria: '{categoria}'...")
    try:
        driver.get(f"https://www.facebook.com/marketplace/category/{categoria}/")
        time.sleep(random.uniform(5, 8))

        itens = driver.find_elements(
            By.XPATH, "//a[contains(@href, '/marketplace/item/')]"
        )
        if not itens:
            print("    ✗ Nenhum item encontrado.")
            return

        item = random.choice(itens[:10])
        print("    → Abrindo item...")
        _clicar_robusto(driver, item)
        time.sleep(random.uniform(4, 7))

        t_min, t_max = MARKETPLACE_TEMPO_POR_MODO.get(nome_modo, (60, 180))
        duracao_mp = random.uniform(t_min, t_max)
        print(f"    ⏱  Navegando por {duracao_mp:.0f}s...")

        fim_mp = time.time() + duracao_mp
        while time.time() < fim_mp:
            if stop_check and stop_check(): break
            scroll_humano_avancado(driver, random.randint(400, 900))
            
            if random.random() < 0.20:
                ruido_humano(driver, "baixa")

            if random.random() < 0.25:
                try:
                    btn_next = driver.find_element(
                        By.XPATH,
                        "//div[@aria-label='Próxima foto' or "
                        "@aria-label='Next photo' or @aria-label='Next']",
                    )
                    micro_move_before_click(driver, btn_next)
                    time.sleep(random.uniform(1.0, 2.5))
                except Exception:
                    pass

        task_marketplace_messenger(driver, wait, resultados, stop_check=stop_check)

        resultados["itens_marketplace_vistos"] = (
            resultados.get("itens_marketplace_vistos", 0) + 1
        )
        print("    ✓ Item do Marketplace visualizado.")
    except Exception as e:
        print(f"    ✗ Falha no Marketplace: {e}")


# ═══════════════════════════════════════════════════════════════
#  TAREFA F — CONSUMIDOR VIP (CTA no Feed)
# ═══════════════════════════════════════════════════════════════

def task_interact_ad(driver, wait, resultados: dict, stop_check=None, **kwargs):
    """Tarefa F — Consumidor VIP. 30% prob por ciclo. Detecta por CTA."""
    if stop_check and stop_check(): return
    if random.random() > 0.30:
        return

    print("\n  ▶ [F] Procurando anúncio por CTA...")
    try:
        driver.get("https://www.facebook.com/")
        time.sleep(random.uniform(5, 7))

        condicoes_cta = " or ".join(
            [f"normalize-space(text())='{t}'" for t in CTA_AD_TEXTOS]
        )
        xpath_cta = (
            f"//div[@role='button' and ({condicoes_cta})]"
            f" | //a[@role='button' and ({condicoes_cta})]"
            f" | //span[{condicoes_cta}]/ancestor::div[@role='button'][1]"
        )

        btn_cta = None
        for _ in range(5):
            if stop_check and stop_check(): break
            driver.execute_script(
                f"window.scrollBy(0, {random.randint(400, 700)});"
            )
            time.sleep(random.uniform(1.5, 2.5))
            try:
                candidatos = driver.find_elements(By.XPATH, xpath_cta)
                visiveis = [
                    c for c in candidatos
                    if c.is_displayed() and c.size.get("height", 0) > 0
                ]
                if visiveis:
                    btn_cta = random.choice(visiveis[:3])  # type: ignore
                    break
            except Exception:
                continue

        if btn_cta is None:
            print("    · Nenhum botão CTA encontrado neste ciclo.")
            return

        driver.execute_script(
            "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});",
            btn_cta,
        )
        time.sleep(random.uniform(1.5, 2.5))

        print("    👁  Lendo anúncio por 5s antes de clicar...")
        try:
            ActionChains(driver).move_to_element(btn_cta).perform()
        except Exception:
            pass
        time.sleep(random.uniform(4.5, 5.5))

        url_antes = driver.current_url
        micro_move_before_click(driver, btn_cta)
        time.sleep(random.uniform(2, 4))

        if driver.current_url != url_antes:
            print("    ✓ Acessou site de destino. Navegando ~20s...")
            fim_ad = time.time() + random.uniform(18, 24)
            while time.time() < fim_ad:
                if stop_check and stop_check(): break
                driver.execute_script(
                    f"window.scrollBy(0, {random.randint(200, 420)});"
                )
                time.sleep(random.uniform(2.0, 4.0))
            driver.back()
            time.sleep(random.uniform(3, 5))
            resultados["ads_clicados_por_cta"] = (
                resultados.get("ads_clicados_por_cta", 0) + 1
            )
            print(
                f"    ✓ CTA clicado (total: {resultados['ads_clicados_por_cta']}). Voltou."
            )
        else:
            print("    · Clique no CTA não resultou em navegação externa.")

    except Exception as e:
        print(f"    ✗ Falha na interação com CTA: {e}")


# ═══════════════════════════════════════════════════════════════
#  TAREFA G — POSTAGEM DE STATUS
# ═══════════════════════════════════════════════════════════════

def task_postagem_status(driver, wait, resultados: dict, stop_check=None, **kwargs):
    """Tarefa G — Publicação de status (uma única vez por sessão)."""
    if stop_check and stop_check(): return
    print("\n  ▶ [G] Publicando status de texto...")
    try:
        driver.get("https://www.facebook.com/")
        time.sleep(random.uniform(5, 7))

        texto = random.choice(FRASES_STATUS)
        post_box = None
        for sel in [
            "//span[contains(text(), 'pensando')]",
            "//span[contains(text(), 'thinking')]",
            "//span[contains(text(), 'Mande um alô')]",
            "//span[contains(text(), 'Escribe algo')]",
            "//div[@aria-label='Criar publicação']",
            "//div[@aria-label='Create a post']",
            "//div[@data-pagelet='FeedComposer']",
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

        txt_area = wait.until(
            EC.presence_of_element_located((By.XPATH, "//div[@role='textbox']"))
        )
        human_type(txt_area, texto)
        time.sleep(random.uniform(2.0, 3.5))

        btn_pub = None
        for sel in [
            "//div[@aria-label='Postar']",
            "//button[@aria-label='Postar']",
            "//div[@aria-label='Publicar']",
            "//button[@aria-label='Publicar']",
            "//div[@aria-label='Post']",
            "//button[@aria-label='Post']",
            "//div[@role='button']//span[text()='Postar' or text()='Publicar' or text()='Post']",
        ]:
            try:
                btn_pub = driver.find_element(By.XPATH, sel)
                if btn_pub.is_displayed():
                    break
            except Exception:
                continue

        if btn_pub:
            micro_move_before_click(driver, btn_pub)
            resultados["postagem"] = True
            print(f'    ✓ Status publicado: "{texto}"')
        else:
            print("    ✗ Botão 'Postar' não encontrado.")

        time.sleep(random.uniform(4, 7))
    except Exception as e:
        print(f"    ✗ Falha na postagem: {e}")


# ═══════════════════════════════════════════════════════════════
#  TAREFA I — REAÇÕES VARIADAS (HUMANIZADAS)
# ═══════════════════════════════════════════════════════════════

def task_reagir_posts(driver, wait, resultados: dict, stop_check=None, **kwargs):
    """Tarefa I — Reage a posts no feed com distribuição natural (35% prob)."""
    if stop_check and stop_check(): return
    if random.random() > 0.35:
        return

    print("\n  ▶ [I] Reagindo a posts no feed...")
    try:
        driver.get("https://www.facebook.com/")
        time.sleep(random.uniform(4, 6))

        for _ in range(random.randint(1, 3)):
            if stop_check and stop_check(): break
            driver.execute_script(f"window.scrollBy(0, {random.randint(400, 800)});")
            time.sleep(random.uniform(2, 4))

            try:
                # Encontra botões de Curtir visíveis
                like_btns = driver.find_elements(
                    By.XPATH,
                    "//div[@aria-label='Curtir' or @aria-label='Like' or @aria-label='Me gusta']"
                )
                visiveis = [b for b in like_btns if b.is_displayed()]
                if not visiveis:
                    continue

                alvo = random.choice(visiveis[:2])
                reacao = random.choice(REACOES_POPULACAO)
                
                print(f"    → Escolhendo reação: {reacao}...")
                
                if reacao == "Like":
                    micro_move_before_click(driver, alvo)
                else:
                    # Hover para abrir menu de reações
                    ActionChains(driver).move_to_element(alvo).perform()
                    time.sleep(random.uniform(1.5, 2.5))
                    
                    # Procura o botão da reação específica
                    nomes_reacao = REACAO_ARIA.get(reacao, [reacao])
                    xpath_reacao = " or ".join([f"@aria-label='{n}'" for n in nomes_reacao])
                    
                    try:
                        btn_reacao = wait.until(EC.element_to_be_clickable((By.XPATH, f"//div[{xpath_reacao}]")))
                        micro_move_before_click(driver, btn_reacao)
                    except Exception:
                        # Fallback para Like se não achar o menu
                        micro_move_before_click(driver, alvo)

                resultados["reacoes_dadas"] = resultados.get("reacoes_dadas", 0) + 1
                time.sleep(random.uniform(2, 4))
            except Exception:
                continue

    except Exception as e:
        print(f"    ✗ Falha ao reagir a posts: {e}")


# ═══════════════════════════════════════════════════════════════
#  TAREFA J — COMENTÁRIOS EM POSTS
# ═══════════════════════════════════════════════════════════════

def task_comentar_posts(driver, wait, resultados: dict, stop_check=None, **kwargs):
    """Tarefa J — Comenta em posts do feed (25% prob)."""
    if stop_check and stop_check(): return
    if random.random() > 0.25:
        return

    print("\n  ▶ [J] Comentando em posts no feed...")
    try:
        driver.get("https://www.facebook.com/")
        time.sleep(random.uniform(4, 6))

        scroll_humano_avancado(driver, random.randint(800, 1500))
        
        # Chance de indecisão (HC-1)
        if gestao_indecisao(driver, 0.15): return

        # Busca posts com texto longo o suficiente para comentar
        posts = driver.find_elements(By.XPATH, "//div[@data-ad-comet-preview='message' or @data-ad-preview='message']")
        candidatos = [p for p in posts if len(p.text.strip()) > 40]

        if not candidatos:
            print("    · Nenhum post adequado para comentar encontrado.")
            return

        alvo_post = random.choice(candidatos[:2])
        driver.execute_script("arguments[0].scrollIntoView({behavior:'smooth',block:'center'});", alvo_post)
        
        # Simula leitura do post antes de comentar (HC-5)
        simular_leitura_texto(driver, alvo_post)
        time.sleep(random.uniform(2, 4)) 

        try:
            # Tenta achar o campo de comentário
            cmt_box = alvo_post.find_element(By.XPATH, ".//div[@role='textbox' and contains(@aria-label, 'coment')]")
        except Exception:
            # Se não achar direto no post, tenta clicar no botão de comentar primeiro
            try:
                btn_cmt = alvo_post.find_element(By.XPATH, ".//div[@aria-label='Escrever um comentário' or @aria-label='Write a comment']")
                micro_move_before_click(driver, btn_cmt)
                time.sleep(random.uniform(1, 2))
                cmt_box = driver.find_element(By.XPATH, "//div[@role='textbox' and contains(@aria-label, 'coment')]")
            except Exception:
                print("    ✗ Campo de comentário não encontrado.")
                return

        comentario = random.choice(COMENTARIOS_POSTS)
        micro_move_before_click(driver, cmt_box)
        time.sleep(random.uniform(1, 2))
        
        # 20% de chance de errar e apagar (humanizado)
        if random.random() < 0.20:
            human_type(cmt_box, "Muito bo")
            time.sleep(random.uniform(0.5, 1.0))
            for _ in range(8):
                cmt_box.send_keys(Keys.BACKSPACE)
                time.sleep(0.1)
                
        human_type(cmt_box, comentario)
        time.sleep(random.uniform(1.5, 3))
        cmt_box.send_keys(Keys.RETURN)
        
        resultados["comentarios_feitos"] = resultados.get("comentarios_feitos", 0) + 1
        print(f"    ✓ Comentário enviado: {comentario}")
        time.sleep(random.uniform(2, 4))

    except Exception as e:
        print(f"    ✗ Falha ao comentar posts: {e}")


# ═══════════════════════════════════════════════════════════════
#  TAREFA K — ENTRAR E EXPLORAR GRUPOS
# ═══════════════════════════════════════════════════════════════

def task_entrar_grupo(driver, wait, resultados: dict, nome_modo: str = "Padrão", stop_check=None, **kwargs):
    """Tarefa K — Busca nicho em grupos e explora (20% prob, 1x por sessão)."""
    if stop_check and stop_check(): return
    if resultados.get("grupos_visitados", 0) > 0:
        return
    if random.random() > 0.20:
        return

    nicho = random.choice(GRUPOS_NICHO)
    print(f"\n  ▶ [K] Explorando grupos de '{nicho}'...")
    try:
        driver.get(f"https://www.facebook.com/search/groups/?q={nicho}")
        time.sleep(random.uniform(5, 8))

        # Pega o primeiro grupo da lista
        grupos = driver.find_elements(By.XPATH, "//a[contains(@href, '/groups/')]")
        if not grupos:
            print("    ✗ Nenhum grupo encontrado.")
            return

        alvo_grupo = grupos[0]
        micro_move_before_click(driver, alvo_grupo)
        time.sleep(random.uniform(5, 8))

        t_min, t_max = GRUPOS_TEMPO_POR_MODO.get(nome_modo, (60, 120))
        duracao = random.uniform(t_min, t_max)
        print(f"    ⏱  Navegando no grupo por {duracao/60:.1f} min...")

        fim = time.time() + duracao
        while time.time() < fim:
            if stop_check and stop_check(): break
            driver.execute_script(f"window.scrollBy(0, {random.randint(300, 700)});")
            time.sleep(random.uniform(3, 6))
            
            # Chance de 30% de pedir para entrar se não for membro
            if random.random() < 0.30:
                try:
                    btn_join = driver.find_element(By.XPATH, "//div[@aria-label='Participar do grupo' or @aria-label='Join group']")
                    if btn_join:
                        micro_move_before_click(driver, btn_join)
                        print("    ✓ Pedido para participar do grupo enviado.")
                        time.sleep(2)
                except Exception:
                    pass

        resultados["grupos_visitados"] = resultados.get("grupos_visitados", 0) + 1
        print("    ✓ Exploração de grupo concluída.")

    except Exception as e:
        print(f"    ✗ Falha ao explorar grupo: {e}")


# ═══════════════════════════════════════════════════════════════
#  TAREFA L — ADICIONAR AMIGOS (SUGESTÕES)
# ═══════════════════════════════════════════════════════════════

def task_adicionar_amigos(driver, wait, resultados: dict, stop_check=None, **kwargs):
    """Tarefa L — Vê sugestões de amizade e adiciona 1-2 (15% prob, 1x)."""
    if stop_check and stop_check(): return
    if resultados.get("amigos_adicionados", 0) > 0:
        return
    if random.random() > 0.15:
        return

    print("\n  ▶ [L] Vendo sugestões de amizade...")
    try:
        driver.get("https://www.facebook.com/friends/suggestions")
        time.sleep(random.uniform(5, 8))

        # Encontra perfis sugeridos
        sugestoes = driver.find_elements(By.XPATH, "//div[@aria-label='Adicionar amigo' or @aria-label='Add Friend']/ancestor::div[4]")
        if not sugestoes:
            print("    · Nenhuma sugestão encontrada.")
            return

        qtd = random.randint(1, 2)
        print(f"    → Analisando {len(sugestoes[:5])} sugestões...")
        
        for i in range(min(qtd, len(sugestoes))):
            try:
                perfil = sugestoes[i]
                driver.execute_script("arguments[0].scrollIntoView({behavior:'smooth',block:'center'});", perfil)
                if stop_check and stop_check(): break
                time.sleep(random.uniform(2, 4))
                
                # Clica no botão "Adicionar amigo"
                btn_add = perfil.find_element(By.XPATH, ".//div[@aria-label='Adicionar amigo' or @aria-label='Add Friend']")
                micro_move_before_click(driver, btn_add)
                resultados["amigos_adicionados"] = resultados.get("amigos_adicionados", 0) + 1
                print(f"    ✓ Solicitação enviada ({i+1}).")
                time.sleep(random.uniform(3, 6))
            except Exception:
                continue

    except Exception as e:
        print(f"    ✗ Falha ao adicionar amigos: {e}")


# ═══════════════════════════════════════════════════════════════
#  TAREFA H — FACEBOOK GAMING
# ═══════════════════════════════════════════════════════════════

def task_facebook_gaming(driver, wait, resultados: dict, nome_modo: str = "Padrão", stop_check=None, **kwargs):
    """Tarefa H — Retenção Gamer. Tempo proporcional ao modo."""
    if stop_check and stop_check(): return
    print(f"\n  ▶ [H] Facebook Gaming ({nome_modo})...")
    try:
        driver.get("https://www.facebook.com/gaming")
        time.sleep(random.uniform(6, 9))

        live_card = None
        seletores_live = [
            "//a[.//span[contains(translate(text(),'live','LIVE'),'LIVE')]]",
            "//a[.//span[contains(text(),'AO VIVO')]]",
            "//a[.//span[contains(text(),'Ao vivo')]]",
            "//a[@aria-label and contains(@aria-label,'LIVE')]",
            "//a[@aria-label and contains(@aria-label,'AO VIVO')]",
            "//a[contains(@href,'/live/') and contains(@href,'gaming')]",
            "//a[contains(@href,'/videos/') and contains(@href,'gaming')]",
        ]
        for sel in seletores_live:
            try:
                candidatos = driver.find_elements(By.XPATH, sel)
                if candidatos:
                    live_card = random.choice(candidatos[:5])
                    break
            except Exception:
                continue

        if live_card is None:
            try:
                live_card = driver.find_element(
                    By.XPATH,
                    "//a[contains(@href,'/videos/') or contains(@href,'/live/')]",
                )
            except Exception:
                pass

        if live_card is None:
            print("    · Nenhuma live encontrada no Gaming. Pulando.")
            return

        print("    → Abrindo live do Gaming...")
        _clicar_robusto(driver, live_card)
        time.sleep(random.uniform(5, 8))

        player = None
        for sel_p in ["//video", "//div[contains(@class,'video')]",
                       "//div[@data-pagelet='VideoContainer']"]:
            try:
                player = driver.find_element(By.XPATH, sel_p)
                break
            except Exception:
                continue

        t_min, t_max = GAMING_TEMPO_POR_MODO.get(nome_modo, (2 * 60, 4 * 60))
        duracao_gaming = random.uniform(t_min, t_max)
        print(f"    ⏱  Assistindo Gaming por {duracao_gaming / 60:.1f} min...")

        inicio_g     = time.time()
        ultimo_move_g = inicio_g

        while time.time() - inicio_g < duracao_gaming:
            if stop_check and stop_check(): break
            agora = time.time()
            if agora - ultimo_move_g >= 40:
                if player:
                    micro_movimentos_sobre_elemento(driver, player, 3.0)
                else:
                    try:
                        ActionChains(driver).move_by_offset(
                            random.randint(-12, 12), random.randint(-6, 6)
                        ).perform()
                    except Exception:
                        pass
                ultimo_move_g = time.time()
                print("    · Micro-movimento no player Gaming (anti-inatividade).")
            # Responsive sleep for gaming
            sleep_end_g = time.time() + random.uniform(4, 8)
            while time.time() < sleep_end_g:
                if stop_check and stop_check(): break
                time.sleep(0.5)

        tempo_gaming = time.time() - inicio_g
        resultados["tempo_gaming_real"] = (
            resultados.get("tempo_gaming_real", 0) + tempo_gaming
        )
        print(f"    ✓ Gaming assistido: {tempo_gaming / 60:.1f} min.")

    except Exception as e:
        print(f"    ✗ Falha no Facebook Gaming: {e}")


# ═══════════════════════════════════════════════════════════════
#  HC-A — EXPLORAÇÃO ORGÂNICA E CURIOSIDADE
# ═══════════════════════════════════════════════════════════════

def task_explorar_organico(driver, wait, resultados: dict, stop_check=None, **kwargs):
    """HC-4: Navega por hashtags, aba explorar e sugestões."""
    if stop_check and stop_check(): return
    print("\n  ▶ [HC-A] Exploração Orgânica...")
    try:
        # 1. Tenta ir para a aba Explorar
        driver.get("https://www.facebook.com/explore/")
        time.sleep(random.uniform(5, 8))
        scroll_humano_avancado(driver, random.randint(1000, 2000))
        
        # 2. Busca uma hashtag aleatória de um post visível
        tags = driver.find_elements(By.XPATH, "//a[contains(@href, '/hashtag/')]")
        if tags and random.random() < 0.5:
            escolhida = random.choice(tags[:3])
            print(f"    #  Clicando na hashtag: {escolhida.text}")
            _clicar_robusto(driver, escolhida)
            time.sleep(random.uniform(4, 7))
            scroll_humano_avancado(driver, random.randint(800, 1500))

        # 3. Sugestões do Algoritmo (Pessoas que talvez conheça)
        if random.random() < 0.4:
            print("    👥 Espiando sugestões de amizade...")
            driver.get("https://www.facebook.com/friends/suggestions")
            time.sleep(random.uniform(5, 8))
            scroll_humano_avancado(driver, random.randint(500, 1200))
            # Entra em um perfil e sai rápido (indecisão)
            perfil_links = driver.find_elements(By.XPATH, "//a[contains(@href, '/user/') or contains(@href, 'profile.php')]")
            if perfil_links:
                alvo = random.choice(perfil_links[:3])
                _clicar_robusto(driver, alvo)
                time.sleep(random.uniform(2, 5))
                print("    🤔 [Indecisão] Perfil visto por 3s e abandonado.")
                driver.back()
                time.sleep(random.uniform(2, 4))
                
    except Exception as e:
        print(f"    ✗ Falha na exploração orgânica: {e}")

# ═══════════════════════════════════════════════════════════════
#  HC-B — TROCA DE CONTEXTO E RITUAIS
# ═══════════════════════════════════════════════════════════════

def task_troca_contexto(driver, wait, resultados: dict, stop_check=None, **kwargs):
    """HC-6: Alterna entre feed, perfil e notificações."""
    if stop_check and stop_check(): return
    print("\n  ▶ [HC-B] Troca de Contexto...")
    try:
        # Ritual: Feed -> Ver Próprio Perfil -> Voltar
        print("    👤 Visitando próprio perfil...")
        perfil_btn = driver.find_element(By.XPATH, "//a[contains(@href, '/me/') or contains(@href, 'profile.php')]")
        _clicar_robusto(driver, perfil_btn)
        time.sleep(random.uniform(4, 7))
        scroll_humano_avancado(driver, random.randint(400, 900))
        
        ruido_humano(driver, "baixa")
        
        # Volta para Home
        print("    🏠 Voltando para o Feed...")
        home_btn = driver.find_element(By.XPATH, "//a[@aria-label='Facebook' or @aria-label='Página inicial']")
        _clicar_robusto(driver, home_btn)
        time.sleep(random.uniform(3, 5))
        
        # Check de notificações (mesmo se vazio)
        if random.random() < 0.6:
            check_notificacoes(driver, wait)

    except Exception as e:
        print(f"    ✗ Falha na troca de contexto: {e}")

# ═══════════════════════════════════════════════════════════════
#  HC-C — AÇÕES INCOMPLETAS E GHOSTING
# ═══════════════════════════════════════════════════════════════

def task_acoes_incompletas(driver, wait, resultados: dict, stop_check=None, **kwargs):
    """HC-7: Simula interações que não são concluídas (Comentário fantasma, inbox peek)."""
    if stop_check and stop_check(): return
    print("\n  ▶ [HC-C] Ações Incompletas...")
    try:
        # 1. Inbox Peek (Messenger)
        if random.random() < 0.5:
            print("    💬 Espiando o Messenger Inbox...")
            msg_btn = driver.find_element(By.XPATH, "//div[contains(@aria-label, 'Messenger')] | //a[contains(@aria-label, 'Messenger')]")
            _clicar_robusto(driver, msg_btn)
            time.sleep(random.uniform(4, 8))
            # Apenas olha e clica fora (ou dá ESC)
            ActionChains(driver).send_keys(Keys.ESCAPE).perform()
            print("    ✓ Inbox visualizado e fechado (sem mensagens enviadas).")
            time.sleep(random.uniform(2, 4))

        # 2. Ghost Comment
        # Procura um campo de comentário visível
        caixas = driver.find_elements(By.XPATH, "//div[@role='textbox' and contains(@aria-label, 'escreva um comentário')]")
        if caixas:
            alvo = random.choice(caixas[:2])
            driver.execute_script("arguments[0].scrollIntoView({behavior:'smooth',block:'center'});", alvo)
            time.sleep(random.uniform(2, 4))
            
            # Digita ago e apaga
            msg = random.choice(["Top!", "Legal!", "Muito bom", "Show"])
            print(f"    ⌨️  Digitando comentário fantasma: '{msg}'")
            for char in msg:
                alvo.send_keys(char)
                time.sleep(random.uniform(0.1, 0.3))
            
            time.sleep(random.uniform(2, 4))
            print("    ⌨️  [Ghosting] Apagando comentário e desistindo...")
            for _ in range(len(msg)):
                alvo.send_keys(Keys.BACKSPACE)
                time.sleep(random.uniform(0.05, 0.15))
            
            ActionChains(driver).send_keys(Keys.ESCAPE).perform()
            time.sleep(random.uniform(1, 3))

        # 3. Cancel Share
        if random.random() < 0.4:
            print("    ↪️  [Ação Incompleta] Abrindo menu de compartilhamento...")
            try:
                share_btns = driver.find_elements(By.XPATH, "//div[@aria-label='Enviar esta publicação para amigos ou publique-a no seu mural.' or @aria-label='Share' or @aria-label='Compartilhar']")
                if share_btns:
                    alvo_s = random.choice(share_btns[:2])
                    micro_move_before_click(driver, alvo_s)
                    time.sleep(random.uniform(3, 5))
                    # Simula indecisão e cancela
                    print("    ↪️  [Indecisão] Desistiu de compartilhar. Fechando menu.")
                    ActionChains(driver).send_keys(Keys.ESCAPE).perform()
                    time.sleep(random.uniform(1.5, 3))
            except: pass

    except Exception as e:
        print(f"    ✗ Falha nas ações incompletas: {e}")


# ═══════════════════════════════════════════════════════════════
#  LOOP PRINCIPAL DE AQUECIMENTO POR TEMPO
# ═══════════════════════════════════════════════════════════════

def facebook_warmup_por_tempo(
    controller, duracao_original: int, nome_modo: str, stop_check: Callable[[], bool] = None, resultados: dict = None
):
    """
    Orquestra todas as tarefas em ciclos variados até o tempo esgotar.
    Upgrade: Human Behavior 2.0 (Persona & Phases)
    """
    # ── INICIALIZAR PERSONA ─────────────────
    pid = "unknown"
    try:
        pid = getattr(controller, "profile_id", str(controller))
    except: pass
    
    persona = SessionPersona(pid)
    log(f"\n🚀 [BOT] PERSONA CONSTRUÍDA PARA {pid}")
    log(f"🧠 Mood: {persona.mood:.2f} | Energy: {persona.energy:.2f} | Energy: {persona.energy:.2f}")
    log(f"🌪️ Misclick Rate: {persona.misclick_rate:.1%}")
    
    try:
        log("🔍 [PASSO 1] Capturando WebDriver...")
        try:
            driver = extrair_driver(controller)
            if not driver:
                raise Exception("WebDriver não capturado.")
        except Exception as e:
            return {"ok": False, "error": str(e)}

        wait = WebDriverWait(driver, 25)
        duracao_segundos = duracao_original
        inicio = time.time()

        if resultados is None:
            resultados = {
                "curtidas_feed": 0, "reacoes_dadas": 0, "comentarios_feitos": 0,
                "reels_assistidos": 0, "reels_curtidos": 0, "buscas": 0,
                "distancia_total_scrollada": 0, "ciclos": 0, "ok": True,
            }
        else:
            # Garante que as chaves essenciais existam
            defaults = {
                "curtidas_feed": 0, "reacoes_dadas": 0, "comentarios_feitos": 0,
                "reels_assistidos": 0, "reels_curtidos": 0, "buscas": 0,
                "ciclos": 0, "ok": True, "distancia_total_scrollada": 0
            }
            for k, v in defaults.items():
                if k not in resultados:
                    resultados[k] = v
        
        ctx = {"nome_modo": nome_modo, "persona": persona}
        tarefas_ciclicas = [
            task_curtir_feed, task_reels_watch, task_busca_aleatoria,
            task_watch_live, task_marketplace_browse, task_interact_ad,
            task_deep_comments, task_facebook_gaming, task_reagir_posts,
            task_comentar_posts, task_entrar_grupo, task_adicionar_amigos,
            task_explorar_organico, task_troca_contexto, task_acoes_incompletas,
        ]
        
        # Ordem específica para o Bootstrap se necessário
        bootstrap_queue = [task_curtir_feed, task_explorar_organico, task_reagir_posts]
        random.shuffle(bootstrap_queue)

        postagem_feita = False
        inicio = time.time()

        log(f"🕐 [LOG] Meta de Duração: {duracao_segundos // 60} minutos.")
        log("🌐 [PASSO 2] Carregando portal Facebook...")
        
        try:
            # 🔄 Estratégia de Reaproveitamento Inteligente (Ajuste 2.3)
            handles = driver.window_handles
            reused = False
            
            # 1. Busca por uma aba que já seja o Facebook Home
            for handle in handles:
                try:
                    driver.switch_to.window(handle)
                    curr_url = driver.current_url.lower()
                    if "facebook.com" in curr_url and not any(x in curr_url for x in ["business.", "adsmanager.", "ads.", "help."]):
                        log(f"✅ [Bot] Facebook já aberto na aba '{curr_url}'. Usando esta guia.")
                        reused = True
                        break
                except: continue
            
            # 2. Se não achou o Facebook, busca uma aba "limpa" do AdsPower para reaproveitar
            if not reused:
                for handle in handles:
                    try:
                        driver.switch_to.window(handle)
                        curr_url = driver.current_url.lower()
                        placeholders = ["start.adspower.net", "about:blank", "adspower.com/start", "chrome://newtab"]
                        if any(x in curr_url for x in placeholders):
                            log(f"🎯 [Bot] Reaproveitando guia inicial limpa ({curr_url})")
                            driver.get("https://www.facebook.com/")
                            reused = True
                            break
                    except: continue

            # 3. Se não achou nada (ex: só tem BM aberta), abre uma nova para não atrapalhar
            if not reused:
                log("🆕 [Bot] Nenhuma guia reutilizável encontrada. Abrindo nova guia para Facebook.")
                driver.execute_script("window.open('https://www.facebook.com/', '_blank');")
                time.sleep(1)
                driver.switch_to.window(driver.window_handles[-1])

            time.sleep(random.uniform(5, 8))
            log("✅ [PASSO 2] Facebook pronto. Iniciando rituais...")
            check_notificacoes(driver, wait)
        except Exception as e:
            log(f"⚠️ [AVISO] Falha no ritual de entrada (não fatal): {e}")

        # ── CICLO DE PERSISTÊNCIA ─────────────────────────────
        log("⚡ [PASSO 3] Entrando em loop de atividades persistente.")
        
        # ── ESTADO INICIAL DO RITMO ──
        current_rhythm = "NORMAL"
        next_rhythm_change = time.time() + random.uniform(60, 180)

        while True:
            elapsed = time.time() - inicio
            if elapsed >= duracao_segundos:
                log(f"⏲️ [FIM] Tempo de aquecimento atingido ({duracao_segundos}s).")
                break
                
            # Mudança dinâmica de Ritmo (Ajuste 2.1)
            if time.time() > next_rhythm_change:
                current_rhythm = random.choice(["NORMAL", "BURST", "OBSERVE"])
                next_rhythm_change = time.time() + random.uniform(60, 240)
                log(f"🎭 [Persona] Mudando ritmo de navegação para: {current_rhythm}")

            # Early Exit simulado
            if persona.early_exit_chance > 0 and random.random() < 0.005: 
                log("🚪 [Persona] Decidiu sair mais cedo hoje por tédio ou cansaço.")
                break
            
            if stop_check and stop_check():
                log("🛑 [STOP] Interrupção manual detectada.")
                break

            # Determina a Fase da Sessão
            progresso = elapsed / duracao_segundos
            if progresso < 0.2:
                fase = "BOOTSTRAP"
                pool = bootstrap_queue if random.random() < persona.bootstrap_intensity else tarefas_ciclicas
            elif progresso < 0.8:
                fase = "HUMAN"
                pool = tarefas_ciclicas
            else:
                fase = "COOLDOWN"
                pool = tarefas_ciclicas

            log(f"🔄 [FASE: {fase} | RITMO: {current_rhythm}] Ciclo {resultados['ciclos'] + 1}...")
            random.shuffle(pool)
            resultados["ciclos"] += 1

            for tarefa in pool:
                if stop_check and stop_check(): break
                if time.time() - inicio >= duracao_segundos: break
                
                t_name = tarefa.__name__.replace('task_', '').upper()
                
                # Inconsistência Proposital (Contradição)
                if persona.should_contradict() and random.random() < 0.3:
                    log(f"➰ [Contradição] Ignorando {t_name} de propósito para quebrar padrão.")
                    human_sleep(random.uniform(5, 15), driver)
                    continue

                # Efeito do Ritmo OBSERVE (Passivo)
                if current_rhythm == "OBSERVE" and random.random() < 0.6:
                    log(f"🔭 [Observe] Apenas observando o feed em vez de {t_name}...")
                    human_sleep(random.uniform(10, 25), driver)
                    continue

                log(f"🎬 [ATIVIDADE] Executando {t_name}...")
                try:
                    tarefa(driver, wait, resultados, stop_check=stop_check, **ctx)
                    log(f"✔️ [OK] {t_name} finalizada.")
                except Exception as e:
                    log(f"⚠️ [ERRO] {t_name}: {e}")
                
                # Delay variável entre tarefas (ajustado pelo Ritmo)
                delay_base = random.uniform(4, 10)
                if current_rhythm == "BURST": delay_base = random.uniform(1, 4)
                if current_rhythm == "OBSERVE": delay_base = random.uniform(15, 40)
                if fase == "COOLDOWN": delay_base *= 1.8

                delay_final = persona.get_delay(delay_base)
                human_sleep(delay_final, driver)

            # A postagem foi removida para evitar repetição de textos (comportamento de bot).

        log(f"🏁 [FINALIZADO] Automação concluída em {time.strftime('%H:%M:%S')}")
        return resultados

    except Exception as e:
        print(f"🔴 [ERRO CRÍTICO] Falha no coração do bot: {e}")
        import traceback
        traceback.print_exc()
        return {"ok": False, "error": str(e)}

    return resultados


# ═══════════════════════════════════════════════════════════════
#  MENU PRINCIPAL
# ═══════════════════════════════════════════════════════════════

def menu_modo_tempo() -> tuple[str, int]:
    print("\n  Selecione o modo de aquecimento:")
    print("  [1] Rápido   — 10 minutos")
    print("  [2] Padrão   — 30 minutos")
    print("  [3] Intenso  — 60 minutos")
    while True:
        escolha = input("\n  Modo: ").strip()
        if escolha in MODOS_TEMPO:
            nome, segundos = MODOS_TEMPO[escolha]
            print(f"\n  ✓ Modo '{nome}' selecionado ({segundos // 60} min por perfil).")
            return nome, segundos
        print("  ⚠ Opção inválida. Digite 1, 2 ou 3.")
    return "", 0


def main():
    print(BANNER)
    manager = AccountManager()

    if not manager.check_adspower():
        print("\n⚠ AdsPower não detectado. Abra o software primeiro!")
        sys.exit(1)

    while True:
        print("\n  [1] Aquecer perfil(s)")
        print("  [0] Sair")
        choice = input("\n  Opção: ").strip()

        if choice == "0":
            print("\n  Encerrando bot. Até logo! 👋\n")
            break

        if choice != "1":
            print("  ⚠ Opção inválida.")
            continue

        raw_ids = input(
            "\n  IDs do AdsPower (separe por vírgula para vários): "
        ).strip()
        if not raw_ids:
            print("  ⚠ Nenhum ID inserido.")
            continue

        ids = [i.strip() for i in raw_ids.split(",") if i.strip()]
        nome_modo, duracao = menu_modo_tempo()

        print(f"\n  ▶ Total de perfis na fila: {len(ids)}")
        print("  " + "=" * 54)

        for idx, pid in enumerate(ids, 1):
            print(f"\n  [{idx}/{len(ids)}] Iniciando perfil: {pid}")

            session = manager.open_account(pid)
            if not session:
                print(f"  ✗ Erro ao abrir perfil {pid}. Pulando...")
                continue

            print(f"  ✓ Perfil {pid} aberto com sucesso.")

            resultado = manager.run_task(
                pid,
                lambda ctrl, d=duracao, m=nome_modo: facebook_warmup_por_tempo(
                    ctrl, d, m
                ),
            )

            if isinstance(resultado, dict) and "details" in resultado:
                dados = resultado["details"]
                dados["ok"] = resultado.get("ok", True)
            elif isinstance(resultado, dict):
                dados = resultado
            else:
                dados = {"ok": False, "error": str(resultado)}

            live_s   = float(dados.get("tempo_live_total", 0))
            gaming_s = float(dados.get("tempo_gaming_real", 0))
            feed_s   = float(dados.get("tempo_total_feed", 0))
            busca_s  = float(dados.get("tempo_gasto_na_busca", 0))
            dist_px  = float(dados.get("distancia_total_scrollada", 0))

            print(
                f"\n  📊 Resumo"
                f" | Feed: {int(feed_s//60)}m{int(feed_s%60):02d}s"
                f" / {dados.get('curtidas_feed', 0)}❤ / {dados.get('reacoes_dadas', 0)}👍"
                f" / {dados.get('comentarios_feitos', 0)}💬"
                f" | Scroll: {dist_px:,}px"
                f" | Busca: {'✓' if dados.get('busca_nicho_concluida') else '✗'}"
                f" {int(busca_s//60)}m{int(busca_s%60):02d}s"
                f" | Reels: {dados.get('reels_assistidos', 0)}▶"
                f"/{dados.get('reels_curtidos', 0)}❤"
                f" | Live: {int(live_s//60)}m{int(live_s%60):02d}s"
                f" | Gaming: {int(gaming_s//60)}m{int(gaming_s%60):02d}s"
                f" | Ads CTA: {dados.get('ads_clicados_por_cta', 0)}"
                f" | Ads varredura: {dados.get('anuncios_clicados_na_varredura', 0)}"
                f" | Mktplace: {dados.get('itens_marketplace_vistos', 0)}"
                f" | Grupos: {dados.get('grupos_visitados', 0)}👥"
                f" | Amigos: {dados.get('amigos_adicionados', 0)}👤+"
                f" | Msg: {'✓' if dados.get('interacao_comercial_messenger') else '✗'}"
                f" | Post: {'✓' if dados.get('postagem') else '✗'}"
                f" | Ciclos: {dados.get('ciclos', 0)}"
            )

            salvar_relatorio(pid, dados, nome_modo)
            manager.close_account(pid)
            print(f"  ✓ Perfil {pid} finalizado e fechado.")

            if idx < len(ids):
                delay = random.randint(18, 35)
                print(f"\n  ⏳ Aguardando {delay}s antes do próximo perfil...")
                time.sleep(delay)

        print("\n  " + "=" * 54)
        log("  ✅ FILA DE AQUECIMENTO CONCLUÍDA!")
        print("  " + "=" * 54)


if __name__ == "__main__":
    main()