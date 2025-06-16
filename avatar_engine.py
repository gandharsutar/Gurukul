import subprocess
import uuid
import os
from pathlib import Path
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
import shutil
import tempfile
import subprocess
import librosa
import numpy as np

import pickle
from tensorflow.keras.models import load_model

app = FastAPI(title="LipSync API")

# Define paths for pre-defined avatar images
FEMALE_AVATAR_1 = "./avatars/pht1.jpg"
FEMALE_AVATAR_2 = "./avatars/pht2.jpg"
MALE_AVATAR_1 = "./avatars/pht3.jpg"
MALE_AVATAR_2 = "./avatars/pht4.jpg"

# Placeholder for the pre-trained gender detection model
gender_model = None
GENDER_MODEL_DIR = "gender-recognition-by-voice/results"

def load_gender_model():
    global gender_model
    try:
        gender_model = load_model(os.path.join(GENDER_MODEL_DIR, "model.h5"))
        print("Gender model loaded successfully.")
    except Exception as e:
        print(f"An error occurred while loading the gender model: {e}")

def predict_gender(audio_path, **kwargs):
    if gender_model is None:
        print("Gender model not loaded.")
        return "unknown"
    try:
        features = extract_features(audio_path, **kwargs)
        # The model expects a batch of inputs, so we add an extra dimension
        features = np.expand_dims(features, axis=0)
        prediction = gender_model.predict(features)[0]
        # Assuming the model outputs a probability for male (1) or female (0)
        return "male" if prediction >= 0.5 else "female"
    except Exception as e:
        print(f"Error predicting gender: {e}")
        return "unknown"

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

def extract_features(file_name, **kwargs):
    mfcc = kwargs.get("mfcc")
    mel = kwargs.get("mel")
    X, sample_rate = librosa.core.load(file_name)
    result = np.array([])
    if mfcc:
        mfccs = np.mean(librosa.feature.mfcc(y=X, sr=sample_rate, n_mfcc=40).T, axis=0)
        result = np.hstack((result, mfccs))
    if mel:
        mel = np.mean(librosa.feature.melspectrogram(y=X, sr=sample_rate).T, axis=0)
        result = np.hstack((result, mel))
    return result

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
async def create_lipsync_video():
    try:
        # Create temporary directory for processing
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            session_id = str(uuid.uuid4())

            # Get latest MP3
            mp3_file = get_latest_mp3()

            # Generate file paths
            wav_file = temp_path / f"temp_audio_{session_id}.wav"
            output_dir = Path("results")
            output_dir.mkdir(exist_ok=True)
            output_video = output_dir / f"{session_id}.mp4"

            # Convert MP3 to WAV
            convert_mp3_to_wav(mp3_file, str(wav_file))

            # Predict gender
            gender = predict_gender(str(wav_file), mfcc=True, mel=True)
            selected_image_path = None
            if gender == "male":
                selected_image_path = MALE_AVATAR_1 # Or MALE_AVATAR_2 based on some logic
            elif gender == "female":
                selected_image_path = FEMALE_AVATAR_1 # Or FEMALE_AVATAR_2 based on some logic
            else:
                raise HTTPException(status_code=500, detail="Could not determine gender for avatar selection.")

            if not Path(selected_image_path).exists():
                raise HTTPException(status_code=500, detail=f"Selected avatar image not found at {selected_image_path}")

            # Run lip-sync with selected avatar
            run_wav2lip(selected_image_path, str(wav_file), str(output_video))

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
    load_gender_model()
    uvicorn.run(app, host="192.168.0.111", port=8001)