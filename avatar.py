import streamlit as st
import requests
import os
from pathlib import Path
import base64
import time

# Configure Streamlit
st.set_page_config(
    page_title="LipSync Avatar",
    page_icon="🎥",
    layout="centered"
)

# API configuration
API_URL = "http://192.168.1.105:8001/lipsync/"
TIMEOUT = 300  # 5 minutes

def get_available_mp3s(folder="tts/tts_outputs"):
    folder = Path(folder)
    return [f.name for f in folder.glob("*.mp3")] if folder.exists() else []

def display_video(video_path: str):
    """Display video with retries for file availability"""
    max_retries = 5
    retry_delay = 1
    
    for attempt in range(max_retries):
        try:
            with open(video_path, "rb") as f:
                video_bytes = f.read()
                st.video(video_bytes)
                return video_bytes
        except FileNotFoundError:
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                continue
            raise
    return None

def main():
    st.title("LipSync Avatar Generator")
    st.markdown("Generate a lip-synced video using a dynamically selected avatar and audio file.")

    # Audio selection
    mp3_files = get_available_mp3s()
    if not mp3_files:
        st.warning("No MP3 files found in tts/tts_outputs")
        return
        
    selected_audio = st.selectbox("Select an audio file", mp3_files)

    if st.button("Generate LipSync Video"):
        with st.spinner("Generating lip-sync video..."):
            try:
                # Send request to API
                audio_path = Path("tts/tts_outputs") / selected_audio
                with open(audio_path, "rb") as audio_file:
                    files = {"audio": (selected_audio, audio_file, "audio/mpeg")}
                    response = requests.post(
                        API_URL,
                        files=files,
                        timeout=TIMEOUT
                    )

                if response.status_code == 200:
                    # Save and display video
                    video_path = f"temp_{selected_audio.replace('.mp3', '.mp4')}"
                    with open(video_path, "wb") as f:
                        f.write(response.content)

                    st.success("Lip-sync video generated successfully!")
                    video_bytes = display_video(video_path)

                    # Download button
                    if video_bytes:
                        st.download_button(
                            label="Download Video",
                            data=video_bytes,
                            file_name=f"lipsync_{selected_audio.replace('.mp3', '.mp4')}",
                            mime="video/mp4"
                        )

                    # Clean up
                    try:
                        os.remove(video_path)
                    except Exception as e:
                        st.warning(f"Could not clean up temporary file: {e}")
                else:
                    error_detail = response.json().get("detail", "Unknown error")
                    st.error(f"API Error: {error_detail}")

            except requests.exceptions.RequestException as e:
                st.error(f"Connection error: {str(e)}")
            except Exception as e:
                st.error(f"An unexpected error occurred: {str(e)}")

if __name__ == "__main__":
    main()