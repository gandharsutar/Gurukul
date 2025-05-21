from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from gtts import gTTS
import os
import uuid

# Init
app = FastAPI()
os.makedirs("audio", exist_ok=True)

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
    data = await request.json()
    text = data.get("text", "")
    lang = data.get("lang", "en")  # Default to English

    if not text:
        return {"error": "Text is required"}

    try:
        # Create unique file
        file_id = f"{uuid.uuid4().hex}.mp3"
        file_path = f"audio/{file_id}"

        # Generate speech
        tts = gTTS(text=text, lang=lang)
        tts.save(file_path)

        return {"audio_url": f"/audio/{file_id}"}
    except Exception as e:
        return {"error": str(e)}

@app.get("/audio/{filename}")
async def get_audio(filename: str):
    path = os.path.join("audio", filename)
    if os.path.exists(path):
        return FileResponse(path, media_type="audio/mpeg")
    return {"error": "File not found"}
