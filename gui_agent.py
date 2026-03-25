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

# Adjust paths for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Reconfigure stdout for UTF-8 to handle special characters on Windows
if sys.platform == "win32":
    try:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    except:
        pass

from core.account_manager import AccountManager
from main import facebook_warmup_por_tempo, MODOS_TEMPO, set_log_callback

# Configuration
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
DEFAULT_SERVER_URL = "wss://certo134-production.up.railway.app/ws/agent"
DEFAULT_DASHBOARD_URL = "https://stately-torrone-4253a1.netlify.app/"
MACHINE_ID = "default"

def load_config():
    """Load cloud URLs from config.json if it exists."""
    config = {"server_url": DEFAULT_SERVER_URL, "dashboard_url": DEFAULT_DASHBOARD_URL}
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
            root, text="Servidor ligado. Acesse o site para começar.", 
            fg="#64748b", bg="#0f172a", 
            font=("Segoe UI", 9)
        )
        self.instr.pack(pady=(20, 10))

        # Open Dashboard Button
        self.btn = tk.Button(
            root, text="ABRIR PAINEL WEB", 
            command=self.open_dashboard,
            fg="white", bg="#38bdf8", 
            font=("Segoe UI", 10, "bold"),
            padx=20, pady=5,
            relief="flat", cursor="hand2"
        )
        self.btn.pack(pady=10)

        # Periodic check for status updates from agent
        self.update_ui()

    def open_dashboard(self):
        webbrowser.open(DASHBOARD_URL)

    def update_ui(self):
        if self.agent.ws and self.agent.ws.open:
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
        self.is_running = False

    async def log(self, message: str):
        print(message)
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
                    "data": {"is_running": is_running, "current_profile": current_profile}
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
                self.manager.run_task(pid, lambda ctrl: facebook_warmup_por_tempo(ctrl, duracao, nome_modo))
                await self.ws.send(json.dumps({"type": "RESULT", "profile_id": pid, "data": {"ok": True}}))
            except Exception as e:
                await self.log(f"Erro: {e}")
            finally:
                self.manager.close_account(pid)
            
            if idx < len(profile_ids): await asyncio.sleep(5)

        self.is_running = False
        await self.update_status(False)
        await self.ws.send(json.dumps({"type": "FINISHED"}))

    async def connect(self):
        set_log_callback(self.log)
        while True:
            try:
                async with websockets.connect(self.server_url) as websocket:
                    self.ws = websocket
                    async for message in websocket:
                        data = json.loads(message)
                        if data.get("type") == "START":
                            asyncio.create_task(self.execute_task(
                                data["data"].get("profile_ids", []),
                                data["data"].get("mode", "1")
                            ))
                        elif data.get("type") == "STOP":
                            self.is_running = False
            except:
                self.ws = None
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
