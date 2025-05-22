from fastapi import FastAPI, Request, Query
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from gtts import gTTS
import os
import uuid
import json

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
async def speak(request: Request, text: str = Query(None)):
    try:
        # 1. If text is provided as a query parameter
        if text:
            input_text = text

        # 2. Otherwise try to extract from JSON body
        else:
            body = await request.body()
            if not body:
                return {"error": "No text provided in query or body"}

            try:
                data = await request.json()
            except json.JSONDecodeError:
                return {"error": "Invalid JSON in request body"}

            input_text = data.get("text", "")

        if not input_text:
            return {"error": "Text is required"}

        # Create unique filename for audio file
        file_id = f"{uuid.uuid4().hex}.mp3"
        file_path = os.path.join("audio", file_id)

        # Generate audio with gTTS
        tts = gTTS(text=input_text, lang="en")
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="192.168.0.78", port=8000)
