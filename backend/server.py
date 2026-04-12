import sys
import os
import threading
import time
import json
import logging
import datetime
import random
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add parent directory to path to import main and core
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import facebook_warmup_por_tempo, MODOS_TEMPO
from core.account_manager import AccountManager
from core.plan_manager import PlanManager
from core.profile_db import ProfileDB
from core.cloud_bridge import CloudBridge, generate_machine_id
from core.path_utils import user_data_path

app = FastAPI(title="AdsPower Manager - Local API")

# Enable CORS for the React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
class AppState:
    def __init__(self):
        self.is_running = False
        self.stop_requested = False
        self.current_profile = None
        self.logs = []
        self.results = {}
        self.manager = AccountManager()
        self.plan_manager = PlanManager()
        self.profile_db = ProfileDB()
        self.current_task_start = 0
        self.current_task_duration = 0
        self.last_logged_account = None  # To avoid log spam
        self.last_logged_plan = None     # To avoid log spam
        
        # Scheduler Internal Engine
        self.scheduler_file = user_data_path(os.path.join("config", "scheduler.json"))
        self.scheduler_config = self._load_scheduler()
        self.scheduler_status = {"active_tasks": len([w for w in self.scheduler_config.get("windows", {}).values() if w.get("enabled")])}

    def _load_scheduler(self):
        try:
            with open(self.scheduler_file, 'r') as f:
                return json.load(f)
        except:
            return {}
            
    def save_scheduler(self):
        os.makedirs(os.path.dirname(self.scheduler_file), exist_ok=True)
        with open(self.scheduler_file, 'w') as f:
            json.dump(self.scheduler_config, f, indent=4)

state = AppState()

# Custom logger to capture prints
class LogBuffer:
    def __init__(self, terminal):
        self.terminal = terminal

    def write(self, message):
        # Ignore common HTTP access logs to clean up the UI terminal
        if "GET /api/warmup/status" in message or "HTTP/1.1\" 200 OK" in message:
            return

        try:
            self.terminal.write(message)
            self.terminal.flush()
        except UnicodeEncodeError:
            # Fallback if the raw console really can't handle the characters
            try:
                self.terminal.write(message.encode('ascii', 'replace').decode('ascii'))
                self.terminal.flush()
            except Exception:
                pass
        except Exception:
            # Ignore OS/pipe errors (like [Errno 22] Invalid argument in Windows Concurrently)
            pass
        
        msg = message.strip()
        if msg:
            state.logs.append(msg)
            if len(state.logs) > 1000:
                state.logs.pop(0)

    def flush(self):
        self.terminal.flush()

    def isatty(self):
        return hasattr(self.terminal, 'isatty') and self.terminal.isatty()

# Force UTF-8 for everything
if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Redirect stdout and stderr to our LogBuffer
buf = LogBuffer(sys.stdout)
sys.stdout = buf
sys.stderr = buf

class StartRequest(BaseModel):
    profile_ids: List[str]
    mode: str
    machine_id: Optional[str] = "default"
    duration: Optional[int] = None
    minimized: Optional[bool] = False

def run_automation_thread(profile_ids: List[str], mode: str, access_token: str, custom_duration: Optional[int] = None, minimized: bool = False):
    try:
        run_automation(profile_ids, mode, access_token, custom_duration, minimized)
    except Exception as e:
        state.logs.append(f"🔴 ERRO FATAL NA EXECUÇÃO: {str(e)}")
        import traceback
        state.logs.append(traceback.format_exc())
    finally:
        state.is_running = False
        state.current_profile = None
        state.logs.append("✅ Fila de automação finalizada com segurança.")

def run_automation(profile_ids: List[str], mode: str, access_token: str, custom_duration: Optional[int] = None, minimized: bool = False):
    state.is_running = True
    state.stop_requested = False
    
    # ── LOGGING BRIDGE ──
    from main import set_log_callback
    def log_bridge(msg):
        msg = str(msg).strip()
        if msg:
            state.logs.append(msg)
            if len(state.logs) > 500: # Limit history
                state.logs.pop(0)
    set_log_callback(log_bridge)

    state.logs.append("🚀 Iniciando automação...")
    
    # ── ROTATION SYSTEM & LIMITS CHECK
    available_profs = [p for p in state.profile_db.get_all() if p["id"] in profile_ids]
    # If no explicitly valid passed or empty list passed, we can auto-rotate from all active
    if not available_profs and not profile_ids:
        available_profs = state.profile_db.get_all()
        
    selected_ids, skipped_info = state.plan_manager.select_profiles(available_profs, access_token)
    
    if not selected_ids:
        state.logs.append("⚠ Nenhum perfil selecionado ou disponível para rodar.")
        return
        
    state.logs.append(f"🚀 Iniciando automação para {len(selected_ids)} perfis...")


    
    nome_modo, _ = MODOS_TEMPO.get(mode, ("Padrão", 1800))
    
    # Enforce Session Time strictly according to the user's plan
    user_limits = state.plan_manager.get_user_plan_config(access_token)
    min_sess, max_sess = user_limits["session_time"]
    
    if custom_duration:
        capped_min = min(custom_duration, max_sess)
        duracao = max(capped_min, min_sess) * 60
        
        if custom_duration != (duracao // 60):
            state.logs.append(f"⏱ Tempo de sessão ajustado automaticamente para corresponder aos limites do seu plano ({user_limits['plan']}).")
        else:
            state.logs.append(f"⏱ Tempo mapeado conforme seleção: {custom_duration} minutos (Plano {user_limits['plan']}).")
    else:
        import random
        # slight variance
        duracao = random.randint(min_sess * 60, max_sess * 60) 
        state.logs.append(f"⏱ Tempo de sessão automático definido: ~{duracao//60} minutos (Limites do Plano {user_limits['plan']}).")
    
    try:
        if not state.manager.check_adspower():
            state.logs.append("⚠ AdsPower não detectado. Abra o software primeiro!")
            return
        
        state.logs.append("ℹ Verificando comunicação com AdsPower API...")
        
        for idx, pid in enumerate(selected_ids):
            if state.stop_requested:
                state.logs.append("🛑 Parada solicitada pelo usuário.")
                break
                
            state.current_profile = pid
            state.current_task_start = time.time()
            state.current_task_duration = duracao
            state.logs.append(f"\n[{idx+1}/{len(selected_ids)}] Iniciando perfil: {pid}")
            
            state.results[pid] = {
                "curtidas_feed": 0, "reacoes_dadas": 0, "comentarios_feitos": 0,
                "reels_assistidos": 0, "reels_curtidos": 0, "ciclos": 0, "ok": True
            }
            
            try:
                session = state.manager.open_account(pid, minimized=minimized)
            except Exception as adspower_ex:
                if "open daily limit" in str(adspower_ex).lower():
                    state.logs.append("🚨 FAIL-SAFE ATIVADO: O AdsPower retornou 'Exceeding open daily limit'.")
                    state.logs.append("🛑 A automação será completamente interrompida para proteger sua conta e evitar bloqueios.")
                    state.stop_requested = True
                    break
                else:
                    state.logs.append(f"✗ Erro ao abrir perfil {pid}: {adspower_ex}")
                    state.plan_manager.log_profile_failed(pid)
                    continue

            if not session:
                state.logs.append(f"✗ Erro ao abrir perfil {pid}. Pulando...")
                state.plan_manager.log_profile_failed(pid)
                continue
                
            # Log as opened!
            state.plan_manager.log_profile_opened(pid)
                
            state.logs.append(f"✓ Perfil {pid} aberto. Conectando Selenium...")
            try:
                time.sleep(2)
                title = session.browser.get_title()
                state.logs.append(f"ℹ Conectado ao browser: '{title}'")
            except Exception as e:
                state.logs.append(f"⚠ Falha ao conectar: {e}. Tentando prosseguir...")

            try:
                profile_results = state.results[pid]
                state.logs.append("🔥 Iniciando rituais de aquecimento (Warming actions)...")
                
                resultado = state.manager.run_task(
                    pid,
                    lambda ctrl, d=duracao, m=nome_modo, r=profile_results: facebook_warmup_por_tempo(
                        ctrl, d, m, stop_check=lambda: state.stop_requested, resultados=r
                    )
                )
                
                if isinstance(resultado, dict):
                    state.results[pid].update(resultado)
                state.logs.append(f"✅ Tarefas concluídas para o perfil {pid}.")
                
            except Exception as e:
                state.logs.append(f"✗ Erro na execução do perfil {pid}: {str(e)}")
            
            state.manager.close_account(pid)
            state.logs.append(f"✓ Perfil {pid} finalizado e fechado.")
            
            # ── PROFILE HISTORY TRACKING
            date_str = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
            duracao_m = duracao // 60
            state.profile_db.add_history(pid, date_str, duracao_m)
            
            if idx < len(selected_ids) - 1 and not state.stop_requested:
                delay = 5 
                state.logs.append(f"⏳ Aguardando {delay}s para o próximo...")
                time.sleep(delay)
                
    except Exception as e:
        state.logs.append(f"❌ Erro crítico no loop principal: {str(e)}")
    finally:
        state.logs.append("✅ Fila de automação finalizada.")

def scheduler_generate_slots(config: dict) -> list:
    """
    Generates a list of execution slots distributed randomly within the time window.
    Each slot is a dict: { "time": "HH:MM", "profile_id": "xxx" }
    """
    profile_ids = config.get("profile_ids", [])
    start_str = config.get("start_time", "00:00")
    end_str = config.get("end_time", "06:00")
    repetitions = config.get("repetitions", 1)
    warmup_minutes = config.get("warmup_duration", 15)
    
    if not profile_ids:
        return []
    
    # Parse start/end into minutes from midnight
    sh, sm = map(int, start_str.split(":"))
    eh, em = map(int, end_str.split(":"))
    start_min = sh * 60 + sm
    end_min = eh * 60 + em
    
    # Handle overnight windows (e.g., 22:00 to 06:00)
    if end_min <= start_min:
        end_min += 24 * 60  # treat as next day
    
    total_window = end_min - start_min
    
    # Build all sessions: each profile × repetitions
    sessions = []
    for pid in profile_ids:
        for _ in range(repetitions):
            sessions.append(pid)
    
    random.shuffle(sessions)
    
    # Distribute sessions across the window with gaps
    # Each session needs warmup_minutes + a small buffer (3 min)
    session_block = warmup_minutes + 3
    total_needed = len(sessions) * session_block
    
    if total_needed > total_window:
        # Not enough time, compress the gaps
        session_block = max(warmup_minutes + 1, total_window // len(sessions))
    
    slots = []
    for i, pid in enumerate(sessions):
        # Calculate a base time for this slot
        base = start_min + int((total_window / len(sessions)) * i)
        # Add some randomness (±5 min) without going out of bounds
        jitter = random.randint(-3, 5)
        slot_min = max(start_min, min(end_min - warmup_minutes, base + jitter))
        
        # Convert back to HH:MM (handle >24h for overnight)
        actual_min = slot_min % (24 * 60)
        hh = actual_min // 60
        mm = actual_min % 60
        
        slots.append({
            "time": f"{hh:02d}:{mm:02d}",
            "profile_id": pid,
            "executed": False
        })
    
    # Sort by time for display
    slots.sort(key=lambda s: s["time"])
    return slots


def scheduler_daemon():
    """
    Slot-based scheduler daemon. Checks every 30 seconds if a scheduled slot
    matches the current time and executes it. Profiles open one at a time.
    """
    last_date = None  # Track current date to regenerate slots at midnight
    
    while True:
        try:
            cfg = state.scheduler_config
            if not cfg.get("active"):
                time.sleep(30)
                continue
            
            today = datetime.date.today().isoformat()
            
            # Regenerate slots once per day (or on first run)
            if last_date != today:
                slots = scheduler_generate_slots(cfg)
                cfg["_slots"] = slots
                cfg["_slots_date"] = today
                state.save_scheduler()
                last_date = today
                
                if slots:
                    times_preview = [f"{s['time']} ({s['profile_id'][:6]}...)" for s in slots[:8]]
                    state.logs.append(f"📅 Agendamento gerado para hoje: {len(slots)} sessões")
                    state.logs.append(f"   Próximos slots: {', '.join(times_preview)}")
            
            # Check if any slot matches NOW
            slots = cfg.get("_slots", [])
            now = datetime.datetime.now()
            current_hhmm = now.strftime("%H:%M")
            
            for slot in slots:
                if slot.get("executed"):
                    continue
                    
                if slot["time"] == current_hhmm and not state.is_running:
                    pid = slot["profile_id"]
                    warmup_min = cfg.get("warmup_duration", 15)
                    token = cfg.get("_access_token", "")
                    
                    slot["executed"] = True
                    state.save_scheduler()
                    
                    state.logs.append(f"⏰ Agendamento disparado! Perfil: {pid} | Duração: {warmup_min}min")
                    
                    # Run single profile warmup
                    thread = threading.Thread(
                        target=run_automation_thread, 
                        args=([pid], "1", token, warmup_min), 
                        daemon=True
                    )
                    thread.start()
                    
                    # Wait for this session to finish before checking next slot
                    thread.join()
                    
                    # Small cooldown between sessions
                    time.sleep(random.randint(30, 90))
                    break  # Re-check slots from the top
                    
        except Exception as e:
            state.logs.append(f"⚠ Erro no agendador: {str(e)}")
        
        time.sleep(30)

@app.get("/api/health")
def health_check():
    return {"status": "ok"}

def extract_token(request: Request) -> str:
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header.split(" ")[1]
    return ""

@app.get("/api/plan")
async def get_plan(request: Request):
    token = extract_token(request)
    return state.plan_manager.get_user_plan_config(token)

@app.get("/api/profiles")
async def get_profiles():
    # Return local profiles
    return {"profiles": state.profile_db.get_all()}

class ProfileCreateReq(BaseModel):
    id: str
    name: str = ""
    tag: str = ""

@app.post("/api/profiles")
async def create_profile(req: ProfileCreateReq, request: Request):
    token = extract_token(request)
    limits = state.plan_manager.get_user_plan_config(token)
    max_allowed = limits.get("max_profiles", 5)
    
    current_count = len(state.profile_db.get_all())
    if current_count >= max_allowed:
        raise HTTPException(status_code=403, detail=f"Plan limit reached: Maximum {max_allowed} profiles allowed on {limits['plan']} plan.")
        
    success = state.profile_db.add_profile(req.id, req.name, req.tag)
    if not success:
        raise HTTPException(status_code=400, detail="Profile ID already exists")
    
    return {"message": "Profile added successfully", "profile": state.profile_db.get_by_id(req.id)}

@app.put("/api/profiles/{profile_id}")
async def update_profile(profile_id: str, req: ProfileCreateReq):
    success = state.profile_db.update_profile(profile_id, req.name, req.tag)
    if not success:
        raise HTTPException(status_code=404, detail="Profile not found")
    return {"message": "Profile updated", "profile": state.profile_db.get_by_id(profile_id)}

@app.delete("/api/profiles/{profile_id}")
async def delete_profile(profile_id: str):
    success = state.profile_db.remove_profile(profile_id)
    if not success:
        raise HTTPException(status_code=404, detail="Profile not found")
    return {"message": "Profile deleted"}

@app.post("/api/warmup/start")
async def start_bot(req: StartRequest, request: Request):
    if state.is_running:
        raise HTTPException(status_code=400, detail="Bot is already running")
    
    token = extract_token(request)
    thread = threading.Thread(target=run_automation_thread, args=(req.profile_ids, req.mode, token, req.duration, req.minimized), daemon=True)
    thread.start()
    
    return {"message": "Automation started securely and dynamically evaluated"}

@app.post("/api/warmup/stop")
async def stop_bot(machine_id: str = "default"):
    state.stop_requested = True
    return {"message": "Stop requested"}

@app.post("/api/scheduler/update")
async def update_scheduler(request: Request, machine_id: str = "default"):
    config = await request.json()
    state.scheduler_config.update(config)
    
    token = extract_token(request)
    if token:
        state.scheduler_config["_access_token"] = token
    
    # Regenerate slots immediately when config changes
    if config.get("active") or state.scheduler_config.get("active"):
        slots = scheduler_generate_slots(state.scheduler_config)
        state.scheduler_config["_slots"] = slots
        state.scheduler_config["_slots_date"] = datetime.date.today().isoformat()
    
    state.save_scheduler()
    
    total_slots = len(state.scheduler_config.get("_slots", []))
    pending_slots = len([s for s in state.scheduler_config.get("_slots", []) if not s.get("executed")])
    state.scheduler_status = {
        "total_sessions": total_slots,
        "pending_sessions": pending_slots,
        "active": state.scheduler_config.get("active", False)
    }
    
    return {"message": "Scheduler saved", "config": state.scheduler_config, "status": state.scheduler_status}

@app.get("/api/status")
@app.get("/api/warmup/status")
async def get_status(request: Request, machine_id: str = "default"):
    token = extract_token(request)
    plan_status = state.plan_manager.get_status(token)
    
    # PEGAR E-MAIL REAL DO TOKEN PARA A TRAVA
    real_email = ""
    try:
        from core.supabase_client import SupabaseManager
        sm = SupabaseManager()
        user_data = sm.client.auth.get_user(token)
        if user_data and user_data.user:
            real_email = user_data.user.email.lower().strip()
    except:
        pass

    # Só printar se o status mudar para evitar spam
    current_plan = plan_status.get('plan')
    if state.last_logged_account != real_email or state.last_logged_plan != current_plan:
        print(f"DEBUG [Server]: Account Identified: {real_email or 'Unknown'} | Final Plan: {current_plan}")
        state.last_logged_account = real_email
        state.last_logged_plan = current_plan
    
    # Calculate scheduler status dynamically
    slots = state.scheduler_config.get("_slots", [])
    pending = len([s for s in slots if not s.get("executed")])
    scheduler_status = {
        "total_sessions": len(slots),
        "pending_sessions": pending,
        "active": state.scheduler_config.get("active", False)
    }
    
    cloud_connected = cloud_bridge.is_connected if cloud_bridge else False
    
    return {
        "is_running": state.is_running,
        "is_paused": state.stop_requested, 
        "current_profile": state.current_profile,
        "results": state.results,
        "logs": state.logs[-50:],
        "agent_connected": True,
        "cloud_connected": cloud_connected,
        "machine_id": machine_id,
        "plan_status": plan_status,
        "current_task_start": state.current_task_start,
        "current_task_duration": state.current_task_duration,
        "scheduler_config": state.scheduler_config,
        "scheduler_status": scheduler_status
    }

@app.get("/api/cloud")
async def cloud_status():
    return {
        "connected": cloud_bridge.is_connected if cloud_bridge else False,
        "machine_id": machine_id
    }

# ═══════════════════════════════════════════════════════════════
#  CLOUD BRIDGE - callbacks for remote commands
# ═══════════════════════════════════════════════════════════════

def _cloud_on_start(profile_ids, mode, token, duration, minimized=False):
    """Called when the cloud dashboard sends a START command."""
    run_automation_thread(profile_ids, mode, token, duration, minimized)

def _cloud_on_stop():
    """Called when the cloud dashboard sends a STOP command."""
    state.stop_requested = True

def _cloud_get_status():
    """Returns current status for the cloud heartbeat."""
    return {
        "is_running": state.is_running,
        "current_profile": state.current_profile,
        "results": state.results,
        "current_task_start": state.current_task_start,
        "current_task_duration": state.current_task_duration,
    }

def _cloud_get_profiles():
    """Returns local profiles for the cloud dashboard."""
    return {"profiles": state.profile_db.get_all()}

def _cloud_get_scheduler():
    """Returns scheduler config for the cloud dashboard."""
    slots = state.scheduler_config.get("_slots", [])
    pending = len([s for s in slots if not s.get("executed")])
    return {
        "config": state.scheduler_config,
        "status": {
            "total_sessions": len(slots),
            "pending_sessions": pending,
            "active": state.scheduler_config.get("active", False)
        }
    }

# Machine ID & Bridge instance
machine_id = generate_machine_id()
cloud_bridge = None

# Load saved machine_id if exists
_config_path = user_data_path(os.path.join("config", "config.json"))
try:
    if os.path.exists(_config_path):
        with open(_config_path, 'r') as f:
            _cfg = json.load(f)
            machine_id = _cfg.get("machine_id", machine_id)
except:
    pass

# Save machine_id for future runs
try:
    os.makedirs(os.path.dirname(_config_path), exist_ok=True)
    with open(_config_path, 'w') as f:
        json.dump({"machine_id": machine_id}, f, indent=4)
except:
    pass

if __name__ == "__main__":
    # Start scheduler daemon
    threading.Thread(target=scheduler_daemon, daemon=True).start()
    
    # Start Cloud Bridge (connect to Railway)
    cloud_bridge = CloudBridge(
        machine_id=machine_id,
        on_start=_cloud_on_start,
        on_stop=_cloud_on_stop,
        get_status=_cloud_get_status,
        log_buffer=state.logs,
        get_profiles=_cloud_get_profiles,
        get_scheduler=_cloud_get_scheduler
    )
    cloud_bridge.start_in_background()
    state.logs.append(f"🆔 Machine ID: {machine_id[:12]}...")
    
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="warning", access_log=False)

