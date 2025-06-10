import subprocess
import uuid
import os
from pathlib import Path

def get_latest_mp3(folder="tts_outputs"):
    mp3_files = [f for f in os.listdir(folder) if f.endswith(".mp3")]
    if not mp3_files:
        raise FileNotFoundError("No MP3 files found in tts_outputs/")
    latest = max(mp3_files, key=lambda x: os.path.getctime(os.path.join(folder, x)))
    return os.path.join(folder, latest)

def convert_mp3_to_wav(mp3_path, wav_path):
    subprocess.run(["ffmpeg", "-y", "-i", mp3_path, wav_path], check=True)

def run_wav2lip(image_path, audio_path, output_path):
    subprocess.run([
        "python3", "inference.py",
        "--checkpoint_path", "checkpoints/wav2lip_gan.pth",
        "--face", image_path,
        "--audio", audio_path,
        "--outfile", output_path
    ], check=True)

if __name__ == "__main__":
    # Step 1: Get the most recent MP3
    mp3_file = get_latest_mp3()
    print(f"Using audio file: {mp3_file}")

    # Step 2: Generate UUID-based filenames
    session_id = str(uuid.uuid4())
    wav_file = f"temp_audio_{session_id}.wav"
    image_file = "guru.png"
    output_dir = Path("results")
    output_dir.mkdir(exist_ok=True)
    output_video = output_dir / f"{session_id}.mp4"

    # Step 3: Convert MP3 to WAV
    convert_mp3_to_wav(mp3_file, wav_file)

    # Step 4: Run lip-sync
    run_wav2lip(image_file, wav_file, str(output_video))

    print(f"Lip-sync complete. Output saved to {output_video}")
