import sys
import json
import asyncio
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
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

class WarmupRequest(BaseModel):
    machine_id: str = "default"  # Added machine_id to specify which agent to target
    profile_ids: List[str]
    mode: str 

@app.get("/api/health")
def health_check():
    return {"status": "ok", "active_agents": list(manager.active_agents.keys())}

@app.post("/api/warmup/start")
async def start_warmup(req: WarmupRequest):
    state = get_state(req.machine_id)
    if state.is_running:
        raise HTTPException(status_code=400, detail="Agent is already busy")
    
    # Send command to agent
    command = {
        "type": "START",
        "data": {
            "profile_ids": req.profile_ids,
            "mode": req.mode
        }
    }
    
    ok = await manager.send_command(req.machine_id, command)
    if not ok:
        raise HTTPException(status_code=404, detail="Agent not connected")
    
    # Reset local cloud state for this agent
    state.is_running = True
    state.logs = []
    state.results = {}
    
    return {"message": "Command sent to agent", "machine_id": req.machine_id}

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
def get_status(machine_id: str = "default"):
    state = get_state(machine_id)
    return {
        "is_running": state.is_running,
        "current_profile": state.current_profile,
        "logs": state.logs,
        "results": state.results,
        "scheduler_config": state.scheduler_config,
        "scheduler_status": state.scheduler_status,
        "agent_connected": machine_id in manager.active_agents
    }

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

# --- WebSocket Agent Tunnel ---

@app.websocket("/ws/agent/{machine_id}")
async def agent_tunnel(websocket: WebSocket, machine_id: str):
    await manager.connect(machine_id, websocket)
    state = get_state(machine_id)
    try:
        while True:
            data = await websocket.receive_json()
            
            # Handle messages from agent
            msg_type = data.get("type")
            
            if msg_type == "LOG":
                state.logs.append(data.get("message"))
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
