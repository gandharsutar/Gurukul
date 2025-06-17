import subprocess
import uuid
import os
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
import tempfile
import librosa
import numpy as np
import logging
from typing import Optional
import subprocess
from contextlib import asynccontextmanager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define paths for pre-defined avatar images
AVATARS = {
    "female": ["./avatars/pht1.jpg", "./avatars/pht2.jpg"],
    "male": ["./avatars/pht3.jpg", "./avatars/pht4.jpg"],
    "default": "./avatars/pht1.jpg"  # Fallback avatar
}

# Gender detection model
gender_model = None
GENDER_MODEL_DIR = Path(__file__).parent / "gender-recognition-by-voice" / "results"

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Modern lifespan handler for startup/shutdown events"""
    global gender_model
    try:
        logger.info("Starting application...")
        load_gender_model()
        yield
    finally:
        logger.info("Cleaning up resources...")
        # Add any cleanup logic here if needed

def load_gender_model():
    """Load the gender detection model with error handling"""
    global gender_model
    try:
        from tensorflow.keras.models import load_model
        model_path = os.path.join(GENDER_MODEL_DIR, "model.h5")
        if not os.path.exists(model_path):
            logger.error(f"Model file not found at {model_path}")
            return
            
        gender_model = load_model(model_path)
        logger.info("Gender model loaded successfully")
        
        # Verify model input shape
        if hasattr(gender_model, 'input_shape'):
            logger.info(f"Model expects input shape: {gender_model.input_shape}")
    except Exception as e:
        logger.error(f"Failed to load gender model: {e}")
        gender_model = None

def predict_gender(audio_path: str) -> Optional[str]:
    """Predict gender from audio file with proper feature handling"""
    if gender_model is None:
        logger.warning("Gender model not available")
        return None
    
    try:
        # Extract only Mel features (128 coefficients)
        features = extract_features(audio_path, mfcc=False, chroma=False, mel=True)
        if features.size == 0:
            logger.error("Feature extraction failed - empty features")
            return None
            
        # Ensure correct feature dimensions
        expected_features = 128
        if features.shape[0] != expected_features:
            logger.warning(f"Adjusting features from {features.shape[0]} to {expected_features}")
            if features.shape[0] > expected_features:
                features = features[:expected_features]
            else:
                features = np.pad(features, (0, expected_features - features.shape[0]), 
                                mode='constant')
        
        features = np.expand_dims(features, axis=0)
        prediction = gender_model.predict(features, verbose=0)[0]
        logger.info(f"Gender prediction output: {prediction}")
        
        return "male" if prediction >= 0.5 else "female"
    except Exception as e:
        logger.error(f"Gender prediction failed: {e}", exc_info=True)
        return None

def get_avatar_path(gender: Optional[str]) -> str:
    """Select appropriate avatar with fallback to default"""
    if gender in AVATARS:
        import random
        return random.choice(AVATARS[gender])
    logger.warning(f"Using default avatar (invalid gender: {gender})")
    return AVATARS["default"]

def get_latest_mp3(folder="tts/tts_outputs") -> str:
    # Construct the full path relative to the user's home directory
    full_path = Path.home() / folder
    """Get most recent MP3 file with error handling"""
    if not full_path.exists():
        raise FileNotFoundError(f"Folder {full_path} does not exist")
    mp3_files = list(full_path.glob("*.mp3"))
    if not mp3_files:
        raise FileNotFoundError(f"No MP3 files found in {full_path}")
    return str(max(mp3_files, key=lambda x: x.stat().st_ctime))

def convert_mp3_to_wav(mp3_path: str, wav_path: str):
    """Convert audio format with proper error handling"""
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-i", mp3_path, wav_path],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.decode() if e.stderr else str(e)
        logger.error(f"FFmpeg conversion failed: {error_msg}")
        raise HTTPException(
            status_code=500,
            detail=f"Audio conversion failed: {error_msg}"
        )

def extract_features(file_name: str, mfcc: bool = False, chroma: bool = False, mel: bool = True) -> np.ndarray:
    """Extract specified audio features with proper error handling"""
    try:
        X, sample_rate = librosa.load(file_name, sr=None)
        if len(X) == 0:
            logger.error("Loaded empty audio file")
            return np.array([])
            
        result = np.array([])
        
        if mel:
            mel_features = np.mean(
                librosa.feature.melspectrogram(
                    y=X, 
                    sr=sample_rate, 
                    n_mels=128
                ).T,
                axis=0
            )
            result = np.hstack((result, mel_features))
        
        logger.debug(f"Extracted features shape: {result.shape}")
        return result
        
    except Exception as e:
        logger.error(f"Feature extraction failed: {e}", exc_info=True)
        return np.array([])

def run_wav2lip(image_path: str, audio_path: str, output_path: str):
    """Run Wav2Lip with proper error handling"""
    wav2lip_dir = Path(__file__).parent / "Wav2Lip"
    if not wav2lip_dir.exists():
        raise HTTPException(
            status_code=500,
            detail=f"Wav2Lip directory not found at {wav2lip_dir}"
        )

    try:
        result = subprocess.run(
            [
                "python", "inference.py",
                "--checkpoint_path", "checkpoints/wav2lip_gan.pth",
                "--face", str(Path(image_path).resolve()),
                "--audio", str(Path(audio_path).resolve()),
                "--outfile", str(Path(output_path).resolve())
            ],
            cwd=str(wav2lip_dir),
            check=True,
            capture_output=True,
            text=True
        )
        logger.debug(f"Wav2Lip output: {result.stdout}")
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr if isinstance(e.stderr, str) else e.stderr.decode()
        logger.error(f"Wav2Lip failed: {error_msg}")
        raise HTTPException(
            status_code=500,
            detail=f"Lip sync processing failed: {error_msg}"
        )

app = FastAPI(
    title="LipSync API",
    lifespan=lifespan
)

@app.post("/lipsync/")
async def create_lipsync_video():
    """Main endpoint for lip sync generation"""
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            session_id = str(uuid.uuid4())

            # Get and convert audio
            mp3_file = get_latest_mp3()
            wav_file = temp_path / f"temp_audio_{session_id}.wav"
            convert_mp3_to_wav(mp3_file, str(wav_file))

            # Predict gender with fallback
            gender = predict_gender(str(wav_file))
            avatar_path = get_avatar_path(gender)
            logger.info(f"Selected avatar: {avatar_path}")

            # Prepare output
            output_dir = Path("results")
            output_dir.mkdir(exist_ok=True)
            output_video = output_dir / f"{session_id}.mp4"

            # Run lip-sync
            run_wav2lip(avatar_path, str(wav_file), str(output_video))

            return FileResponse(
                path=str(output_video),
                filename=f"lipsync_{session_id}.mp4",
                media_type="video/mp4"
            )

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Processing failed: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="192.168.1.105", port=8001)