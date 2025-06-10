from fastapi import FastAPI, Form, Request, HTTPException
from fastapi.responses import FileResponse, JSONResponse
import edge_tts
import uuid
import os
from pathlib import Path
import asyncio

app = FastAPI()
OUTPUT_DIR = "tts_outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

@app.get("/")
async def root():
    return {"message": "Edge TTS Service is running"}

@app.get("/api/audio/{filename}")
async def get_audio_file(filename: str):
    filepath = os.path.join(OUTPUT_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Audio file not found")
    return FileResponse(path=filepath, filename=filename, media_type='audio/mpeg')

@app.get("/api/list-audio-files")
async def list_audio_files():
    files = [f for f in os.listdir(OUTPUT_DIR) if f.endswith('.mp3')]
    return {"audio_files": files, "count": len(files)}

# POST method to generate audio using Edge TTS
@app.post("/api/generate")
async def text_to_speech(text: str = Form(...), voice: str = Form("en-US-AriaNeural")):
    if not text:
        raise HTTPException(status_code=400, detail="Text is required")
    
    filename = f"{uuid.uuid4()}.mp3"
    filepath = os.path.join(OUTPUT_DIR, filename)
    
    try:
        # Initialize Edge TTS communicator
        communicate = edge_tts.Communicate(text, voice)
        
        # Save the audio to file
        await communicate.save(filepath)
        
        if not os.path.exists(filepath):
            raise HTTPException(status_code=500, detail="Audio generation failed")
            
        return JSONResponse({
            "status": "success",
            "audio_url": f"/api/audio/{filename}",
            "filename": filename,
            "voice": voice
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="192.168.1.103", port=8001)