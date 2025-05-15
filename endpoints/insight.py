from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, Literal
from threading import Lock

app = FastAPI()

# Define agent types
AgentName = Literal["financial_crew", "edumentor", "wellness_bot"]

# Define mood/status enums
StatusType = Literal["online", "offline", "busy"]
MoodType = Literal["happy", "neutral", "tired", "frustrated","calm"]

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

    def get_all_agents(self) -> Dict[str, AgentState]:
        with self.lock:
            return {k: v.dict() for k, v in self._agents.items()}

    def update_agent(self, agent: AgentName, key: str, value):
        with self.lock:
            if agent in self._agents and hasattr(self._agents[agent], key):
                setattr(self._agents[agent], key, value)

# Instance
agent_manager = AgentManager()


@app.get("/agent-insight/live", response_model=Dict[str, AgentState])
async def get_agent_insight():
    """
    Return live status of all registered agents.
    """
    return agent_manager.get_all_agents()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="192.168.0.94", port=8000)