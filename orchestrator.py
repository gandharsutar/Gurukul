from fastapi import FastAPI, HTTPException
from pymongo import MongoClient
import requests
from dotenv import load_dotenv
import os
import logging
import json
from datetime import datetime
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from pydantic import BaseModel

# Load environment variables
load_dotenv()

# MongoDB Config
MONGO_URI = os.getenv("MONGODB_URI")
DB_NAME = os.getenv("MONGODB_DB")
COLLECTION_NAME = os.getenv("MONGODB_COLLECTION")

# External API Endpoints
AGENT_ENDPOINTS = {
    "financial_crew": os.getenv("FINANCIAL_API"),
    "wellness_bot": os.getenv("WELLNESS_API"),
    "edumentor": os.getenv("EDUMENTOR_API")
}

# Agent profiles (used for message similarity)
AGENT_PROFILES = {
    "financial_crew": "I provide advice on money, investments, finance, taxes, retirement, and loans.",
    "wellness_bot": "I help with health, wellbeing, stress, sleep, mental fitness, and diet.",
    "edumentor": "I guide on study, courses, learning, education, university, career, and college."
}

# Prepare the TF-IDF vectorizer and agent profile vectors
vectorizer = TfidfVectorizer()
profile_texts = list(AGENT_PROFILES.values())
profile_vectors = vectorizer.fit_transform(profile_texts)

# Configure logging
logging.basicConfig(
    filename='routing_logs.log',
    filemode='a',
    format='%(message)s',
    level=logging.INFO
)

# Pydantic model for request body
class MessageRequest(BaseModel):
    message: str

def classify_input(message: str):
    """Classifies the input message to one or more agents using TF-IDF similarity and logs the action."""
    message_vec = vectorizer.transform([message])
    sims = cosine_similarity(message_vec, profile_vectors)[0]

    threshold = 0.2
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

# FastAPI setup
app = FastAPI()
client = MongoClient(MONGO_URI)
collection = client[DB_NAME][COLLECTION_NAME]

def forward_to_agents(message: str, targets: list):
    """Send the message to matched agents and return their responses."""
    responses = {}
    for agent in targets:
        url = AGENT_ENDPOINTS.get(agent)
        if not url:
            responses[agent] = {"error": "No URL configured"}
            continue
        try:
            res = requests.post(url, json={"message": message}, timeout=10)
            responses[agent] = res.json() if res.status_code == 200 else {"error": f"Status {res.status_code}"}
        except Exception as e:
            responses[agent] = {"error": str(e)}
    return responses

@app.post("/route-message")
def route_message(request: MessageRequest):
    """API endpoint to classify and route the message to relevant agents."""
    message = request.message
    if not message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    
    target_agents = classify_input(message)
    if not target_agents:
        return {
            "input": message,
            "agent_responses": {},
            "note": "No relevant agent matched the input."
        }

    agent_responses = forward_to_agents(message, target_agents)
    return {
        "input": message,
        "routed_to": target_agents,
        "agent_responses": agent_responses
    }