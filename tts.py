from fastapi import FastAPI, Request
from pydantic import BaseModel
from uuid import uuid4
import requests
import os

app = FastAPI()

BHASHINI_API_URL = "https://dhruva-api.bhashini.gov.in/services/inference/pipeline"
BHASHINI_AUTH_TOKEN = "YOUR_BHASHINI_API_KEY"  # Replace with your token
OUTPUT_DIR = "audio_outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

class TTSRequest(BaseModel):
    text: str
    language: str  # e.g., "hi" for Hindi, "en" for English
    session_id: str

@app.post("/generate-tts")
def generate_tts(req: TTSRequest):
    output_filename = f"{req.session_id}_{uuid4().hex}.mp3"
    output_path = os.path.join(OUTPUT_DIR, output_filename)

    payload = {
        "pipelineTasks": [
            {
                "taskType": "tts",
                "config": {
                    "language": {
                        "sourceLanguage": req.language
                    },
                    "gender": "female"
                }
            }
        ],
        "inputData": {
            "input": [
                {
                    "source": req.text
                }
            ]
        }
    }

    headers = {
        "Authorization": f"Bearer {BHASHINI_AUTH_TOKEN}",
        "Content-Type": "application/json"
    }

    response = requests.post(BHASHINI_API_URL, headers=headers, json=payload)

    if response.status_code == 200:
        audio_url = response.json()["pipelineResponse"][0]["audio"][0]["audioUri"]
        audio_data = requests.get(audio_url).content
        with open(output_path, "wb") as f:
            f.write(audio_data)
        return {
            "audio_path": f"/audio/{output_filename}",
            "session_id": req.session_id
        }
    else:
        return {"error": "Failed to fetch audio from Bhashini", "details": response.text}

# Serve audio files
from fastapi.staticfiles import StaticFiles
app.mount("/audio", StaticFiles(directory=OUTPUT_DIR), name="audio")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="192.168.0.71", port=8000)