from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from gtts import gTTS
import uuid
import subprocess
import os
from pathlib import Path
import numpy as np
import librosa
import traceback
from keras.models import load_model

app = FastAPI()

# Directories
TTS_OUTPUT_DIR = "tts_outputs"
RESULTS_DIR = "results"
AVATAR_DIR = os.path.abspath("avatars")
GENDER_MODEL_PATH = "gender-recognition-by-voice/results/model.h5"
WAV2LIP_PATH = "Wav2Lip"
WAV2LIP_CHECKPOINT = "checkpoints/wav2lip_gan.pth"

os.makedirs(TTS_OUTPUT_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)

# Load gender model once
gender_model = None
if os.path.exists(GENDER_MODEL_PATH):
    gender_model = load_model(GENDER_MODEL_PATH)
else:
    print(f"⚠️ Gender model not found at {GENDER_MODEL_PATH}")

# Avatar config
AVATARS = {
    "female": [os.path.join(AVATAR_DIR, "pht1.jpg"), os.path.join(AVATAR_DIR, "pht2.jpg")],
    "male": [os.path.join(AVATAR_DIR, "pht3.jpg"), os.path.join(AVATAR_DIR, "pht4.jpg")],
    "default": os.path.join(AVATAR_DIR, "pht1.jpg")

}


def extract_features(file_path: str) -> np.ndarray:
    try:
        X, sample_rate = librosa.load(file_path, sr=None)
        if len(X) == 0:
            return np.array([])

        # Updated librosa melspectrogram call
        mel = np.mean(
            librosa.feature.melspectrogram(
                y=X, 
                sr=sample_rate, 
                n_mels=128,
                fmax=8000  # Explicitly set max frequency
            ).T, 
            axis=0
        )
        return mel
    except Exception as e:
        print("Feature extraction error:", traceback.format_exc())
        return np.array([])

def predict_gender(audio_path: str) -> str:
    if gender_model is None:
        return "default"

    features = extract_features(audio_path)
    if features.size != 128:
        features = np.pad(features, (0, 128 - features.shape[0]), mode='constant')

    features = np.expand_dims(features, axis=0)
    prediction = gender_model.predict(features, verbose=0)[0]
    return "male" if prediction >= 0.5 else "female"


def select_avatar(gender: str) -> str:
    import random
    return random.choice(AVATARS.get(gender, [AVATARS["default"]]))


def convert_mp3_to_wav(mp3_path: str, wav_path: str):
    subprocess.run(["ffmpeg", "-y", "-i", mp3_path, wav_path], check=True)


def run_wav2lip(audio_path: str, image_path: str, output_path: str):
    print(f"[DEBUG] Avatar image path: {os.path.abspath(image_path)}")  # Add this line
    subprocess.run([
        "python", "inference.py",
        "--checkpoint_path", WAV2LIP_CHECKPOINT,
        "--face", os.path.abspath(image_path),
        "--audio", os.path.abspath(audio_path),
        "--outfile", os.path.abspath(output_path)
    ], cwd=WAV2LIP_PATH, check=True)


@app.post("/api/generate-and-sync")
async def generate_and_sync(text: str = Form(...)):
    if not text:
        raise HTTPException(status_code=400, detail="Text is required")

    if len(text) > 500:
        text = text[:500]

    session_id = str(uuid.uuid4())
    mp3_filename = f"{session_id}.mp3"
    mp3_path = os.path.join(TTS_OUTPUT_DIR, mp3_filename)

    try:
        # Generate TTS
        tts = gTTS(text=text, lang='en', slow=False)
        tts.save(mp3_path)

        # Convert to WAV
        wav_path = os.path.join(TTS_OUTPUT_DIR, f"{session_id}.wav")
        convert_mp3_to_wav(mp3_path, wav_path)

        # Predict gender
        gender = predict_gender(wav_path)
        avatar_path = select_avatar(gender)

        # Lip Sync
        output_video = os.path.join(RESULTS_DIR, f"{session_id}.mp4")
        run_wav2lip(wav_path, avatar_path, output_video)

        return FileResponse(
            path=output_video,
            filename=f"lipsync_{session_id}.mp4",
            media_type="video/mp4"
        )

    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"FFmpeg/Wav2Lip failed: {e.stderr}")
    except Exception as e:
        print("Unexpected error:", traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@app.get("/")
def root():
    return {"message": "Unified TTS-LipSync Service running"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="192.168.1.105", port=8001)
