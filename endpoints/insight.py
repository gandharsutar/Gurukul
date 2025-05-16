from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from typing import Dict, Literal, List
from threading import Lock
import asyncio
import json

app = FastAPI()

# Define agent types
AgentName = Literal["financial_crew", "edumentor", "wellness_bot"]

# Define mood/status enums
StatusType = Literal["online", "offline", "busy"]
MoodType = Literal["happy", "neutral", "tired", "frustrated", "calm"]

# State model
class AgentState(BaseModel):
    status: StatusType
    mood: MoodType
    model: str
    confidence: float

# Singleton-like store
class AgentManager:
    def __init__(self):
        self.lock = Lock()
        self._agents: Dict[AgentName, AgentState] = {
            "financial_crew": AgentState(status="online", mood="neutral", model="fin-bert-v2", confidence=0.88),
            "edumentor": AgentState(status="online", mood="happy", model="edu-gpt-3", confidence=0.93),
            "wellness_bot": AgentState(status="online", mood="calm", model="wellness-gpt", confidence=0.87)
        }
        self.websockets: List[WebSocket] = []  # Track connected websockets

    def get_all_agents(self) -> Dict[str, AgentState]:
        with self.lock:
            return {k: v.model_dump() for k, v in self._agents.items()}

    def update_agent(self, agent: AgentName, key: str, value):
        with self.lock:
            if agent in self._agents and hasattr(self._agents[agent], key):
                setattr(self._agents[agent], key, value)
        asyncio.create_task(self.notify_clients())  # Notify on update

    async def add_client(self, websocket: WebSocket):
        self.websockets.append(websocket)

    async def remove_client(self, websocket: WebSocket):
        self.websockets.remove(websocket)

    async def notify_clients(self):
        if self.websockets:
            message = json.dumps(self.get_all_agents())
            for ws in self.websockets:
                await ws.send_text(message)

from fastapi import BackgroundTasks

def simulate_agent_dynamics(agent: AgentName):
    import random

    # Example dynamic logic
    new_confidence = round(random.uniform(0.80, 0.99), 2)
    new_mood = random.choice(["happy", "neutral", "tired", "frustrated", "calm"])

    agent_manager.update_agent(agent, "confidence", new_confidence)
    agent_manager.update_agent(agent, "mood", new_mood)

    # Set status to busy briefly
    agent_manager.update_agent(agent, "status", "busy")

    # Return to online after 2 seconds
    import threading
    threading.Timer(2.0, lambda: agent_manager.update_agent(agent, "status", "online")).start()

# Instance
agent_manager = AgentManager()

@app.get("/agent-insight/live", response_model=Dict[str, AgentState])
async def get_agent_insight():
    """
    Return live status of all registered agents.
    """
    return agent_manager.get_all_agents()

@app.post("/agent-insight/use/{agent}")
async def simulate_agent_use(agent: AgentName, background_tasks: BackgroundTasks):
    background_tasks.add_task(simulate_agent_dynamics, agent)
    return {"message": f"Agent '{agent}' used. Status/mood will be updated dynamically."}

@app.websocket("/agent-insight/ws")
async def websocket_endpoint(websocket: WebSocket):
    await agent_manager.add_client(websocket)
    await websocket.accept()
    try:
        while True:
            await websocket.receive_text()  # Keep connection open
            #  No need to process messages from client in this example,
            #  but you might want to do so in a more complex app
    except WebSocketDisconnect:
        await agent_manager.remove_client(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="192.168.0.66", port=8000)