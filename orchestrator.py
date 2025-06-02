from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import httpx  # For async HTTP requests

app = FastAPI(title="Multi-Agent Orchestration Service")

# === Schemas ===
class UserMessage(BaseModel):
    session_id: str
    user_input: str

class AgentResponse(BaseModel):
    response_text: str
    agent_name: str
    confidence: Optional[float] = None
    metadata: Optional[dict] = None

# === External Agent Endpoints (mock or real) ===
AGENT_ENDPOINTS = {
    "financial_crew": "http://localhost:8001/respond",
    "edumentor": "http://localhost:8002/respond",
    "wellness_bot": "http://localhost:8003/respond",
}

# === Routing Logic ===
def pick_agent(user_input: str) -> str:
    input_lower = user_input.lower()
    if any(word in input_lower for word in ["money", "investment", "finance", "loan"]):
        return "financial_crew"
    elif any(word in input_lower for word in ["study", "college", "exam", "education"]):
        return "edumentor"
    elif any(word in input_lower for word in ["stress", "health", "wellness", "sleep"]):
        return "wellness_bot"
    else:
        return "edumentor"  # Default fallback

# === Main Handler ===
@app.post("/chat", response_model=AgentResponse)
async def chat(message: UserMessage):
    agent_key = pick_agent(message.user_input)
    agent_url = AGENT_ENDPOINTS.get(agent_key)

    if not agent_url:
        raise HTTPException(status_code=400, detail="Unknown agent")

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(agent_url, json=message.dict())
            resp.raise_for_status()
            data = resp.json()
            return AgentResponse(
                response_text=data.get("response_text", ""),
                agent_name=agent_key,
                confidence=data.get("confidence"),
                metadata=data.get("metadata", {})
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent call failed: {str(e)}")
if __name__=="__main__":
    import uvicorn
    uvicorn.run(app,host="192.168.0.88",port=8000)