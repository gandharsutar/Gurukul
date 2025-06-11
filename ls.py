import subprocess
import uuid
import os
from pathlib import Path
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
import shutil
import tempfile

app = FastAPI(title="LipSync API")

def get_latest_mp3(folder="tts/tts_outputs"):
    folder = Path(folder)
    if not folder.exists():
        raise FileNotFoundError(f"Folder {folder} does not exist")
    mp3_files = list(folder.glob("*.mp3"))
    if not mp3_files:
        raise FileNotFoundError(f"No MP3 files found in {folder}")
    return str(max(mp3_files, key=lambda x: x.stat().st_ctime))

def convert_mp3_to_wav(mp3_path, wav_path):
    try:
        subprocess.run(["ffmpeg", "-y", "-i", mp3_path, wav_path], check=True)
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"FFmpeg conversion failed: {str(e)}")

def run_wav2lip(image_path, audio_path, output_path):
    wav2lip_dir = Path(__file__).parent / "Wav2Lip"
    
    if not wav2lip_dir.exists():
        raise HTTPException(status_code=500, detail=f"Wav2Lip directory not found at {wav2lip_dir}")

    try:
        subprocess.run([
            "python", "inference.py",
            "--checkpoint_path", "checkpoints/wav2lip_gan.pth",
            "--face", str(Path(image_path).resolve()),
            "--audio", str(Path(audio_path).resolve()),
            "--outfile", str(Path(output_path).resolve())
        ], check=True, cwd=str(wav2lip_dir))
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"Wav2Lip processing failed: {str(e)}")

@app.post("/lipsync/", response_class=FileResponse)
async def create_lipsync_video(image: UploadFile = File(...)):
    try:
        # Create temporary directory for processing
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Save uploaded image
            session_id = str(uuid.uuid4())
            image_path = temp_path / f"input_{session_id}.png"
            with image_path.open("wb") as buffer:
                shutil.copyfileobj(image.file, buffer)

            # Get latest MP3
            mp3_file = get_latest_mp3()

            # Generate file paths
            wav_file = temp_path / f"temp_audio_{session_id}.wav"
            output_dir = Path("results")
            output_dir.mkdir(exist_ok=True)
            output_video = output_dir / f"{session_id}.mp4"

            # Convert MP3 to WAV
            convert_mp3_to_wav(mp3_file, str(wav_file))

            # Run lip-sync
            run_wav2lip(str(image_path), str(wav_file), str(output_video))

            # Return the output video
            return FileResponse(
                path=str(output_video),
                filename=f"lipsync_{session_id}.mp4",
                media_type="video/mp4"
            )

    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="192.168.1.103", port=8001)