from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import pyttsx3
import tempfile
import os
from pydub import AudioSegment
from datetime import datetime
import uuid

app = FastAPI()

# Create necessary directories
os.makedirs("tts_outputs", exist_ok=True)

# Initialize TTS engine with default settings
engine = pyttsx3.init()
engine.setProperty('rate', 150)  # Fixed speech rate
voices = engine.getProperty('voices')
if voices:  # Use first available voice
    engine.setProperty('voice', voices[0].id)

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Simple TTS Converter</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
            textarea { width: 100%; height: 200px; margin-bottom: 15px; }
            button { padding: 10px 15px; background-color: #4CAF50; color: white; border: none; cursor: pointer; }
            button:hover { background-color: #45a049; }
        </style>
    </head>
    <body>
        <h1>Simple Text-to-Speech Converter</h1>
        <form action="/generate-speech/" method="post">
            <textarea name="text" placeholder="Enter text here..." required></textarea>
            <button type="submit">Convert to Speech</button>
        </form>
    </body>
    </html>
    """

@app.post("/generate-speech/")
async def generate_speech(text: str = Form(...)):
    if not text.strip():
        raise HTTPException(status_code=400, detail="Please enter some text.")
    
    try:
        # Create temp WAV file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as wav_file:
            wav_path = wav_file.name
        
        # Generate speech
        engine.save_to_file(text, wav_path)
        engine.runAndWait()

        # Create output filename
        mp3_filename = f"tts_output_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3"
        mp3_path = os.path.join("tts_outputs", mp3_filename)

        # Convert to MP3
        sound = AudioSegment.from_wav(wav_path)
        sound.export(mp3_path, format="mp3")

        return FileResponse(
            mp3_path,
            media_type="audio/mp3",
            headers={"Content-Disposition": f"attachment; filename={mp3_filename}"}
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        if 'wav_path' in locals() and os.path.exists(wav_path):
            os.remove(wav_path)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="", port=8000)