from fastapi import FastAPI, HTTPException
import requests
from dotenv import load_dotenv
import os
import logging
import json
from datetime import datetime
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from pydantic import BaseModel
from typing import List, Dict, Optional
from fastapi.middleware.cors import CORSMiddleware

# Load environment variables
load_dotenv()

# Configuration
class AgentConfig(BaseModel):
    name: str
    endpoint: str
    profile: str

class LogEntry(BaseModel):
    timestamp: str
    input_message: str
    model: str
    similarities: Dict[str, float]
    routed_to: List[str]

# External API Endpoints
AGENT_ENDPOINTS = {
    "financial_crew": os.getenv("FINANCIAL_API", "http://localhost:8001/process"),
    "wellness_bot": os.getenv("WELLNESS_API", "http://localhost:8002/process"),
    "edumentor": os.getenv("EDUMENTOR_API", "http://localhost:8003/process")
}

# Agent profiles (used for message similarity)
AGENT_PROFILES = {
    "financial_crew": "I provide advice on money, investments, finance, taxes, retirement, and loans.",
    "wellness_bot": "I help with health, wellbeing, stress, sleep, mental fitness, and diet.",
    "edumentor": "I guide on study, courses, learning, education, university, career, and college."
}

# Initialize vectorizer and agent profile vectors
vectorizer = TfidfVectorizer(stop_words='english')
profile_texts = list(AGENT_PROFILES.values())
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

def classify_input(message: str) -> List[str]:
    """
    Classifies the input message to one or more agents using TF-IDF similarity.
    Returns list of agent names that match the message.
    """
    message_vec = vectorizer.transform([message])
    sims = cosine_similarity(message_vec, profile_vectors)[0]

    threshold = 0.2  # Minimum similarity score to route to an agent
    results = [
        {"agent": agent, "score": float(sim)}
        for agent, sim in zip(AGENT_PROFILES.keys(), sims)
        if sim > threshold
    ]
    routed_agents = [res["agent"] for res in results]

    # Log the classification action
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "input_message": message,
        "model": "TF-IDF + Cosine Similarity",
        "similarities": {agent: float(sim) for agent, sim in zip(AGENT_PROFILES.keys(), sims)},
        "routed_to": routed_agents
    }
    logging.info(json.dumps(log_entry))

    return routed_agents

def forward_to_agents(message: str, targets: List[str]) -> Dict[str, Dict]:
    """Send the message to matched agents and return their responses."""
    responses = {}
    for agent in targets:
        url = AGENT_ENDPOINTS.get(agent)
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
async def route_message(request: MessageRequest):
    """
    Route a message to the most appropriate agent(s) based on content analysis.
    
    Parameters:
    - message: The text message to be routed
    - user_id: Optional user identifier for personalization
    - context: Optional additional context for the message
    
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

    agent_responses = forward_to_agents(request.message, target_agents)
    return RoutingResponse(
        input=request.message,
        routed_to=target_agents,
        agent_responses=agent_responses
    )

@app.get("/agents", response_model=Dict[str, str])
async def list_agents():
    """List all available agents and their specialties"""
    return {
        agent: AGENT_PROFILES[agent].replace("I ", "").replace(".", "")
        for agent in AGENT_PROFILES
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="192.168.0.66", port=8000)