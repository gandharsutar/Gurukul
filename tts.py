from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from indic_transliteration.sanscript import transliterate, ITRANS, DEVANAGARI, BENGALI, TAMIL, TELUGU, MALAYALAM, KANNADA, GUJARATI, GURMUKHI
import pyttsx3
import os
import uuid
import threading
import time
from pathlib import Path
import asyncio

app = FastAPI()

# Configuration
AUDIO_DIR = "audio"
AUDIO_FORMAT = "wav"  # Changed from mp3 to wav for better compatibility
os.makedirs(AUDIO_DIR, exist_ok=True)
print(f"Audio directory '{AUDIO_DIR}' ensured to exist.")

# CORS setup with additional headers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"]
)

# Initialize pyttsx3 engine with multilingual support
def get_multilingual_tts_engine():
    try:
        engine = pyttsx3.init()
        engine.setProperty('rate', 150)
        engine.setProperty('volume', 1.0)

        voices = engine.getProperty('voices')
        voice_options = {
            'en': None,
            'hi': None,
            'ta': None,
            'te': None,
            'bn': None,
            'ml': None,
            'kn': None,
            'gu': None,
            'mr': None,
            'pa': None
        }

        print("\n--- Available voices on your system ---")
        for voice in voices:
            print(f"ID: {voice.id}, Name: {voice.name}, Languages: {voice.languages}")
            v_id = voice.id.lower()
            name = voice.name.lower()

            # Voice mapping logic (same as before)
            if 'en' in voice.languages or 'english' in name or 'en' in v_id:
                voice_options['en'] = voice.id
            if 'hi' in voice.languages or 'hindi' in name or 'hi' in v_id:
                voice_options['hi'] = voice.id
            # ... (rest of voice mapping)

        engine.voice_options = voice_options
        return engine
    except Exception as e:
        print(f"ERROR initializing TTS engine: {e}")
        return None

# Thread-local engine
tts_engine_local = threading.local()

# Pronunciation fixes (same as before)
hindi_pronunciation_fixes = {
    "aaj": "aadge",
    "kal": "call",
    # ... (rest of pronunciation fixes)
}

def fix_hindi_pronunciation(text):
    # ... (same implementation as before)
    return text

# Script code mapping
SCRIPT_MAP = {
    "hi": DEVANAGARI,
    "mr": DEVANAGARI,
    # ... (rest of script mapping)
}

def transliterate_if_needed(text: str, lang: str) -> str:
    # ... (same implementation as before)
    return text

def preprocess_text(text: str, lang: str) -> str:
    """Apply language-specific text processing"""
    if lang == "hi":
        text = fix_hindi_pronunciation(text)
        text = " ".join(text.split())
    elif lang == "ta":
        text = text.replace("zh", "ɻ")
    # ... (other language processing)
    return text

@app.post("/speak")
async def speak(
    text: str = Query(..., description="Text to convert to speech"),
    lang: str = Query("en", description="Language code (hi, ta, te, etc.)")
):
    try:
        if not text.strip():
            raise HTTPException(status_code=400, detail="Text is required")

        # Generate unique filename with correct extension
        file_id = f"{uuid.uuid4().hex}.{AUDIO_FORMAT}"
        file_path = os.path.join(AUDIO_DIR, file_id)
        
        # Initialize engine if needed
        if not hasattr(tts_engine_local, 'engine') or tts_engine_local.engine is None:
            tts_engine_local.engine = get_multilingual_tts_engine()
            if tts_engine_local.engine is None:
                raise HTTPException(status_code=500, detail="TTS engine initialization failed")

        engine = tts_engine_local.engine

        # Set voice if available
        if lang in engine.voice_options and engine.voice_options[lang]:
            engine.setProperty('voice', engine.voice_options[lang])

        # Process text
        text_to_speak = preprocess_text(text, lang)
        text_to_speak = transliterate_if_needed(text_to_speak, lang)

        # Ensure directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # Save to file
        engine.save_to_file(text_to_speak, file_path)
        engine.runAndWait()

        # Verify file was created
        if not os.path.exists(file_path):
            raise HTTPException(status_code=500, detail="Audio file creation failed")

        # Set correct permissions
        os.chmod(file_path, 0o644)

        return {"audio_url": f"/audio/{file_id}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/audio/{filename}")
async def get_audio(filename: str):
    file_path = os.path.join(AUDIO_DIR, filename)
    
    # Security check
    if not filename.endswith(f".{AUDIO_FORMAT}") or ".." in filename or "/" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    # Set proper headers
    headers = {
        "Content-Disposition": f"inline; filename={filename}",
        "Cache-Control": "public, max-age=3600"
    }
    
    return FileResponse(
        file_path,
        media_type="audio/wav" if AUDIO_FORMAT == "wav" else "audio/mpeg",
        headers=headers
    )

# Cleanup task to remove old files
async def cleanup_old_files():
    while True:
        try:
            now = time.time()
            for f in Path(AUDIO_DIR).glob(f"*.{AUDIO_FORMAT}"):
                if os.stat(f).st_mtime < now - 3600:  # 1 hour old
                    try:
                        os.remove(f)
                    except:
                        pass
        except:
            pass
        await asyncio.sleep(3600)  # Run every hour

# Start cleanup task when app starts
@app.on_event("startup")
async def startup_event():
    import asyncio
    asyncio.create_task(cleanup_old_files())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="192.168.0.71", port=8000)