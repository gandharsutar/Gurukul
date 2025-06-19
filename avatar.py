import streamlit as st
import requests
import os
import time

# ========================
# Streamlit Configuration
# ========================
st.set_page_config(page_title="LipSync Avatar Generator", layout="centered")

st.title("🎙️ LipSync Avatar Generator")
st.markdown("Enter text below and generate a lip-synced video using AI avatars.")

# ========================
# Backend Configuration
# ========================
API_URL = "http://192.168.1.105:8001/api/generate-and-sync"  # Update if hosted remotely
TIMEOUT = 300  # seconds

# ========================
# Video Display Helper
# ========================
def display_video(video_path):
    with open(video_path, "rb") as f:
        video_bytes = f.read()
        st.video(video_bytes)
        return video_bytes

# ========================
# Main App
# ========================
def main():
    text_input = st.text_area("Enter text to synthesize", height=150, max_chars=3000)

    if st.button("Generate Lip-Synced Video"):
        if not text_input.strip():
            st.warning("Please enter some text.")
            return

        with st.spinner("Processing... This might take a minute or two."):
            try:
                response = requests.post(
                    API_URL,
                    data={"text": text_input.strip()},
                    timeout=TIMEOUT
                )

                if response.status_code == 200:
                    # Save video
                    video_filename = f"result_{int(time.time())}.mp4"
                    with open(video_filename, "wb") as f:
                        f.write(response.content)

                    st.success("Video generated successfully!")
                    video_bytes = display_video(video_filename)

                    # Download button
                    if video_bytes:
                        st.download_button(
                            label="Download Video",
                            data=video_bytes,
                            file_name=video_filename,
                            mime="video/mp4"
                        )

                else:
                    try:
                        error_msg = response.json().get("detail", "Unknown error")
                    except:
                        error_msg = response.text
                    st.error(f"Server error: {error_msg}")

            except requests.exceptions.RequestException as e:
                st.error(f"Connection error: {str(e)}")

if __name__ == "__main__":
    main()
