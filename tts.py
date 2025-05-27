from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel
from typing import Dict, Any
import uuid
import json
import os

app = FastAPI()

# In-memory store (can be replaced with DB or file persistence)
TTS_GRAPH_STORE = {}

# Endpoint to accept a full TTS graph (like tts.json)
@app.post("/upload-graph/")
def upload_tts_graph(graph: Dict[str, Any] = Body(...)):
    graph_id = str(uuid.uuid4())
    TTS_GRAPH_STORE[graph_id] = graph
    return {"graph_id": graph_id, "message": "Graph uploaded successfully."}

# Endpoint to retrieve a specific TTS graph
@app.get("/graph/{graph_id}")
def get_graph(graph_id: str):
    graph = TTS_GRAPH_STORE.get(graph_id)
    if not graph:
        raise HTTPException(status_code=404, detail="Graph not found.")
    return graph

# Endpoint to simulate audio generation
@app.post("/generate-audio/{graph_id}")
def simulate_audio_generation(graph_id: str):
    graph = TTS_GRAPH_STORE.get(graph_id)
    if not graph:
        raise HTTPException(status_code=404, detail="Graph not found.")

    # Example: Fetch the final node (SaveAudioMP3) and simulate output
    final_nodes = [v for k, v in graph.items() if v["class_type"] == "SaveAudioMP3"]
    if not final_nodes:
        raise HTTPException(status_code=400, detail="No audio output node found.")

    fake_output_path = f"audio/{graph_id}.mp3"
    return {
        "message": "Audio generation simulated.",
        "output": fake_output_path,
        "graph_metadata": [v["_meta"] for v in final_nodes]
    }
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="192.168.0.108", port=8000)