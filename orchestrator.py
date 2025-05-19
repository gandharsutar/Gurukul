from fastapi import FastAPI, HTTPException, Depends, Query
import requests
from dotenv import load_dotenv
import os
import logging
import json
from datetime import datetime
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from pydantic import BaseModel
from typing import List, Dict, Optional, Annotated
from fastapi.middleware.cors import CORSMiddleware

# Load environment variables
load_dotenv()

# Configuration
class AgentConfig(BaseModel):
    name: str
    endpoint: str
    profile: str
    backend_url: str

class LogEntry(BaseModel):
    timestamp: str
    input_message: str
    model: str
    similarities: Dict[str, float]
    routed_to: List[str]
    agent_responses: Dict[str, Dict]

# External API Endpoints
AGENT_CONFIG = {
    "financial_crew": AgentConfig(
        name="financial_crew",
        endpoint=os.getenv("FINANCIAL_API", "http://localhost:8001/process"),
        profile="I provide advice on money, investments, finance, taxes, retirement, and loans.",
        backend_url="https://your-friends-backend-url.com/api/financialcrew"
    ),
    "wellness_bot": AgentConfig(
        name="wellness_bot",
        endpoint=os.getenv("WELLNESS_API", "http://localhost:8002/process"),
        profile="I help with health, wellbeing, stress, sleep, mental fitness, and diet.",
        backend_url="https://your-wellnessbot-backend-url.com/api/wellnessbot"
    ),
    "edumentor": AgentConfig(
        name="edumentor",
        endpoint=os.getenv("EDUMENTOR_API", "http://localhost:8003/process"),
        profile="I guide on study, courses, learning, education, university, career, and college.",
        backend_url="https://your-edumentor-backend-url.com/api/edumentor"
    )
}

# Initialize vectorizer and agent profile vectors
vectorizer = TfidfVectorizer(stop_words='english')
profile_texts = [config.profile for config in AGENT_CONFIG.values()]
profile_vectors = vectorizer.fit_transform(profile_texts)

# Configure logging
logging.basicConfig(
    filename='orchestration.log',
    filemode='a',
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# FastAPI setup
app = FastAPI(
    title="Agent Orchestration Service",
    description="Routes messages to specialized agents based on content analysis",
    version="1.0.0"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class MessageRequest(BaseModel):
    message: str
    user_id: Optional[str] = None
    context: Optional[Dict] = None

class AgentResponse(BaseModel):
    agent: str
    response: Dict
    status: str

class RoutingResponse(BaseModel):
    input: str
    routed_to: List[str]
    agent_responses: Dict[str, Dict]
    note: Optional[str] = None

# --- Simulation Mode Logic ---
SIMULATION_MODE = False  # Global variable to control simulation mode
SIMULATION_RESPONSES = {  # Mock agent responses for simulation
    "financial_crew": {"response": "Simulated financial advice."},
    "wellness_bot": {"response": "Simulated wellness tip."},
    "edumentor": {"response": "Simulated education guidance."}
}

def get_simulation_response(agent_name: str):
    """Returns a simulated agent response."""
    return SIMULATION_RESPONSES.get(agent_name, {"error": "No simulation response."})

def classify_input(message: str) -> List[str]:
    """Classifies the input message to one or more agents using TF-IDF similarity."""

    message_vec = vectorizer.transform([message])
    sims = cosine_similarity(message_vec, profile_vectors)[0]

    threshold = 0.2
    results = [
        {"agent": agent, "score": float(sim)}
        for agent, sim in zip(AGENT_CONFIG.keys(), sims)
        if sim > threshold
    ]
    routed_agents = [res["agent"] for res in results]

    return routed_agents

def forward_to_agents(message: str, targets: List[str], simulation_mode: bool) -> Dict[str, Dict]:
    """Send the message to matched agents and return their responses."""

    responses = {}
    for agent in targets:
        if simulation_mode:
            responses[agent] = get_simulation_response(agent)
            continue  # Skip actual API call in simulation mode

        url = AGENT_CONFIG[agent].backend_url
        if not url:
            responses[agent] = {"error": "No URL configured for this agent"}
            continue

        try:
            payload = {"message": message}
            res = requests.post(url, json=payload, timeout=10)
            if res.status_code == 200:
                responses[agent] = res.json()
            else:
                responses[agent] = {
                    "error": f"Agent returned status {res.status_code}",
                    "details": res.text
                }
        except requests.exceptions.Timeout:
            responses[agent] = {"error": "Request to agent timed out"}
        except Exception as e:
            responses[agent] = {"error": str(e)}

    return responses

@app.post("/route", response_model=RoutingResponse)
async def route_message(
    request: MessageRequest,
    simulation: Annotated[Optional[bool], Query()] = False  # Query parameter for toggle
):
    """
    Route a message to the most appropriate agent(s) based on content analysis.

    Parameters:
    - message: The text message to be routed
    - user_id: Optional user identifier for personalization
    - context: Optional additional context for the message
    - simulation: Optional boolean query parameter to enable simulation mode
                  (e.g., /route?simulation=true)

    Returns:
    - Original input message
    - List of agents the message was routed to
    - Responses from each agent
    """
    if not request.message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    target_agents = classify_input(request.message)
    if not target_agents:
        return RoutingResponse(
            input=request.message,
            routed_to=[],
            agent_responses={},
            note="No relevant agent matched the input."
        )

    agent_responses = forward_to_agents(request.message, target_agents, simulation_mode=simulation) # Pass the simulation mode

    # Log the interaction
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "input_message": request.message,
        "model": "TF-IDF + Cosine Similarity",
        "similarities": {
            agent: float(cosine_similarity(vectorizer.transform([request.message]), vectorizer.transform([AGENT_CONFIG[agent].profile]))[0][0])
            for agent in AGENT_CONFIG
        },
        "routed_to": target_agents,
        "agent_responses": agent_responses
    }
    logging.info(json.dumps(log_entry))

    return RoutingResponse(
        input=request.message,
        routed_to=target_agents,
        agent_responses=agent_responses
    )

@app.get("/agents", response_model=Dict[str, str])
async def list_agents():
    """List all available agents and their specialties"""
    return {
        agent: AGENT_CONFIG[agent].profile.replace("I ", "").replace(".", "")
        for agent in AGENT_CONFIG
    }

@app.post("/call_agent/{agent_name}")
async def call_agent(agent_name: str, request: MessageRequest, simulation: Annotated[Optional[bool], Query()] = False):
    """
    Calls a specific agent's backend with the provided message.
    Now accepts a 'simulation' query parameter.
    """
    if agent_name not in AGENT_CONFIG:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")

    if simulation:
        return get_simulation_response(agent_name)

    agent_config = AGENT_CONFIG[agent_name]
    try:
        response = requests.post(
            agent_config.backend_url,
            json={"message": request.message},
            timeout=5
        )
        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(status_code=response.status_code, detail=f"Agent backend error: {response.text}")
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error connecting to agent backend: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="192.168.0.66", port=8000)