from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import FileResponse, JSONResponse,PlainTextResponse
import edge_tts
import uuid
import os
from pathlib import Path
import asyncio
import aiohttp
from aiohttp import ClientConnectionError
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.requests import Request
import traceback


app = FastAPI()
OUTPUT_DIR = "tts_outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

@app.exception_handler(ClientConnectionError)
async def aiohttp_client_error_handler(request: Request, exc: ClientConnectionError):
    return PlainTextResponse("TTS client connection lost. Please try again later.", status_code=503)

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

async def try_save_with_retries(communicate, filepath, retries=3, delay=2):
    for attempt in range(retries):
        try:
            task = asyncio.create_task(communicate.save(filepath))
            await task
            return
        except aiohttp.ClientConnectionError as e:
            err_msg = str(e)
            if "WinError 64" in err_msg or "WinError 10054" in err_msg:
                if attempt < retries - 1:
                    print(f"[Retry {attempt+1}] Network error: {err_msg} — retrying in {delay}s...")
                    await asyncio.sleep(delay)
                    continue
                raise HTTPException(status_code=503, detail=f"Network issue: {err_msg}")
            raise HTTPException(status_code=503, detail="TTS client connection error.")
        except Exception as e:
            print("Unexpected error:", traceback.format_exc())
            raise HTTPException(status_code=500, detail=f"TTS generation failed: {str(e)}")

@app.post("/api/generate")
async def text_to_speech(text: str = Form(...), voice: str = Form("en-US-AriaNeural")):
    if not text:
        raise HTTPException(status_code=400, detail="Text is required")
    if len(text) > 500:
        raise HTTPException(status_code=400, detail="Text too long. Limit to 500 characters.")
    
    filename = f"{uuid.uuid4()}.mp3"
    filepath = os.path.join(OUTPUT_DIR, filename)

    try:
        communicate = edge_tts.Communicate(text, voice)
        await try_save_with_retries(communicate, filepath)

        if not os.path.exists(filepath):
            raise HTTPException(status_code=500, detail="Audio generation failed")

        return JSONResponse({
            "status": "success",
            "audio_url": f"/api/audio/{filename}",
            "filename": filename,
            "voice": voice
        })
    except HTTPException as http_ex:
        raise http_ex
    except Exception as e:
        print("Fatal error:\n", traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Fatal error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="192.168.1.103", port=8001)
