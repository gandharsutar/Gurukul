from fastapi import FastAPI, Request
from pydantic import BaseModel
from typing import List
import uvicorn
import requests
import datetime
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

GROQ_API_KEY = "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"

# Temporary in-memory storage
user_queries: List[dict] = []
llm_responses: List[dict] = []

# Pydantic model for request validation
class ChatMessage(BaseModel):
    message: str
    timestamp: str = None
    type: str = "chat_message"


# Route 1: Receive query from frontend
@app.post("/chatpost")
async def receive_query(chat: ChatMessage):
    timestamp = datetime.datetime.utcnow().isoformat() + "Z"
    query_record = {
        "message": chat.message,
        "timestamp": timestamp,
        "type": "chat_message"
    }
    user_queries.append(query_record)
    print(f"Received message: {chat.message}")
    return {"status": "Query received", "data": query_record}


import requests

def call_groq_llama3(prompt: str) -> str:
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "llama3-70b-8192",  # As per Groq model name
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 512,
        "top_p": 1.0,
        "stop": None
    }

    try:
        response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)

        response.raise_for_status()  # Raise error for bad status codes

        result = response.json()

        return result['choices'][0]['message']['content'].strip()

    except requests.exceptions.RequestException as e:
        print(f"Error calling Groq Llama3 API: {e}")
        return "Failed to fetch response from Groq Llama3 model."


# Route 2: Send LLM response back
@app.get("/chatbot")
async def send_response():
    if not user_queries:
        return {"error": "No queries yet"}

    latest_query = user_queries[-1]['message']
    print(f"Processing query: {latest_query}")

    llm_reply = call_groq_llama3(latest_query)

    timestamp = datetime.datetime.utcnow().isoformat() + "Z"
    response_record = {
        "message": llm_reply,
        "timestamp": timestamp,
        "type": "chat_response"
    }

    llm_responses.append(response_record)
    return response_record


# Run using: uvicorn filename:app --reload --port 5000
if __name__ == "__main__":
    uvicorn.run(app, host="192.168.0.122", port=8000)