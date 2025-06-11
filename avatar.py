import streamlit as st
import requests
import os
from pathlib import Path
import base64

# Streamlit page configuration
st.set_page_config(page_title="LipSync Avatar", page_icon="🎥", layout="centered")

# API endpoint
API_URL = "http://192.168.1.103:8001/lipsync/"

def get_available_mp3s(folder="tts/tts_outputs"):
    folder = Path(folder)
    if folder.exists():
        return [f.name for f in folder.glob("*.mp3")]
    return []

def main():
    st.title("LipSync Avatar Generator")
    st.markdown("Generate a lip-synced video using the default avatar image and a selected audio file.")

    # Use default image (guru.png)
    image_path = "guru.png"
    if not Path(image_path).exists():
        st.error(f"Default image {image_path} not found. Please ensure it exists in the same directory as this script.")
        return

    # Audio selection
    mp3_files = get_available_mp3s()
    selected_audio = st.selectbox("Select an audio file", mp3_files) if mp3_files else st.write("No MP3 files found in tts/tts_outputs")

    # Generate button
    if st.button("Generate LipSync Video", disabled=not (selected_audio)):
        with st.spinner("Generating lip-sync video..."):
            try:
                # Read the default image
                with open(image_path, "rb") as image_file:
                    image_data = image_file.read()

                # Send request to FastAPI backend
                files = {"image": ("guru.png", image_data, "image/png")}
                response = requests.post(API_URL, files=files, timeout=300)

                if response.status_code == 200:
                    # Save the video temporarily
                    video_path = "temp_video_guru.mp4"
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
                        file_name="lipsync_guru.mp4",
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