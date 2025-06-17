from fastapi import FastAPI, Form, HTTPException, UploadFile, File
from fastapi.responses import FileResponse, JSONResponse,PlainTextResponse
from gtts import gTTS
import uuid
import subprocess
import os
from pathlib import Path

import traceback


app = FastAPI()
OUTPUT_DIR = "tts_outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs("results", exist_ok=True)


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

async def try_save_with_retries(tts, filepath, retries=3, delay=2):
    for attempt in range(retries):
        try:
            tts.save(filepath)
            return

        except Exception as e:
            print("Unexpected error:", traceback.format_exc())
            raise HTTPException(status_code=500, detail=f"TTS generation failed: {str(e)}")

@app.post("/api/generate")
async def text_to_speech(text: str = Form(...)):
    if not text:
        raise HTTPException(status_code=400, detail="Text is required")
    
    # Truncate text if it's longer than 500 characters
    if len(text) > 500:
        text = text[:500]

    filename = f"{uuid.uuid4()}.mp3"
    filepath = os.path.join(OUTPUT_DIR, filename)

    try:
        tts = gTTS(text=text, lang='en', slow=False) # 'en' for English, slow=False for faster speech
        await try_save_with_retries(tts, filepath)

        if not os.path.exists(filepath):
            raise HTTPException(status_code=500, detail="Audio generation failed")

        return JSONResponse({
            "status": "success",
            "audio_url": f"/api/audio/{filename}",
            "filename": filename,

        })
    except HTTPException as http_ex:
        raise http_ex
    except Exception as e:
        print("Fatal error:\n", traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Fatal error: {str(e)}")

@app.post("/api/lip-sync")
async def lip_sync(audio_file: UploadFile = File(...), video_file: UploadFile = File(...)):
    audio_path = f"temp_{audio_file.filename}"
    video_path = f"temp_{video_file.filename}"
    output_path = f"results/lip_sync_{uuid.uuid4()}.mp4"

    with open(audio_path, "wb") as f:
        f.write(await audio_file.read())
    with open(video_path, "wb") as f:
        f.write(await video_file.read())

    command = [
        "python", "e:\\pythonProject\\Gurukul\\Wav2Lip\\inference.py",
        "--checkpoint_path", "e:\\pythonProject\\Gurukul\\Wav2Lip\\checkpoints\\wav2lip_gan.pth", # You might need to download this checkpoint
        "--face", video_path,
        "--audio", audio_path,
        "--outfile", output_path
    ]

    try:
        process = subprocess.run(command, capture_output=True, text=True, check=True)
        print("Wav2Lip Output:", process.stdout)
        print("Wav2Lip Error:", process.stderr)
    except subprocess.CalledProcessError as e:
        print("Wav2Lip Command Failed:", e.stderr)
        raise HTTPException(status_code=500, detail=f"Lip-sync generation failed: {e.stderr}")
    finally:
        os.remove(audio_path)
        os.remove(video_path)

    if not os.path.exists(output_path):
        raise HTTPException(status_code=500, detail="Lip-sync video generation failed.")

    return JSONResponse({
        "status": "success",
        "video_url": f"/api/video/{os.path.basename(output_path)}",
        "filename": os.path.basename(output_path)
    })

@app.get("/api/video/{filename}")
async def get_video_file(filename: str):
    filepath = os.path.join("results", filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Video file not found")
    return FileResponse(path=filepath, filename=filename, media_type='video/mp4')

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="192.168.1.105", port=8001)