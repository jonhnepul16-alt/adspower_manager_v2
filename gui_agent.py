import tkinter as tk
from tkinter import ttk
import threading
import asyncio
import json
import websockets
import sys
import os
import time
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
from main import facebook_warmup_por_tempo, MODOS_TEMPO, set_log_callback

# Configuration
if getattr(sys, 'frozen', False):
    application_path = os.path.dirname(sys.executable)
else:
    application_path = os.path.dirname(os.path.abspath(__file__))

CONFIG_PATH = os.path.join(application_path, "config.json")
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

    async def log(self, message: str):
        try:
            print(message)
        except Exception:
            pass
            
        if self.ws:
            try:
                await self.ws.send(json.dumps({"type": "LOG", "message": message}))
            except: pass

    async def update_status(self, is_running: bool, current_profile: Optional[str] = None):
        self.is_running = is_running
        if self.ws:
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
        await self.ws.send(json.dumps({"type": "FINISHED"}))

    async def connect(self):
        self.main_loop = asyncio.get_event_loop()
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
                        if data.get("type") == "START":
                            asyncio.create_task(self.execute_task(
                                data["data"].get("profile_ids", []),
                                data["data"].get("mode", "1")
                            ))
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
    loop.run_until_complete(worker.connect())

if __name__ == "__main__":
    worker = AgentWorker(MACHINE_ID, SERVER_URL)
    # Start Agent in a separate thread
    threading.Thread(target=run_async_loop, args=(worker,), daemon=True).start()
    
    root = tk.Tk()
    app = GUIApp(root, worker)
    root.mainloop()
