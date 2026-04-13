import sys
import json
import asyncio
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import os
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Request
from supabase import create_client, Client
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Vexel Cloud API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- WebSocket Manager ---
class ConnectionManager:
    def __init__(self):
        # machine_id -> socket
        self.active_agents: Dict[str, WebSocket] = {}
        # request_id -> asyncio.Future (for request-response pattern)
        self._pending: Dict[str, asyncio.Future] = {}
        self._req_counter = 0

    async def connect(self, machine_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_agents[machine_id] = websocket
        print(f"Agent {machine_id} connected")

    def disconnect(self, machine_id: str):
        if machine_id in self.active_agents:
            del self.active_agents[machine_id]
            print(f"Agent {machine_id} disconnected")

    async def send_command(self, machine_id: str, command: Dict[str, Any]):
        if machine_id in self.active_agents:
            await self.active_agents[machine_id].send_json(command)
            return True
        return False

    async def send_and_wait(self, machine_id: str, request_type: str, timeout: float = 5.0) -> Any:
        """Send a data request to the agent and wait for the response."""
        self._req_counter += 1
        req_id = f"req_{self._req_counter}"
        
        loop = asyncio.get_event_loop()
        future = loop.create_future()
        self._pending[req_id] = future
        
        ok = await self.send_command(machine_id, {
            "type": "DATA_REQUEST",
            "request_id": req_id,
            "request_type": request_type
        })
        
        if not ok:
            del self._pending[req_id]
            return None
        
        try:
            result = await asyncio.wait_for(future, timeout=timeout)
            return result
        except asyncio.TimeoutError:
            self._pending.pop(req_id, None)
            return None
    
    def resolve_request(self, req_id: str, data: Any):
        """Called when an agent responds to a data request."""
        future = self._pending.pop(req_id, None)
        if future and not future.done():
            future.set_result(data)

manager = ConnectionManager()

# --- Global State (Simple for now, should be in DB/Redis for real scale) ---
class AgentState:
    def __init__(self):
        self.is_running = False
        self.logs: List[str] = []
        self.current_profile: Optional[str] = None
        self.results: Dict[str, Any] = {}
        self.scheduler_status: Dict[str, Any] = {}
        self.scheduler_config: Dict[str, Any] = {
            "active": False,
            "windows": {
                "morning": {"enabled": True, "start": "08:00", "end": "12:00", "frequency": "medium"},
                "afternoon": {"enabled": True, "start": "13:00", "end": "18:00", "frequency": "medium"},
                "night": {"enabled": True, "start": "19:00", "end": "23:00", "frequency": "medium"}
            },
            "intensity": "normal",
            "style": "normal",
            "daily_limit": 15
        }

# machine_id -> AgentState
agent_states: Dict[str, AgentState] = {}

def get_state(machine_id: str) -> AgentState:
    if machine_id not in agent_states:
        agent_states[machine_id] = AgentState()
    return agent_states[machine_id]

# --- API Endpoints ---

# --- Supabase Config ---
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")

def get_supabase() -> Optional[Client]:
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        return None
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

def get_user_plan_from_token(token: str) -> Dict[str, Any]:
    """Helper to fetch plan from Supabase using the access token."""
    db = get_supabase()
    if not db:
        return {"plan": "START", "max_profiles": 5, "session_time": [10, 15]}
        
    try:
        # 1. Get user from token
        user_resp = db.auth.get_user(token)
        if not user_resp or not user_resp.user:
            print("DEBUG: Token validation failed - auth.get_user returned no user")
            return {"plan": "START", "max_profiles": 5, "session_time": [10, 15]}
        
        email = user_resp.user.email
        print(f"DEBUG: Identifying plan for account found in token: [{email}]")
        
        # 2. Get subscription (Case-insensitive search, get newest record first)
        sub_resp = db.table("subscriptions").select("*").ilike("email", email).order("created_at", desc=True).execute()
        
        row_count = len(sub_resp.data)
        if row_count > 1:
            print(f"WARNING: Found {row_count} records for {email}. Using the newest one.")
        else:
            print(f"DEBUG: Supabase query for {email} returned {row_count} row.")

        if sub_resp.data and len(sub_resp.data) > 0:
            record = sub_resp.data[0]
            print(f"DEBUG: Raw record from DB: {record}")
            
            # Canonicalize tier to uppercase for consistent logic
            raw_tier = record.get("tier", "start")
            tier = str(raw_tier).strip().upper()
            status = str(record.get("status", "unknown")).strip().lower()
            
            # If not active, fallback to START
            if status != "active":
                print(f"DEBUG: Account {email} is NOT active (status: {status}). Defaulting to START.")
                return {"plan": "START", "max_profiles": 5, "session_time": [10, 15], "max_machines": 1, "detected_email": email}
            
            if tier == "TEAM":
                print(f"DEBUG: Account {email} matched TEAM tier. UNLEASHING FULL POWER.")
                return {"plan": "TEAM", "max_profiles": 1000, "session_time": [1, 120], "max_machines": 8, "detected_email": email}
            elif tier == "SCALE":
                print(f"DEBUG: Account {email} matched SCALE tier. LIBERATING.")
                return {"plan": "SCALE", "max_profiles": 100, "session_time": [5, 60], "max_machines": 3, "detected_email": email}
            else:
                print(f"DEBUG: Account {email} matched tier [{tier}]. Enforcing START limits.")
                return {"plan": "START", "max_profiles": 5, "session_time": [10, 15], "max_machines": 1, "detected_email": email}
                
        # Default fallback for any other case
        print(f"DEBUG: No subscription record found for {email}. Defaulting to START.")
        return {"plan": "START", "max_profiles": 5, "session_time": [10, 15], "max_machines": 1, "detected_email": email}
    except Exception as e:
        print(f"CRITICAL ERROR in get_user_plan_from_token: {e}")
        import traceback
        traceback.print_exc()
        return {"plan": "START", "max_profiles": 5, "session_time": [10, 15]}

class ProfileUpdate(BaseModel):
    id: str # AdsPower ID
    name: str
    tag: str
    history: Optional[List[Dict[str, Any]]] = None

class WarmupRequest(BaseModel):
    machine_id: str = "default"
    profile_ids: List[str]
    mode: str 
    duration: Optional[int] = None

@app.get("/api/health")
def health_check():
    return {"status": "ok", "active_agents": list(manager.active_agents.keys())}

@app.post("/api/warmup/start")
async def start_warmup(request: Request, req: WarmupRequest):
    print(f"DEBUG: Backend recebeu solicitação de warmup para os IDs: {req.profile_ids} (Agent: {req.machine_id})")
    state = get_state(req.machine_id)
    if state.is_running:
        raise HTTPException(status_code=400, detail="Agent is already busy")
    
    # Determine plan limits
    plan_info = {"plan": "START", "max_profiles": 5, "session_time": [10, 15]}
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        pinfo = get_user_plan_from_token(auth_header.split(" ")[1])
        if pinfo: plan_info = pinfo

    # 1. Enforce max profiles
    pids = req.profile_ids[:plan_info["max_profiles"]]

    # 2. Enforce max duration
    duration = min(req.duration or 15, plan_info["session_time"][1])

    # 3. Enforce mode restrictions
    mode = req.mode
    if plan_info["plan"] == "START":
        mode = "1"

    # Send command to agent
    command = {
        "type": "START",
        "data": {
            "profile_ids": pids,
            "mode": mode,
            "duration": duration
        }
    }
    
    ok = await manager.send_command(req.machine_id, command)
    if not ok:
        raise HTTPException(status_code=404, detail="Agent not connected")
    
    # Reset local cloud state for this agent
    state.is_running = True
    state.logs = []
    state.results = {}
    
    return {"message": "Warmup started", "machine_id": req.machine_id}

@app.post("/api/warmup/stop")
async def stop_warmup(machine_id: str = "default"):
    # Always reset local cloud state first
    state = get_state(machine_id)
    state.is_running = False
    state.current_profile = None
    
    # Best-effort: try to notify the agent too (it may already be offline)
    await manager.send_command(machine_id, {"type": "STOP"})
    
    return {"message": "Stop command sent"}

@app.get("/api/warmup/status")
async def get_status(request: Request, machine_id: str = "default"):
    state = get_state(machine_id)
    
    # Try to get plan from token
    plan_info = {"plan": "START", "max_profiles": 5, "session_time": [10, 15]}
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        plan_info = get_user_plan_from_token(token)

    return {
        "is_running": state.is_running,
        "current_profile": state.current_profile,
        "logs": state.logs,
        "results": state.results,
        "scheduler_config": state.scheduler_config,
        "scheduler_status": state.scheduler_status,
        "agent_connected": machine_id in manager.active_agents,
        "plan_status": {
            "plan": plan_info["plan"],
            "limits": plan_info
        }
    }

@app.get("/api/profiles")
async def get_profiles_db(request: Request):
    """Fetch profiles from the cloud database (Supabase) for the logged-in user."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    token = auth_header.split(" ")[1]
    user_info = get_user_plan_from_token(token)
    email = user_info.get("detected_email")
    
    if not email:
        raise HTTPException(status_code=401, detail="User not found in token")

    db = get_supabase()
    if not db:
        return {"profiles": []}
    
    try:
        resp = db.table("profiles").select("*").eq("email", email).order("created_at", desc=True).execute()
        return {"profiles": resp.data}
    except Exception as e:
        print(f"Error fetching profiles from DB: {e}")
        return {"profiles": []}

@app.post("/api/profiles")
async def create_profile_db(request: Request, profile: ProfileUpdate):
    """Create or update a profile in the cloud database."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    token = auth_header.split(" ")[1]
    user_info = get_user_plan_from_token(token)
    email = user_info.get("detected_email")
    
    if not email:
        raise HTTPException(status_code=401, detail="User not found in token")

    db = get_supabase()
    if not db:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    profile_data = {
        "id": profile.id,
        "name": profile.name,
        "tag": profile.tag,
        "email": email
    }
    
    if profile.history is not None:
        profile_data["history"] = profile.history

    try:
        # Upsert: If ID exists, update it. Otherwise create.
        # Note: In Supabase, upsert requires the primary key 'id' to be provided.
        resp = db.table("profiles").upsert(profile_data).execute()
        if not resp.data:
            raise HTTPException(status_code=400, detail="Failed to save profile")
        return {"message": "Profile saved", "profile": resp.data[0]}
    except Exception as e:
        print(f"Error saving profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/profiles/{profile_id}")
async def update_profile_db(request: Request, profile_id: str, profile: ProfileUpdate):
    """Update an existing profile."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    token = auth_header.split(" ")[1]
    user_info = get_user_plan_from_token(token)
    email = user_info.get("detected_email")
    
    db = get_supabase()
    try:
        resp = db.table("profiles").update({
            "name": profile.name,
            "tag": profile.tag,
        }).eq("id", profile_id).eq("email", email).execute()
        
        if not resp.data:
            raise HTTPException(status_code=404, detail="Profile not found or access denied")
        return {"message": "Profile updated", "profile": resp.data[0]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/profiles/{profile_id}")
async def delete_profile_db(request: Request, profile_id: str):
    """Delete a profile from the database."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    token = auth_header.split(" ")[1]
    user_info = get_user_plan_from_token(token)
    email = user_info.get("detected_email")
    
    db = get_supabase()
    try:
        resp = db.table("profiles").delete().eq("id", profile_id).eq("email", email).execute()
        return {"message": "Profile deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/agent/profiles")
async def get_profiles_from_agent(machine_id: str = "default"):
    """Fetch live profiles directly from the local SAS agent via WebSocket tunnel."""
    if machine_id not in manager.active_agents:
        raise HTTPException(status_code=404, detail="Agent not connected. Open the SAS app first.")
    
    data = await manager.send_and_wait(machine_id, "GET_PROFILES")
    if data is None:
        raise HTTPException(status_code=504, detail="Agent did not respond in time")
    
    return data

@app.get("/api/scheduler")
async def get_scheduler_from_agent(machine_id: str = "default"):
    """Fetch scheduler config from the local SAS agent via WebSocket tunnel."""
    if machine_id not in manager.active_agents:
        raise HTTPException(status_code=404, detail="Agent not connected")
    
    data = await manager.send_and_wait(machine_id, "GET_SCHEDULER")
    if data is None:
        return {"config": {}, "status": {}}
    
    return data

@app.post("/api/scheduler/update")
async def update_scheduler(machine_id: str, config: Dict[str, Any]):
    state = get_state(machine_id)
    state.scheduler_config.update(config)
    
    # Notify agent about the change
    await manager.send_command(machine_id, {
        "type": "SCHEDULER_UPDATE",
        "data": state.scheduler_config
    })
    
    return {"message": "Scheduler config updated", "config": state.scheduler_config}

# --- Webhook Cakto ---
@app.post("/api/webhook/cakto")
async def cakto_webhook(request: Request):
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    
    event_status = payload.get("event") or payload.get("status")
    customer_email = None

    # Adaptando-se ao formato de payload da Cakto
    if "data" in payload and "customer" in payload["data"]:
        customer_email = payload["data"]["customer"].get("email")
    elif "customer" in payload:
        customer_email = payload["customer"].get("email")
    elif "email" in payload:
        customer_email = payload.get("email")

    # Identifica o plano (Tier) através do nome do produto
    product_name = ""
    if "data" in payload and "product" in payload["data"]:
        product_name = payload["data"]["product"].get("name", "")
    elif "product" in payload:
        product_name = payload["product"] if isinstance(payload["product"], str) else payload["product"].get("name", "")
    elif "product_name" in payload:
        product_name = payload.get("product_name", "")

    tier = "START"
    product_name_str = str(product_name).lower()
    if "equipe" in product_name_str or "team" in product_name_str:
        tier = "TEAM"
    elif "scale" in product_name_str:
        tier = "SCALE"
    
    print(f"Cakto Webhook: Evento de {customer_email} para o produto [{product_name}] -> Tier Detectado: {tier}")

    # Verifica se foi um pagamento aprovado/PIX finalizado
    if event_status in ["payment.approved", "PAID", "approved", "paid"]:
        db = get_supabase()
        if not db:
            print("Erro: SUPABASE chaves de ambiente não configuradas.")
            raise HTTPException(status_code=500, detail="Database config missing")
        
        try:
            # 1. Tenta criar o usuário automaticamente caso não exista
            default_password = "Warmads123"
            try:
                db.auth.admin.create_user({
                    "email": customer_email,
                    "password": default_password,
                    "email_confirm": True
                })
                print(f"Cakto Webhook: Conta VIP nova criada para {customer_email}.")
            except Exception:
                # Se falhar, na maioria das vezes é porque a conta já existe
                pass

            # 2. Atualiza o is_premium, status e TIER para conta do cara
            response = db.table("subscriptions").update({
                "is_premium": True,
                "status": "active",
                "tier": tier
            }).eq("email", customer_email).execute()

            if len(response.data) == 0:
                print(f"Cakto Webhook pago: Mas conta {customer_email} não foi encontrada na tabela subscriptions.")
            else:
                print(f"Cakto Webhook: Perfil {customer_email} atualizado para {tier} com sucesso!")
                
        except Exception as e:
            print(f"Cakto Webhook Falhou ao atualizar BD: {e}")
            raise HTTPException(status_code=500, detail="Supabase error")

    return {"status": "received"}

# --- WebSocket Agent Tunnel ---

@app.websocket("/ws/agent/{machine_id}")
async def agent_tunnel(websocket: WebSocket, machine_id: str):
    await manager.connect(machine_id, websocket)
    state = get_state(machine_id)
    
    # Sincroniza configuração inicial assim que o agente conecta
    await manager.send_command(machine_id, {
        "type": "SCHEDULER_UPDATE",
        "data": state.scheduler_config
    })
    try:
        while True:
            data = await websocket.receive_json()
            
            # Handle messages from agent
            msg_type = data.get("type")
            
            if msg_type == "LOG":
                # Extract from nested data field
                log_data = data.get("data", {})
                msg = log_data.get("message") if isinstance(log_data, dict) else data.get("message")
                if msg:
                    state.logs.append(str(msg))
                    if len(state.logs) > 500:
                        state.logs = state.logs[-500:]
                    
            elif msg_type == "STATUS_UPDATE":
                state.is_running = data.get("is_running", state.is_running)
                state.current_profile = data.get("current_profile", state.current_profile)
                
            elif msg_type == "RESULT":
                pid = data.get("profile_id")
                if pid:
                    state.results[pid] = data.get("data")

            elif msg_type == "SCHEDULER_STATUS":
                state.scheduler_status = data

            elif msg_type == "HEARTBEAT":
                pass

            elif msg_type == "DATA_RESPONSE":
                req_id = data.get("request_id")
                if req_id:
                    manager.resolve_request(req_id, data.get("data"))

            elif msg_type == "FINISHED":
                state.is_running = False
                state.current_profile = None

    except WebSocketDisconnect:
        manager.disconnect(machine_id)
        # Auto-reset running state so site doesn't show stale status
        state = get_state(machine_id)
        state.is_running = False
        state.current_profile = None
    except Exception as e:
        print(f"Error in tunnel for {machine_id}: {e}")
        manager.disconnect(machine_id)
        state = get_state(machine_id)
        state.is_running = False
        state.current_profile = None

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
