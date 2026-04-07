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
import traceback
from typing import List, Dict, Any, Optional

# Previne bugs de stdout em Windows congelado (EXE)
if sys.platform == "win32":
    if sys.stdout is None: sys.stdout = open(os.devnull, 'w', encoding='utf-8')
    if sys.stderr is None: sys.stderr = open(os.devnull, 'w', encoding='utf-8')
    if sys.stdin is None: sys.stdin = open(os.devnull, 'r', encoding='utf-8')

from core.account_manager import AccountManager
from main import facebook_warmup_por_tempo, MODOS_TEMPO, set_log_callback

# ═══════════════════════════════════════════════════════════════
#  HELPERS
# ═══════════════════════════════════════════════════════════════

def crash_report(error_msg):
    try:
        with open("CRASH_REPORT.txt", "a", encoding="utf-8") as f:
            f.write(f"\n[{datetime.datetime.now()}] CRASH:\n{error_msg}\n")
            f.write(traceback.format_exc())
            f.write("\n" + "="*50 + "\n")
    except: pass
    print(f"!!! CRASH !!!: {error_msg}")

# ═══════════════════════════════════════════════════════════════
#  SCHEDULER ENGINE
# ═══════════════════════════════════════════════════════════════

class SchedulerEngine:
    def __init__(self):
        self.config = {"active": False, "windows": {}, "intensity": "normal", "daily_limit": 15}
        self.active_flag = False
        self.force_immediate = False
        self.next_sessions = {} # profile_id -> datetime
        self.daily_counts = {}  # profile_id -> count
        self.last_reset = datetime.datetime.now().date()

    def update_config(self, new_config):
        was_active = self.active_flag
        self.config.update(new_config)
        self.active_flag = bool(self.config.get("active", False))
        if self.active_flag and not was_active:
            self.force_immediate = True
        print(f"    [Scheduler] Atualizado. Ativo: {self.active_flag}")

    def should_run(self, profile_id):
        if not self.active_flag: return False
        
        today = datetime.datetime.now().date()
        if today > self.last_reset:
            self.daily_counts = {}
            self.last_reset = today

        if self.daily_counts.get(profile_id, 0) >= int(self.config.get("daily_limit", 15)):
            return False

        if profile_id not in self.next_sessions:
            self.schedule_next(profile_id)
            return False

        if self.force_immediate:
            self.force_immediate = False
            return True

        return datetime.datetime.now() >= self.next_sessions[profile_id]

    def schedule_next(self, profile_id):
        now = datetime.datetime.now()
        active_windows = []
        raw_win = self.config.get("windows", {})
        if isinstance(raw_win, dict):
            for win in raw_win.values():
                if isinstance(win, dict) and win.get("enabled"):
                    try:
                        sh = int(str(win.get("start", "08")).split(":")[0])
                        eh = int(str(win.get("end", "18")).split(":")[0])
                        active_windows.append((sh, eh))
                    except: pass

        if not active_windows:
            self.next_sessions[profile_id] = now + datetime.timedelta(minutes=random.randint(60, 180))
            return

        intensidade = self.config.get("intensity", "normal")
        base = 45 if intensidade == "high" else 90 if intensidade == "normal" else 180
        target = now + datetime.timedelta(minutes=random.randint(int(base*0.5), int(base*1.5)))
        
        # Ajuste de janela
        th = target.hour
        in_win = any(s <= th < e for s, e in active_windows)
        if not in_win:
            # Pega próxima janela
            future_starts = [s for s, e in active_windows if s > th]
            if future_starts:
                target = target.replace(hour=min(future_starts), minute=random.randint(0, 59))
            else:
                target = target.replace(hour=min(s for s, e in active_windows), minute=random.randint(0, 59)) + datetime.timedelta(days=1)

        self.next_sessions[profile_id] = target
        print(f"    [Scheduler] {profile_id} agendado para {target.strftime('%H:%M')}")

    def mark_executed(self, profile_id):
        self.daily_counts[profile_id] = self.daily_counts.get(profile_id, 0) + 1
        self.schedule_next(profile_id)

# ═══════════════════════════════════════════════════════════════
#  PATHS & CONFIG
# ═══════════════════════════════════════════════════════════════

if getattr(sys, 'frozen', False):
    app_path = os.path.dirname(sys.executable)
else:
    app_path = os.path.dirname(os.path.abspath(__file__))

# Folder 'cliente' friendly paths
LOGS_PATH = os.path.join(app_path, "logs")
CONFIG_PATH = os.path.join(app_path, "config.json")
if not os.path.exists(CONFIG_PATH) and os.path.exists(os.path.join(app_path, "cliente", "config.json")):
    LOGS_PATH = os.path.join(app_path, "cliente", "logs")
    CONFIG_PATH = os.path.join(app_path, "cliente", "config.json")

DEFAULT_SERVER = "wss://certo134-production.up.railway.app/ws/agent"
MACHINE_ID = "default"

if os.path.exists(CONFIG_PATH):
    try:
        with open(CONFIG_PATH, 'r') as f:
            c = json.load(f)
            MACHINE_ID = c.get("machine_id", "default")
    except: pass

# ═══════════════════════════════════════════════════════════════
#  AGENT WORKER
# ═══════════════════════════════════════════════════════════════

class AgentWorker:
    def __init__(self, machine_id: str):
        self.machine_id = machine_id.strip()
        self.server_url = f"{DEFAULT_SERVER}/{self.machine_id}"
        self.manager = AccountManager()
        self.ws = None
        self.is_connected = False
        self.is_running = False
        self.scheduler = SchedulerEngine()
        self.target_profiles = []
        self.main_loop = None
        
        # Bridge automation logs to dashboard and file
        def bridge(msg):
            if self.main_loop:
                asyncio.run_coroutine_threadsafe(self.log(msg), self.main_loop)
            else:
                self.log_to_file(msg)
        set_log_callback(bridge)

    def log_to_file(self, msg):
        try:
            if not os.path.exists(LOGS_PATH): os.makedirs(LOGS_PATH)
            with open(os.path.join(LOGS_PATH, "manager.log"), "a", encoding="utf-8") as f:
                f.write(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [INFO] {msg}\n")
        except: pass

    async def log(self, message: str):
        print(f"    [Agent] {message}")
        self.log_to_file(message)
        if self.ws and getattr(self.ws, 'open', False):
            try:
                await self.ws.send(json.dumps({"type": "LOG", "machine_id": self.machine_id, "data": {"message": str(message)}}))
            except: pass

    async def update_status(self, running: bool, profile: Optional[str] = None):
        if self.ws and getattr(self.ws, 'open', False):
            try:
                await self.ws.send(json.dumps({"type": "STATUS_UPDATE", "is_running": running, "current_profile": profile}))
            except: pass

    async def execute_micro_session(self, pid: str, dur: int):
        if self.is_running: return
        self.is_running = True
        await self.update_status(True, pid)
        try:
            session = self.manager.open_account(pid)
            if session:
                try:
                    await self.log(f"🚀 [SCHEDULER] Sessão curta iniciada: {pid} ({dur}s)")
                    res = await asyncio.to_thread(self.manager.run_task, pid, lambda ctrl: facebook_warmup_por_tempo(ctrl, dur, "Rápido"))
                    self.scheduler.mark_executed(pid)
                    if self.ws: await self.ws.send(json.dumps({"type": "RESULT", "profile_id": pid, "data": res}))
                finally: self.manager.close_account(pid)
            else:
                await self.log(f"❌ Erro ao abrir perfil {pid}")
        except Exception as e:
            await self.log(f"❌ Erro na micro-sessão {pid}: {e}")
            crash_report(f"Micro-sessão {pid} falhou: {e}")
        finally:
            self.is_running = False
            await self.update_status(False)
    async def execute_manual_warmup(self, pids: List[str], mode: str):
        if self.is_running: 
            await self.log("⚠ Agente já está executando uma tarefa.")
            return
        
        self.is_running = True
        await self.update_status(True, pids[0] if pids else None)
        
        try:
            for idx, pid in enumerate(pids):
                if not self.is_running: 
                    await self.log("🛑 Operação interrompida pelo usuário.")
                    break
                
                await self.update_status(True, pid)
                session = self.manager.open_account(pid)
                if session:
                    try:
                        nome_modo, dur = MODOS_TEMPO.get(mode, ("Padrão", 1800))
                        await self.log(f"🚀 [AUTO] Perfil {idx+1}/{len(pids)}: {pid} ({nome_modo})")
                        
                        # Executa em thread para não travar o loop de eventos
                        res = await asyncio.to_thread(
                            self.manager.run_task, 
                            pid, 
                            lambda ctrl: facebook_warmup_por_tempo(
                                ctrl, dur, nome_modo, stop_check=lambda: not self.is_running
                            )
                        )
                        
                        if self.ws:
                            await self.ws.send(json.dumps({
                                "type": "RESULT", 
                                "profile_id": pid, 
                                "data": res
                            }))
                    except Exception as e:
                        await self.log(f"❌ Erro ao processar {pid}: {e}")
                    finally:
                        self.manager.close_account(pid)
                else:
                    await self.log(f"❌ Falha ao abrir AdsPower para o perfil {pid}")
                
                # Pequena pausa entre perfis
                if idx < len(pids) - 1 and self.is_running:
                    await self.log("⏳ Aguardando 15s para o próximo perfil...")
                    await asyncio.sleep(15)
                    
        except Exception as e:
            await self.log(f"❌ Erro crítico no worker: {e}")
            crash_report(f"Erro no execute_manual_warmup: {e}")
        finally:
            self.is_running = False
            await self.update_status(False)
            if self.ws:
                await self.ws.send(json.dumps({"type": "FINISHED"}))
            await self.log("✅ Fila manual concluída.")

    async def scheduler_loop(self):
        while True:
            try:
                if self.scheduler.active_flag:
                    # Heartbeat do scheduler
                    if self.ws and getattr(self.ws, 'open', False):
                        try:
                            nxt = {p: t.strftime("%H:%M") for p, t in self.scheduler.next_sessions.items()}
                            await self.ws.send(json.dumps({"type": "SCHEDULER_STATUS", "next_sessions": nxt, "active": True}))
                        except: pass
                    
                    if not self.is_running:
                        for pid in self.target_profiles:
                            if self.scheduler.should_run(pid):
                                await self.log(f"⏰ [SCHEDULER] Momento ideal para {pid}!")
                                asyncio.create_task(self.execute_micro_session(pid, random.randint(60, 240)))
                                break
            except Exception as e:
                crash_report(f"Erro no scheduler_loop: {e}")
            
            # Se tiver ativação pendente, checa mais rápido
            sleep_time = 5 if self.scheduler.force_immediate else 60
            await asyncio.sleep(sleep_time)

    async def connect(self):
        self.main_loop = asyncio.get_event_loop()
        while True:
            try:
                self.server_url = f"{DEFAULT_SERVER}/{self.machine_id.strip()}"
                uri = self.server_url
                self.log_to_file(f"Conectando a {uri}")
                async with websockets.connect(uri, ping_interval=20, ping_timeout=20) as websocket:
                    self.ws = websocket
                    self.is_connected = True
                    self.log_to_file("Conectado com sucesso.")
                    async for message in websocket:
                        try:
                            data = json.loads(message)
                            mtype = data.get("type")
                            if mtype == "START":
                                config = data.get("data", {})
                                pids = config.get("profile_ids", [])
                                mode = config.get("mode", "2")
                                await self.log(f"📥 Comando recebido: Iniciar {len(pids)} perfis no modo {mode}")
                                asyncio.create_task(self.execute_manual_warmup(pids, mode))
                            elif mtype == "SCHEDULER_UPDATE":
                                cfg = data.get("data", {})
                                old_active = self.scheduler.active_flag
                                self.target_profiles = cfg.get("profile_ids", self.target_profiles)
                                self.scheduler.update_config(cfg)
                                if self.scheduler.active_flag and not old_active:
                                    await self.log(f"⏰ [SCHEDULER] Agendamento iniciado para {len(self.target_profiles)} perfis.")
                                else:
                                    await self.log("⚙️ Dashboard sincronizado.")
                            elif mtype == "STOP":
                                self.is_running = False
                                await self.log("🛑 Comando de parada recebido. Encerrando fila...")
                        except Exception as e:
                            self.log_to_file(f"Erro ao processar mensagem: {e}")
            except Exception as e:
                self.is_connected = False
                self.ws = None
                self.log_to_file(f"Falha de conexão: {e}")
                await asyncio.sleep(10)

# ═══════════════════════════════════════════════════════════════
#  GUI & MAIN
# ═══════════════════════════════════════════════════════════════

class GUIApp:
    def __init__(self, root, worker):
        self.root = root
        self.worker = worker
        self.root.title("Vexel Contigência PRO")
        self.root.geometry("400x250")
        self.root.configure(bg="#0f172a")
        
        tk.Label(root, text="VEXEL CONTIGÊNCIA", fg="#38bdf8", bg="#0f172a", font=("Segoe UI", 16, "bold")).pack(pady=(30, 10))
        self.sf = tk.Frame(root, bg="#1e293b", padx=20, pady=10)
        self.sf.pack(pady=10)
        self.dot = tk.Label(self.sf, text="●", fg="#ef4444", bg="#1e293b", font=("Segoe UI", 14))
        self.dot.pack(side="left", padx=(0, 5))
        self.txt = tk.Label(self.sf, text="RECONECTANDO...", fg="#94a3b8", bg="#1e293b", font=("Segoe UI", 10, "bold"))
        self.txt.pack(side="left")
        
        self.kv = tk.StringVar(value=worker.machine_id)
        tk.Entry(root, textvariable=self.kv, font=("Consolas", 9), width=45, justify="center").pack(pady=5, ipady=3)
        tk.Button(root, text="SALVAR E CONECTAR", command=self.save, fg="white", bg="#0ea5e9", font=("Segoe UI", 9, "bold"), padx=20, pady=5, relief="flat", cursor="hand2").pack(pady=10)
        
        self.up()

    def save(self):
        k = self.kv.get().strip()
        if not k: return
        self.worker.machine_id = k
        try:
            with open(CONFIG_PATH, 'w') as f: json.dump({"machine_id": k}, f, indent=4)
        except: pass
        if self.worker.ws:
            asyncio.run_coroutine_threadsafe(self.worker.ws.close(), self.worker.main_loop)

    def up(self):
        if self.worker.is_connected:
            self.dot.config(fg="#10b981")
            self.txt.config(text="AGENTE ONLINE", fg="#10b981")
        else:
            self.dot.config(fg="#ef4444")
            self.txt.config(text="RECONECTANDO...", fg="#94a3b8")
        self.root.after(1000, self.up)

def start_loop(w):
    l = asyncio.new_event_loop()
    asyncio.set_event_loop(l)
    l.create_task(w.scheduler_loop())
    l.run_until_complete(w.connect())

if __name__ == "__main__":
    w = AgentWorker(MACHINE_ID)
    threading.Thread(target=start_loop, args=(w,), daemon=True).start()
    r = tk.Tk()
    GUIApp(r, w)
    r.mainloop()
