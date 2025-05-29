import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient
import datetime
import aiohttp
import os
import uuid
import logging
import threading
import time
import requests
import json
import glob

# --- SERVER CONFIGURATION ---
MONGODB_URI = "mongodb+srv://blackholeinfiverse1:ImzKJBDjogqox4nQ@user.y9b2fg6.mongodb.net/?retryWrites=true&w=majority&appName=user"
DB_NAME = "user_data"
COLLECTION_NAME = "tts"
AUDIO_SAVE_DIR = "audio_files"

# Default ComfyUI URL
DEFAULT_COMFYUI_BASE_URL = "http://127.0.0.1:8188/"

# Ensure directory exists for audio files
os.makedirs(AUDIO_SAVE_DIR, exist_ok=True)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- FastAPI Application ---
app = FastAPI()
client = AsyncIOMotorClient(MONGODB_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

class AudioFetchRequest(BaseModel):
    source_url: str

@app.post("/fetch-audio/")
async def fetch_audio(data: AudioFetchRequest):
    file_id = str(uuid.uuid4())
    filename = f"{file_id}.mp3"
    filepath = os.path.join(AUDIO_SAVE_DIR, filename)

    logger.info(f"Server: Attempting to fetch audio from: {data.source_url}")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(data.source_url) as response:
                logger.info(f"Server: Response headers: {response.headers}")
                if response.status != 200:
                    error_detail = await response.text()
                    logger.error(f"Server: Failed to download audio: {response.status} - {error_detail}")
                    raise HTTPException(status_code=400, detail=f"Failed to download audio from source: {response.status} - {error_detail}")

                content_type = response.headers.get('Content-Type', '')
                if not content_type.startswith('audio/'):
                    logger.warning(f"Server: Unexpected content type received ({content_type}). Expected audio. Proceeding anyway.")

                with open(filepath, "wb") as f:
                    f.write(await response.read())
        logger.info(f"Server: Successfully downloaded audio to {filepath}")
    except aiohttp.ClientError as e:
        logger.error(f"Server: Network error while fetching audio from {data.source_url}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Network error fetching audio: {str(e)}")
    except Exception as e:
        logger.error(f"Server: Unexpected error fetching audio from {data.source_url}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error fetching audio: {str(e)}")

    metadata = {
        "file_id": file_id,
        "filename": filename,
        "saved_path": filepath,
        "source_url": data.source_url,
        "timestamp": datetime.datetime.now(datetime.timezone.utc),
    }
    try:
        await collection.insert_one(metadata)
        logger.info(f"Server: Stored metadata in MongoDB for file_id: {file_id}")
    except Exception as e:
        logger.error(f"Server: Error storing metadata in MongoDB: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error storing metadata in database: {str(e)}")

    return {"message": "Audio fetched and metadata stored", "file_id": file_id, "path": filepath}

# --- Helper Function to Find Latest ComfyUI Audio File ---
def get_latest_comfyui_file(comfyui_output_dir="ComfyUI/output", subfolder="audio", max_attempts=5, wait_interval=5):
    """
    Find the latest .mp3 file in the ComfyUI output directory with retries.
    Returns the filename and subfolder for use in the ComfyUI /view URL.
    Adjust `comfyui_output_dir` to the actual path of your ComfyUI installation.
    """
    attempt = 0
    while attempt < max_attempts:
        try:
            search_path = os.path.join(comfyui_output_dir, subfolder, "ComfyUI_*.mp3")
            audio_files = glob.glob(search_path)
            if not audio_files:
                logger.warning(f"Attempt {attempt + 1}/{max_attempts}: No .mp3 files found in {search_path}")
                attempt += 1
                if attempt < max_attempts:
                    logger.info(f"Waiting {wait_interval} seconds before retrying...")
                    time.sleep(wait_interval)
                continue
            
            latest_file = max(audio_files, key=os.path.getmtime)
            filename = os.path.basename(latest_file)
            logger.info(f"Found latest audio file: {filename} in subfolder: {subfolder}")
            return filename, subfolder
        except Exception as e:
            logger.error(f"Error finding latest ComfyUI audio file: {str(e)}")
            return None, None
    
    logger.error(f"Failed to find audio file after {max_attempts} attempts in {search_path}")
    return None, None

# --- Client Function ---
def run_client():
    FASTAPI_HOST = "127.0.0.1"
    FASTAPI_PORT = 8000
    FASTAPI_ENDPOINT = "/fetch-audio/"
    fastapi_url = f"http://{FASTAPI_HOST}:{FASTAPI_PORT}{FASTAPI_ENDPOINT}"

    # Fetch the latest audio file from ComfyUI
    comfyui_output_dir = "ComfyUI/output"  # Adjust to your ComfyUI output directory
    subfolder = "audio"  # Matches filename_prefix: audio/ComfyUI
    filename, subfolder = get_latest_comfyui_file(comfyui_output_dir, subfolder, max_attempts=5, wait_interval=5)
    
    if filename and subfolder:
        comfyui_generated_audio_url = f"{DEFAULT_COMFYUI_BASE_URL}view?filename={filename}&subfolder={subfolder}&type=output"
    else:
        logger.error("Could not find any audio file. Please ensure the ComfyUI workflow has been executed.")
        return  # Exit early if no file is found

    payload = {"source_url": comfyui_generated_audio_url}

    logger.info(f"Client: Waiting for server to start...")
    time.sleep(10)

    max_retries = 3
    for attempt in range(max_retries):
        try:
            logger.info(f"Client: Attempting to send request to: {fastapi_url}")
            logger.info(f"Client: Request Payload: {json.dumps(payload, indent=2)}")
            response = requests.post(fastapi_url, json=payload)
            if response.status_code == 200:
                logger.info("Client: Request successful!")
                logger.info(f"Client: Response: {response.json()}")
                return
            else:
                logger.error(f"Client: Request failed with status code: {response.status_code}")
                logger.error(f"Client: Error response from server: {response.text}")
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Client: Connection to server failed on attempt {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                time.sleep(5)
            else:
                logger.error("Client: Max retries reached. Could not connect to server.")
        except Exception as e:
            logger.error(f"Client: Unexpected error: {e}")
            break

# --- Main execution block ---
if __name__ == "__main__":
    server_thread = threading.Thread(target=uvicorn.run, args=(app,), kwargs={"host": "127.0.0.1", "port": 8000, "log_level": "info"})
    server_thread.daemon = True
    server_thread.start()
    logger.info("Main: FastAPI server thread initiated.")

    run_client()

    logger.info("Main: Client execution complete. Server might still be active in background.")