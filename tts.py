from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient
import datetime
import aiohttp
import os
import uuid
import logging
import json
from bson.objectid import ObjectId
from typing import Optional

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Config
MONGODB_URI = "mongodb+srv://blackholeinfiverse1:ImzKJBDjogqox4nQ@user.y9b2fg6.mongodb.net/?retryWrites=true&w=majority&appName=user"
DB_NAME = "user_data"
COLLECTION_NAME = "tts"
AUDIO_SAVE_DIR = "audio_files"
DEFAULT_COMFYUI_URL = "POST http://127.0.0.1:8188/"

# Ensure directory exists
os.makedirs(AUDIO_SAVE_DIR, exist_ok=True)

# FastAPI App
app = FastAPI()
client = AsyncIOMotorClient(MONGODB_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request Models
class AudioFetchRequest(BaseModel):
    source_url: str = DEFAULT_COMFYUI_URL

class KokoroTTSRequest(BaseModel):
    text: str
    speaker_name: Optional[str] = None
    language: Optional[str] = None
    speed: float = 1.0

# Get Kokoro options
async def get_kokoro_options():
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{DEFAULT_COMFYUI_URL}object_info") as response:
                if response.status != 200:
                    return {"speakers": ["am_onyx"], "languages": ["English"]}
                object_info = await response.json()
                speakers = object_info.get("KokoroSpeaker", {}).get("input", {}).get("speaker_name", {}).get("options", ["am_onyx"])
                languages = object_info.get("KokoroGenerator", {}).get("input", {}).get("lang", {}).get("options", ["English"])
                return {"speakers": speakers, "languages": languages}
    except Exception as e:
        logger.error(f"Error fetching Kokoro options: {str(e)}")
        return {"speakers": ["am_onyx"], "languages": ["English"]}

# Fetch audio from URL
@app.post("/fetch-audio/")
async def fetch_audio(data: AudioFetchRequest):
    file_id = str(uuid.uuid4())
    filename = f"{file_id}.mp3"
    filepath = os.path.join(AUDIO_SAVE_DIR, filename)

    logger.info(f"Fetching audio from: {data.source_url}")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(data.source_url) as response:
                if response.status != 200:
                    error_detail = await response.text()
                    raise HTTPException(status_code=400, detail=f"Failed to download audio: {response.status} - {error_detail}")
                
                content_type = response.headers.get("Content-Type", "")
                if "audio" not in content_type:
                    error_detail = await response.text()
                    raise HTTPException(status_code=400, detail=f"Invalid content-type '{content_type}': {error_detail[:100]}")

                data_bytes = await response.read()
                if len(data_bytes) < 1024:
                    raise HTTPException(status_code=400, detail="Downloaded file too small to be valid audio.")

                with open(filepath, "wb") as f:
                    f.write(data_bytes)

    except Exception as e:
        logger.error(f"Error fetching audio: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching audio: {str(e)}")

    metadata = {
        "file_id": file_id,
        "filename": filename,
        "saved_path": filepath,
        "source_url": data.source_url,
        "timestamp": datetime.datetime.now(datetime.timezone.utc),
    }
    await collection.insert_one(metadata)
    logger.info(f"Stored metadata in MongoDB: {metadata}")

    return {"message": "Audio fetched and metadata stored", "file_id": file_id, "path": filepath}

# Get Kokoro options
@app.get("/kokoro-options")
async def kokoro_options():
    return await get_kokoro_options()

# Generate TTS
@app.post("/generate-kokoro-tts/")
async def generate_kokoro_tts(data: KokoroTTSRequest):
    try:
        # Build your workflow dictionary using the uploaded JSON structure
        workflow = {
            "52": {
                "inputs": {
                    "text": data.text,
                    "speed": data.speed,
                    "lang": data.language or "Japanese",
                    "speaker": ["53", 0]
                },
                "class_type": "KokoroGenerator",
                "_meta": {"title": "Kokoro Generator"}
            },
            "53": {
                "inputs": {
                    "speaker_name": data.speaker_name or "am_onyx"
                },
                "class_type": "KokoroSpeaker",
                "_meta": {"title": "Kokoro Speaker"}
            },
            "56": {
                "inputs": {
                    "filename_prefix": "audio/ComfyUI",
                    "quality": "V0",
                    "audioUI": "",
                    "audio": ["52", 0]
                },
                "class_type": "SaveAudioMP3",
                "_meta": {"title": "Save Audio (MP3)"}
            }
        }

        async with aiohttp.ClientSession() as session:
            async with session.post("http://127.0.0.1:8188/prompt", json={"prompt": workflow}) as response:
                if response.status != 200:
                    error_detail = await response.text()
                    raise HTTPException(status_code=400, detail=f"Failed to send workflow: {response.status} - {error_detail}")
                result = await response.json()
                prompt_id = result.get("prompt_id")
                if not prompt_id:
                    raise HTTPException(status_code=500, detail="No prompt_id returned")
                return {"message": "TTS generation started", "prompt_id": prompt_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS generation error: {str(e)}")

# Check status
@app.get("/check-generation/{prompt_id}")
async def check_generation(prompt_id: str):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{DEFAULT_COMFYUI_URL}history/{prompt_id}") as response:
                if response.status != 200:
                    return {"status": "unknown", "message": "Unable to fetch from ComfyUI"}

                history = await response.json()
                prompt_data = history.get(prompt_id, {})
                if "outputs" in prompt_data:
                    for node_id, outputs in prompt_data["outputs"].items():
                        if "audio" in outputs and isinstance(outputs["audio"], dict):
                            filename = outputs["audio"]["filename"]
                            await collection.update_one(
                                {"prompt_id": prompt_id},
                                {"$set": {
                                    "status": "completed",
                                    "audio_filename": filename,
                                    "audio_url": f"{DEFAULT_COMFYUI_URL}view?filename={filename}"
                                }}
                            )
                            return {
                                "status": "completed",
                                "audio_url": f"{DEFAULT_COMFYUI_URL}view?filename={filename}",
                                "filename": filename
                            }

                if prompt_data.get("executing"):
                    return {"status": "processing"}

                return {"status": "error", "message": "No output found."}
    except Exception as e:
        logger.error(f"Check status error: {str(e)}")
        return {"status": "error", "message": str(e)}

# Serve audio by file_id
@app.get("/audio/{file_id}")
async def get_audio(file_id: str):
    audio_metadata = await collection.find_one({"file_id": file_id}) or await collection.find_one({"_id": ObjectId(file_id)})
    if not audio_metadata:
        raise HTTPException(status_code=404, detail="Audio file not found in DB.")
    filepath = audio_metadata.get("saved_path")
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Audio file not found on disk.")
    return FileResponse(path=filepath, media_type="audio/mpeg", filename=audio_metadata["filename"])

# List audio
@app.get("/list-audio")
async def list_audio():
    cursor = collection.find().sort("timestamp", -1)
    audio_files = await cursor.to_list(length=100)
    for audio in audio_files:
        audio["_id"] = str(audio["_id"])
    return {"audio_files": audio_files}

# Run app locally
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="192.168.0.108", port=8000)
