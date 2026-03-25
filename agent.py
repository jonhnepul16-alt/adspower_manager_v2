import asyncio
import json
import websockets
import sys
import os
import time
from typing import List, Dict, Any, Optional

# Reconfigure stdout for UTF-8 to handle special characters on Windows
if sys.platform == "win32":
    try:
        import sys
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    except:
        pass

# Adjust paths to import local core logic
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.account_manager import AccountManager
from main import facebook_warmup_por_tempo, MODOS_TEMPO, salvar_relatorio, set_log_callback

# Configuration
SERVER_URL = "ws://localhost:8000/ws/agent"  # Change to your cloud domain later
MACHINE_ID = "default"

class RemoteAgent:
    def __init__(self, machine_id: str, server_url: str):
        self.machine_id = machine_id
        self.server_url = f"{server_url}/{machine_id}"
        self.manager = AccountManager()
        self.ws: Any = None
        self.is_running = False

    async def send(self, msg_type: str, data: Any = None, message: Optional[str] = None):
        """Send a message to the cloud server."""
        if self.ws:
            payload = {"type": msg_type}
            if data is not None: payload["data"] = data
            if message is not None: payload["message"] = message
            if data is not None and msg_type == "RESULT": 
                payload["profile_id"] = data.get("profile_id") # specific for result
            
            try:
                await self.ws.send(json.dumps(payload))
            except Exception as e:
                print(f"Failed to send {msg_type}: {e}")

    async def log(self, message: str):
        """Send a log message to the server's terminal."""
        try:
            print(message)
        except UnicodeEncodeError:
            print(message.encode('ascii', 'ignore').decode('ascii'))
        await self.send("LOG", message=message)

    async def update_status(self, is_running: bool, current_profile: Optional[str] = None):
        """Update the cloud's view of the agent's state."""
        self.is_running = is_running
        await self.send("STATUS_UPDATE", data={
            "is_running": is_running,
            "current_profile": current_profile
        })

    def run_warmup_sync(self, profile_ids: List[str], modo: str):
        """
        Synchronous wrapper for the existing automation logic.
        Communicates back to the async loop via a queue or simple markers.
        """
        # We'll run this in a thread to not block the WS heartbeat
        pass

    async def execute_task(self, profile_ids: List[str], mode_key: str):
        if self.is_running:
            return

        self.is_running = True
        await self.update_status(True)

        if mode_key not in MODOS_TEMPO:
             # Try mapping by name if key fails
             for k, v in MODOS_TEMPO.items():
                if v[0] == mode_key:
                    mode_key = k
                    break
        
        if mode_key not in MODOS_TEMPO:
            await self.log("✗ Erro: Modo inválido selecionado.")
            self.is_running = False
            await self.update_status(False)
            return

        nome_modo, duracao = MODOS_TEMPO[mode_key]
        
        await self.log(f"▶ Iniciando Fila de Aquecimento: {len(profile_ids)} perfis.")
        
        for idx, pid in enumerate(profile_ids, 1):
            if not self.is_running:
                await self.log("!! Parada solicitada via dashboard.")
                break
                
            await self.update_status(True, current_profile=pid)
            await self.log(f"[{idx}/{len(profile_ids)}] Perfil: {pid}")
            
            # 1. Open Browser
            session = self.manager.open_account(pid)
            if not session:
                await self.log(f"✗ Erro ao abrir {pid}")
                continue
                
            await self.log(f"✓ Perfil {pid} carregado.")
            
            # 2. Run Automation
            # Since this is synchronous Selenium, we run it directly. 
            # Note: In a production agent, we'd use a separate process or thread.
            try:
                resultado = self.manager.run_task(
                    pid,
                    lambda ctrl, d=duracao, m=nome_modo: facebook_warmup_por_tempo(
                        ctrl, d, m, log_callback=self.log_sync # We need to pass a callback to capture sub-logs
                    ),
                )
                
                # Capture result
                if isinstance(resultado, dict):
                    # details = resultado.get("details", resultado)
                    await self.send("RESULT", data=resultado, message=f"Result for {pid}")
                
                await self.log(f"✓ Perfil {pid} concluído.")
            except Exception as e:
                await self.log(f"✗ Falha crítica em {pid}: {e}")
            finally:
                self.manager.close_account(pid)
                
            if idx < len(profile_ids) and self.is_running:
                await self.log("⏳ Intervalo entre perfis...")
                await asyncio.sleep(5)

        await self.send("FINISHED")
        self.is_running = False
        await self.update_status(False)
        await self.log("🏁 Operação de aquecimento finalizada.")

    def log_sync(self, message: str):
        """Synchronous version for internal libraries to call."""
        # Use asyncio.run_coroutine_threadsafe if needed, 
        # but for now we'll just print to stdout which is captured by the main loop if we redirect.
        print(message)

    async def connect(self):
        set_log_callback(self.log) # Hook into main.py prints
        while True:
            try:
                print(f"Connecting to {self.server_url}...")
                async with websockets.connect(self.server_url) as websocket:
                    self.ws = websocket
                    await self.log(f"Agent '{self.machine_id}' online e pronto.")
                    
                    async for message in websocket:
                        command = json.loads(message)
                        cmd_type = command.get("type")
                        
                        if cmd_type == "START":
                            data = command.get("data", {})
                            # Run in background so we don't block the WS receiver
                            asyncio.create_task(self.execute_task(
                                data.get("profile_ids", []),
                                data.get("mode", "1")
                            ))
                        elif cmd_type == "STOP":
                            self.is_running = False
                            await self.log("Stop command received.")

            except Exception as e:
                print(f"Connection lost: {e}. Retrying in 5s...")
                await asyncio.sleep(5)

if __name__ == "__main__":
    agent = RemoteAgent(MACHINE_ID, SERVER_URL)
    asyncio.run(agent.connect())
