"""
CloudBridge — WebSocket tunnel between the local SAS and the Cloud Dashboard.

When the SAS starts, this module connects to the Railway cloud server via WebSocket.
It receives commands (START, STOP, SCHEDULER_UPDATE) from the cloud dashboard
and forwards them to the local automation engine (server.py's run_automation_thread).
It also sends logs, status updates, and results back to the cloud in real-time.
"""
import asyncio
import json
import hashlib
import platform
import uuid
import threading
import time
import datetime
import traceback
from typing import Optional, Callable

try:
    import websockets
except ImportError:
    websockets = None

CLOUD_SERVER = "wss://web-production-373eb.up.railway.app/ws/agent"


def generate_machine_id() -> str:
    """Generate a unique machine ID based on hardware identifiers."""
    unique_str = platform.node() + str(uuid.getnode())
    return hashlib.sha1(unique_str.encode()).hexdigest()


class CloudBridge:
    """
    Manages a persistent WebSocket connection to the cloud dashboard.
    Receives remote commands and forwards them to local automation.
    """
    
    def __init__(self, machine_id: str, on_start: Callable, on_stop: Callable, get_status: Callable, log_buffer: list, get_profiles: Callable = None, get_scheduler: Callable = None):
        """
        Args:
            machine_id: Unique identifier for this machine
            on_start: Callback(profile_ids, mode, token, duration) to start automation
            on_stop: Callback() to stop automation
            get_status: Callback() -> dict with current status
            log_buffer: Reference to the shared log list from AppState
            get_profiles: Callback() -> list of profiles from local DB
            get_scheduler: Callback() -> dict with scheduler config/status
        """
        self.machine_id = machine_id
        self.on_start = on_start
        self.on_stop = on_stop
        self.get_status = get_status
        self.get_profiles = get_profiles
        self.get_scheduler = get_scheduler
        self.log_buffer = log_buffer
        
        self.ws = None
        self.is_connected = False
        self._loop = None
        self._last_log_index = 0  # Track which logs we've already sent
        
    @property
    def server_url(self):
        return f"{CLOUD_SERVER}/{self.machine_id}"
    
    async def _send(self, data: dict):
        """Safely send a JSON message to the cloud."""
        if self.ws and self.is_connected:
            try:
                await self.ws.send(json.dumps(data))
            except Exception:
                pass

    async def _send_status(self):
        """Send current local status to cloud dashboard."""
        try:
            status = self.get_status()
            await self._send({
                "type": "STATUS_UPDATE",
                "is_running": status.get("is_running", False),
                "current_profile": status.get("current_profile"),
                "results": status.get("results", {}),
            })
        except Exception:
            pass
    
    async def _sync_logs(self):
        """Send any new log lines to the cloud."""
        try:
            current_len = len(self.log_buffer)
            if current_len > self._last_log_index:
                new_logs = self.log_buffer[self._last_log_index:current_len]
                self._last_log_index = current_len
                for msg in new_logs[-10:]:  # Send max 10 at a time to avoid flooding
                    await self._send({
                        "type": "LOG",
                        "machine_id": self.machine_id,
                        "data": {"message": msg}
                    })
        except Exception:
            pass
    
    async def _handle_message(self, message: str):
        """Process an incoming command from the cloud dashboard."""
        try:
            data = json.loads(message)
            mtype = data.get("type")
            
            if mtype == "START":
                config = data.get("data", {})
                pids = config.get("profile_ids", [])
                mode = config.get("mode", "1")
                duration = config.get("duration")
                token = config.get("access_token", "")
                
                self.log_buffer.append(f"☁️ Comando remoto recebido: Iniciar {len(pids)} perfis")
                
                # Run in a separate thread to not block the WebSocket loop
                threading.Thread(
                    target=self.on_start, 
                    args=(pids, mode, token, duration), 
                    daemon=True
                ).start()
                
            elif mtype == "STOP":
                self.log_buffer.append("☁️ Comando remoto: PARAR motor")
                self.on_stop()
                
            elif mtype == "SCHEDULER_UPDATE":
                cfg = data.get("data", {})
                self.log_buffer.append(f"☁️ Agendamento atualizado remotamente")
            
            elif mtype == "DATA_REQUEST":
                req_id = data.get("request_id")
                req_type = data.get("request_type")
                response_data = None
                
                if req_type == "GET_PROFILES" and self.get_profiles:
                    response_data = self.get_profiles()
                elif req_type == "GET_SCHEDULER" and self.get_scheduler:
                    response_data = self.get_scheduler()
                
                if req_id:
                    await self._send({
                        "type": "DATA_RESPONSE",
                        "request_id": req_id,
                        "data": response_data
                    })
                
        except Exception as e:
            self.log_buffer.append(f"⚠ Erro ao processar comando cloud: {str(e)}")
    
    async def _heartbeat_loop(self):
        """Periodically send heartbeat, status, and new logs to the cloud."""
        while True:
            try:
                if self.ws and self.is_connected:
                    await self._send({"type": "HEARTBEAT", "machine_id": self.machine_id})
                    await self._send_status()
                    await self._sync_logs()
            except Exception:
                pass
            await asyncio.sleep(5)
    
    async def connect(self):
        """Main connection loop. Auto-reconnects on failure."""
        if websockets is None:
            self.log_buffer.append("⚠ Cloud Bridge desativado: módulo 'websockets' não instalado.")
            return
            
        while True:
            try:
                self.log_buffer.append(f"☁️ Conectando ao Cloud Dashboard...")
                
                async with websockets.connect(
                    self.server_url, 
                    ping_interval=20, 
                    ping_timeout=20
                ) as ws:
                    self.ws = ws
                    self.is_connected = True
                    self._last_log_index = len(self.log_buffer)  # Don't send old logs on reconnect
                    
                    self.log_buffer.append(f"✅ Cloud Bridge conectado! ID: {self.machine_id[:12]}...")
                    
                    # Start heartbeat in background
                    heartbeat_task = asyncio.create_task(self._heartbeat_loop())
                    
                    try:
                        async for message in ws:
                            await self._handle_message(message)
                    finally:
                        heartbeat_task.cancel()
                        
            except Exception as e:
                self.is_connected = False
                self.ws = None
                err = str(e)
                
                # Only log connection errors occasionally to avoid log spam
                if "ssl" in err.lower():
                    self.log_buffer.append("☁️ Erro SSL na conexão cloud. Verificar data/hora do PC.")
                elif "refused" in err.lower() or "10061" in err:
                    pass  # Server temporarily down, retry silently
                else:
                    self.log_buffer.append(f"☁️ Reconectando ao cloud em 10s...")
                    
                await asyncio.sleep(10)

    def start_in_background(self):
        """Start the cloud bridge in a background thread with its own event loop."""
        def _run():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            self._loop = loop
            loop.run_until_complete(self.connect())
        
        thread = threading.Thread(target=_run, daemon=True)
        thread.start()
        return thread
