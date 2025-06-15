import streamlit as st
import requests
import os
from pathlib import Path
import base64

# Streamlit page configuration
st.set_page_config(page_title="LipSync Avatar", page_icon="🎥", layout="centered")

# API endpoint
API_URL = "http://192.168.0.111:8001/create_lipsync_video"

def get_available_mp3s(folder="tts/tts_outputs"):
    folder = Path(folder)
    if folder.exists():
        return [f.name for f in folder.glob("*.mp3")]
    return []

def main():
    st.title("LipSync Avatar Generator")
    st.markdown("Generate a lip-synced video using a dynamically selected avatar and a selected audio file.")

    # Audio selection
    mp3_files = get_available_mp3s()
    selected_audio = st.selectbox("Select an audio file", mp3_files) if mp3_files else st.write("No MP3 files found in tts/tts_outputs")

    # Generate button
    if st.button("Generate LipSync Video", disabled=not (selected_audio)):
        with st.spinner("Generating lip-sync video..."):
            try:
                # Read the selected audio file
                audio_file_path = Path("tts/tts_outputs") / selected_audio
                with open(audio_file_path, "rb") as audio_file:
                    audio_data = audio_file.read()

                # Send request to FastAPI backend
                files = {"audio": (selected_audio, audio_data, "audio/mpeg")}
                response = requests.post(API_URL, files=files, timeout=300)

                if response.status_code == 200:
                    # Save the video temporarily
                    video_path = f"temp_video_{selected_audio.replace('.mp3', '.mp4')}"
                    with open(video_path, "wb") as f:
                        f.write(response.content)

                    # Display video
                    st.success("Lip-sync video generated successfully!")
                    st.video(video_path)

                    # Provide download link
                    with open(video_path, "rb") as f:
                        video_bytes = f.read()
                    st.download_button(
                        label="Download Video",
                        data=video_bytes,
                        file_name=f"lipsync_{selected_audio.replace('.mp3', '.mp4')}",
                        mime="video/mp4"
                    )

                    # Clean up
                    os.remove(video_path)
                else:
                    st.error(f"Error: {response.json().get('detail', 'Failed to generate video')}")
            except requests.exceptions.RequestException as e:
                st.error(f"Failed to connect to the API: {str(e)}")
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()