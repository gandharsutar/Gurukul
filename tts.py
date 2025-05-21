# Import required modules and libraries
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import pyttsx3  # Text-to-speech engine
import os
import uuid
import json
import threading

# Init
app = FastAPI()
os.makedirs("audio", exist_ok=True)

# Initialize pyttsx3 engine
def get_tts_engine():
    engine = pyttsx3.init()
    # Configure properties
    engine.setProperty('rate', 150)  # Speed of speech
    engine.setProperty('volume', 1.0)  # Volume (0.0 to 1.0)
    return engine

# Use a thread-local storage for the TTS engine
tts_engine_local = threading.local()

# CORS (allow frontend access)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/speak")
async def speak(request: Request):
    try:
        # Check if request body is empty
        body = await request.body()
        if not body:
            return {"error": "Empty request body"}

        # Parse JSON
        try:
            data = await request.json()
        except json.JSONDecodeError:
            return {"error": "Invalid JSON in request body"}

        text = data.get("text", "")
        lang = data.get("lang", "en")  # Used to select voice if available

        if not text:
            return {"error": "Text is required"}

        # Create unique file
        file_id = f"{uuid.uuid4().hex}.wav"
        file_path = os.path.join("audio", file_id)

        # Generate speech using pyttsx3
        if not hasattr(tts_engine_local, 'engine'):
            tts_engine_local.engine = get_tts_engine()

        engine = tts_engine_local.engine

        # Set voice based on language if available
        voices = engine.getProperty('voices')
        if lang.startswith('en'):
            # Try to find an English voice
            for voice in voices:
                if 'en' in voice.id.lower():
                    engine.setProperty('voice', voice.id)
                    break

        # Save to file
        engine.save_to_file(text, file_path)
        engine.runAndWait()

        # Check if file was created
        if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
            return {"error": "Failed to generate audio file"}

        return {"audio_url": f"/audio/{file_id}"}
    except Exception as e:
        return {"error": str(e)}

@app.get("/audio/{filename}")
async def get_audio(filename: str):
    path = os.path.join("audio", filename)
    if os.path.exists(path):
        return FileResponse(path, media_type="audio/wav")
    return {"error": "File not found"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="192.168.0.71", port=8000)
