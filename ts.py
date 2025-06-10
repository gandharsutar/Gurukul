import streamlit as st
import requests
import time
from pathlib import Path
from streamlit.components.v1 import html
from pydantic import BaseModel
from fastapi import FastAPI

API_BASE="http://192.168.1.103:8001"
st.title("🗣️ Audio Player")

text_input=st.text_area("Enter your text",height=150)
voice = st.selectbox("Choose voice", ["en-US-AriaNeural", "en-US-GuyNeural", "en-GB-LibbyNeural"])

if st.button("Generate"):
    if not text_input.strip():
        st.error("Please enter some text.")
    else:
        with st.spinner("Generating audio..."):
            response = requests.post(
                f"{API_BASE}/api/generate",
                data={"text": text_input, "voice": voice}
            )

        if response.status_code == 200:
            data = response.json()
            audio_url = f"{API_BASE}{data['audio_url']}"
            filename = data['filename']
            st.success("Audio generated!")

            # Fetch the audio file
            audio_response = requests.get(audio_url)
            audio_path = Path(f"./{filename}")
            audio_path.write_bytes(audio_response.content)

            # Audio controls using HTML5
            audio_html = f"""
                <audio id="audioPlayer" controls>
                    <source src="data:audio/mp3;base64,{audio_response.content.encode('base64').decode()}" type="audio/mp3">
                    Your browser does not support the audio element.
                </audio>
                <br>
                <button onclick="document.getElementById('audioPlayer').play()">Play</button>
                <button onclick="document.getElementById('audioPlayer').pause()">Pause</button>
                <button onclick="document.getElementById('audioPlayer').currentTime=0;document.getElementById('audioPlayer').pause()">Stop</button>
                <button onclick="document.getElementById('audioPlayer').currentTime=0;document.getElementById('audioPlayer').play()">Replay</button>
            """
            html(audio_html, height=120)
        else:
            st.error(f"Failed to generate audio: {response.text}")
