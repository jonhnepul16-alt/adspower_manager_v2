import tkinter as tk
from tkinter import ttk
import threading
import asyncio
import json
import websockets
import sys
import os
import time
import datetime
import random
from typing import List, Dict, Any, Optional

if sys.platform == "win32":
    if sys.stdout is None:
        sys.stdout = open(os.devnull, 'w', encoding='utf-8')
    if sys.stderr is None:
        sys.stderr = open(os.devnull, 'w', encoding='utf-8')
    if sys.stdin is None:
        sys.stdin = open(os.devnull, 'r', encoding='utf-8')
        
    try:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    except:
        pass

from core.account_manager import AccountManager
from main import facebook_warmup_por_tempo, MODOS_TEMPO, set_log_callback, ruido_humano

# ═══════════════════════════════════════════════════════════════
#  SCHEDULER ENGINE (v1.0)
# ═══════════════════════════════════════════════════════════════

class SchedulerEngine:
    def __init__(self):
        self.config = {
            "active": False,
            "windows": {},
            "intensity": "normal",
            "style": "normal",
            "daily_limit": 15
        }
        self.active_flag = False
        self.current_stype = "normal"
        self.next_sessions = {} # profile_id -> datetime
        self.session_types = {}  # profile_id -> str (lazy, curious, normal)
        self.daily_counts = {}  # profile_id -> count
        self.last_reset = datetime.datetime.now().date()

    def update_config(self, new_config):
        self.config.update(new_config)
        self.active_flag = bool(self.config.get("active", False))
        print(f"    [Scheduler] Configuração atualizada. Ativo: {self.active_flag}")

    def should_run(self, profile_id):
        if not self.active_flag: return False
        
        # Reset diário
        today = datetime.datetime.now().date()
        if today > self.last_reset:
            self.daily_counts = {}
            self.last_reset = today

        # Limite diário
        limit = int(self.config.get("daily_limit", 15))
        if self.daily_counts.get(profile_id, 0) >= limit:
            return False

        now = datetime.datetime.now()
        
        # Se não tem próxima sessão agendada, agenda uma
        if profile_id not in self.next_sessions:
            self.schedule_next(profile_id)
            return False

        if now >= self.next_sessions[profile_id]:
            return True
        
        return False

    def schedule_next(self, profile_id):
        now = datetime.datetime.now()
        windows = self.config.get("windows", {})
        
        # Define a intensidade do próximo micro-loop
        r = random.random()
        if r < 0.2: self.current_stype = "lazy"
        elif r < 0.5: self.current_stype = "curious"
        else: self.current_stype = "normal"

        # Encontrar janelas ativas
        active_windows = []
        raw_windows = self.config.get("windows")
        if isinstance(raw_windows, dict):
            for name, win in raw_windows.items():
                if isinstance(win, dict) and win.get("enabled"):
                    try:
                        start_h = int(str(win.get("start", "08")).split(":")[0])
                        end_h = int(str(win.get("end", "18")).split(":")[0])
                        active_windows.append((start_h, end_h))
                    except: pass

        if not active_windows:
            # Fallback se nada habilitado
            wait = random.randint(60, 180)
            self.next_sessions[profile_id] = now + datetime.timedelta(minutes=wait)
            return

        # Calcula o próximo slot baseado nas janelas
        intensidade_global = self.config.get("intensity", "normal")
        base_min = 45 if intensidade_global == "high" else 90 if intensidade_global == "normal" else 180
        
        wait_min = random.randint(int(base_min * 0.5), int(base_min * 1.5))
        target_time = now + datetime.timedelta(minutes=wait_min)
        
        # Verifica se caiu em janela ativa
        is_in_window = False
        target_h = target_time.hour
        for start, end in active_windows:
            if start <= target_h < end:
                is_in_window = True
                break
        
        if not is_in_window:
            # Encontra a próxima janela que começa após target_time
            next_start = 24
            for start, end in active_windows:
                if start > target_h and start < next_start:
                    next_start = start
            
            if next_start == 24: # Nenhuma hoje, pega a primeira de amanhã
                sorted_windows = sorted(active_windows, key=lambda x: x[0])
                next_start = sorted_windows[0][0]
                target_time = target_time.replace(hour=next_start, minute=random.randint(0, 59)) + datetime.timedelta(days=1)
            else:
                target_time = target_time.replace(hour=next_start, minute=random.randint(0, 59))

        self.next_sessions[profile_id] = target_time
        self.session_types[profile_id] = self.current_stype
        print(f"    [Scheduler] Agendado {profile_id} para {target_time.strftime('%d/%m %H:%M:%S')} (Estilo: {self.current_stype})")

    def mark_executed(self, profile_id):
        self.daily_counts[profile_id] = self.daily_counts.get(profile_id, 0) + 1
        self.schedule_next(profile_id)

# Configuration
if getattr(sys, 'frozen', False):
    application_path = os.path.dirname(sys.executable)
else:
    application_path = os.path.dirname(os.path.abspath(__file__))

CONFIG_PATH = os.path.join(application_path, "config.json")
PERFIS_PATH = os.path.join(application_path, "perfis_agendamento.txt")
DEFAULT_SERVER_URL = "wss://certo134-production.up.railway.app/ws/agent"
DEFAULT_DASHBOARD_URL = "https://stately-torrone-4253a1.netlify.app/"
MACHINE_ID = "default"

def load_config():
    """Load cloud URLs and machine ID from config.json if it exists."""
    config = {
        "server_url": DEFAULT_SERVER_URL, 
        "dashboard_url": DEFAULT_DASHBOARD_URL,
        "machine_id": "default"
    }
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r') as f:
                data = json.load(f)
                config.update(data)
        except: pass
    return config

config_data = load_config()
SERVER_URL = config_data.get("server_url", DEFAULT_SERVER_URL)
DASHBOARD_URL = config_data.get("dashboard_url", DEFAULT_DASHBOARD_URL)
MACHINE_ID = config_data.get("machine_id", "default")

import webbrowser

class GUIApp:
    def __init__(self, root, agent):
        self.root = root
        self.agent = agent
        self.root.title("Vexel Contigência PRO")
        self.root.geometry("400x250")
        self.root.configure(bg="#0f172a") # Slate-900
        self.root.resizable(False, False)

        # Style
        style = ttk.Style()
        style.theme_use('clam')

        # Header
        self.header = tk.Label(
            root, text="VEXEL CONTIGÊNCIA", 
            fg="#38bdf8", bg="#0f172a", 
            font=("Segoe UI", 16, "bold")
        )
        self.header.pack(pady=(30, 10))

        # Status Frame
        self.status_frame = tk.Frame(root, bg="#1e293b", padx=20, pady=10)
        self.status_frame.pack(pady=10)

        self.status_dot = tk.Label(
            self.status_frame, text="●", 
            fg="#ef4444", bg="#1e293b", 
            font=("Segoe UI", 14)
        )
        self.status_dot.pack(side="left", padx=(0, 5))

        self.status_text = tk.Label(
            self.status_frame, text="RECONECTANDO...", 
            fg="#94a3b8", bg="#1e293b", 
            font=("Segoe UI", 10, "bold")
        )
        self.status_text.pack(side="left")

        # Instruction
        self.instr = tk.Label(
            root, text="Cole sua API Key do AdsPower abaixo para conectar:", 
            fg="#94a3b8", bg="#0f172a", 
            font=("Segoe UI", 9)
        )
        self.instr.pack(pady=(15, 5))

        # API Key Input
        self.api_key_var = tk.StringVar(value=MACHINE_ID if MACHINE_ID != "default" else "")
        self.api_entry = ttk.Entry(
            root, textvariable=self.api_key_var, 
            font=("Consolas", 9), width=45, justify="center"
        )
        self.api_entry.pack(pady=5, ipady=3)

        # Connect Button
        self.btn = tk.Button(
            root, text="SALVAR E CONECTAR", 
            command=self.save_and_reconnect,
            fg="white", bg="#0ea5e9", 
            font=("Segoe UI", 9, "bold"),
            padx=20, pady=5,
            relief="flat", cursor="hand2"
        )
        self.btn.pack(pady=10)

        # Periodic check for status updates from agent
        self.update_ui()

    def save_and_reconnect(self):
        new_key = self.api_key_var.get().strip()
        if not new_key: return

        # Update config.json
        config_data["machine_id"] = new_key
        try:
            with open(CONFIG_PATH, 'w') as f:
                json.dump(config_data, f, indent=4)
        except: pass

        # Update running agent
        self.agent.machine_id = new_key
        self.agent.server_url = f"{SERVER_URL}/{new_key}"

        # Force websocket to disconnect so the loop reconnects with new URL
        if hasattr(self.agent, 'main_loop') and self.agent.ws:
            import asyncio
            try:
                asyncio.run_coroutine_threadsafe(self.agent.ws.close(), self.agent.main_loop)
            except Exception: pass

    def update_ui(self):
        if self.agent.is_connected:
            self.status_dot.config(fg="#10b981") # Emerald-500
            self.status_text.config(text="AGENTE ONLINE", fg="#10b981")
        else:
            self.status_dot.config(fg="#ef4444")
            self.status_text.config(text="RECONECTANDO...", fg="#94a3b8")
        
        self.root.after(1000, self.update_ui)

class AgentWorker:
    def __init__(self, machine_id: str, server_url: str):
        self.machine_id = machine_id
        self.server_url = f"{server_url}/{machine_id}"
        self.manager = AccountManager()
        self.ws = None
        self.is_connected = False
        self.is_running = False
        self.scheduler = SchedulerEngine()
        self.target_profiles = [] # Profiles eligible for scheduler
        self.main_loop = None

    async def log(self, message: str):
        try:
            print(message)
        except Exception:
            pass
            
        if self.ws and hasattr(self.ws, "send"):
            try:
                await self.ws.send(json.dumps({"type": "LOG", "message": message}))
            except: pass

    async def update_status(self, is_running: bool, current_profile: Optional[str] = None):
        self.is_running = is_running
        if self.ws and hasattr(self.ws, "send"):
            try:
                await self.ws.send(json.dumps({
                    "type": "STATUS_UPDATE",
                    "is_running": is_running,
                    "current_profile": current_profile
                }))
            except: pass

    async def execute_task(self, profile_ids: List[str], mode_key: str):
        if self.is_running: return
        self.is_running = True
        await self.update_status(True)

        if mode_key not in MODOS_TEMPO:
            for k, v in MODOS_TEMPO.items():
                if v[0] == mode_key:
                    mode_key = k
                    break

        nome_modo, duracao = MODOS_TEMPO.get(mode_key, ("Padrao", 1800))
        
        for idx, pid in enumerate(profile_ids, 1):
            if not self.is_running: break
            await self.update_status(True, pid)
            session = self.manager.open_account(pid)
            if not session: continue
            
            try:
                # Execute in background thread to prevent blocking WebSocket PINGs
                result = await asyncio.to_thread(
                    self.manager.run_task,
                    pid, 
                    lambda ctrl: facebook_warmup_por_tempo(ctrl, duracao, nome_modo)
                )
                await self.ws.send(json.dumps({"type": "RESULT", "profile_id": pid, "data": result}))
            except Exception as e:
                await self.log(f"Erro: {e}")
            finally:
                self.manager.close_account(pid)
            
            if idx < len(profile_ids): await asyncio.sleep(5)

        self.is_running = False
        await self.update_status(False)
        if self.ws and hasattr(self.ws, "send"):
            try:
                await self.ws.send(json.dumps({"type": "FINISHED"}))
            except: pass

    async def scheduler_loop(self):
        """Background loop that checks for scheduled sessions."""
        while True:
            if self.scheduler.active_flag:
                # Envia status do scheduler para o painel a cada loop
                if self.ws and hasattr(self.ws, "send"):
                    try:
                        next_times = {pid: dt.strftime("%H:%M") for pid, dt in self.scheduler.next_sessions.items()}
                        await self.ws.send(json.dumps({
                            "type": "SCHEDULER_STATUS",
                            "next_sessions": next_times,
                            "active": self.scheduler.active_flag
                        }))
                    except: pass

                if not self.is_running:
                    for pid in self.target_profiles:
                        if self.scheduler.should_run(pid):
                            await self.log(f"⏰ [Scheduler] Iniciando micro-sessão para {pid}...")
                            duracao = random.randint(60, 240)
                            asyncio.create_task(self.execute_micro_session(pid, duracao))
                            break
            await asyncio.sleep(60) # Checa a cada minuto

    async def execute_micro_session(self, profile_id: str, duracao: int):
        """Executes a single short session."""
        if self.is_running: return
        self.is_running = True
        await self.update_status(True, profile_id)

        session = self.manager.open_account(profile_id)
        if session:
            try:
                await self.log(f"🚀 Sessão curta iniciada ({duracao}s)")
                result = await asyncio.to_thread(
                    self.manager.run_task,
                    profile_id,
                    lambda ctrl: facebook_warmup_por_tempo(ctrl, duracao, "Rápido")
                )
                self.scheduler.mark_executed(profile_id)
                if self.ws:
                    await self.ws.send(json.dumps({"type": "RESULT", "profile_id": profile_id, "data": result}))
            except Exception as e:
                await self.log(f"Erro na micro-sessão: {e}")
            finally:
                self.manager.close_account(profile_id)
        
        self.is_running = False
        await self.update_status(False)

    async def connect(self):
        self.main_loop = asyncio.get_event_loop()
        
        # Load profiles from file if exists
        if os.path.exists(PERFIS_PATH):
            try:
                with open(PERFIS_PATH, 'r') as f:
                    pids = [line.strip() for line in f if line.strip()]
                    if pids:
                        self.target_profiles = pids
                        print(f"    [Agent] {len(pids)} perfis carregados do arquivo para agendamento.")
            except: pass
            
        def sync_log(msg):
            try:
                if not self.main_loop.is_closed():
                    asyncio.run_coroutine_threadsafe(self.log(msg), self.main_loop)
            except Exception:
                pass
                
        set_log_callback(sync_log)
        
        while True:
            try:
                async with websockets.connect(self.server_url) as websocket:
                    self.ws = websocket
                    self.is_connected = True
                    # Sync real current state with server (don't reset if task is running)
                    await self.update_status(self.is_running)
                    
                    async for message in websocket:
                        data = json.loads(message)
                        msg_type = data.get("type")
                        
                        if msg_type == "START":
                            self.target_profiles = data["data"].get("profile_ids", [])
                            asyncio.create_task(self.execute_task(
                                self.target_profiles,
                                data["data"].get("mode", "1")
                            ))
                        elif data.get("type") == "SCHEDULER_UPDATE":
                            self.scheduler.update_config(data.get("data", {}))
                            await self.log("⚙️ Dashboard sincronizado: Agendamento atualizado.")
                        elif data.get("type") == "STOP":
                            was_running = self.is_running
                            self.is_running = False
                            if was_running:
                                self.manager.close_all()
                    self.is_connected = False
            except Exception as e:
                print(f"Erro de conexão: {e}")
                self.ws = None
                self.is_connected = False
                await asyncio.sleep(5)

def run_async_loop(worker):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    # Start scheduler background task
    loop.create_task(worker.scheduler_loop())
    loop.run_until_complete(worker.connect())

if __name__ == "__main__":
    worker = AgentWorker(MACHINE_ID, SERVER_URL)
    # Start Agent in a separate thread
    threading.Thread(target=run_async_loop, args=(worker,), daemon=True).start()
    
    root = tk.Tk()
    app = GUIApp(root, worker)
    root.mainloop()
