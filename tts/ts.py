import streamlit as st
import requests
import base64
from streamlit.components.v1 import html

API_BASE = "http://192.168.1.103:8001"

st.title("🎧 Audio Player with Music Bar")

text_input = st.text_area("Enter text to convert to speech", height=150)
voice = st.selectbox("Choose voice", ["en-US-AriaNeural", "en-US-GuyNeural", "en-GB-LibbyNeural"])

if st.button("Generate Audio"):
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
            audio_response = requests.get(audio_url)
            audio_bytes = audio_response.content
            audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")

            # HTML + CSS + JS Audio Player with Progress Bar on Top
            player_html = f"""
            <style>
                .audio-container {{
                    width: 100%;
                    max-width: 400px;
                    margin: auto;
                    text-align: center;
                }}
                .progress-bar {{
                    width: 100%;
                    height: 8px;
                    background-color: #ddd;
                    border-radius: 5px;
                    margin-bottom: 10px;
                    position: relative;
                }}
                .progress {{
                    height: 100%;
                    background-color: #2196F3;
                    border-radius: 5px;
                    width: 0%;
                }}
                .controls button {{
                    background-color: #f0f0f0;
                    border: none;
                    padding: 8px 12px;
                    margin: 4px;
                    border-radius: 5px;
                    cursor: pointer;
                    font-size: 16px;
                }}
                .controls button:hover {{
                    background-color: #ccc;
                }}
            </style>
            <div class="audio-container">
                <audio id="audioPlayer" ontimeupdate="updateProgress()" onloadedmetadata="initProgress()">
                    <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
                    Your browser does not support the audio element.
                </audio>

                <div class="progress-bar">
                    <div class="progress" id="progressBar"></div>
                </div>

                <div class="controls">
                    <button onclick="document.getElementById('audioPlayer').play()">▶️</button>
                    <button onclick="document.getElementById('audioPlayer').pause()">⏸️</button>
                    <button onclick="document.getElementById('audioPlayer').currentTime=0;document.getElementById('audioPlayer').pause()">⏹️</button>
                    <button onclick="document.getElementById('audioPlayer').currentTime=0;document.getElementById('audioPlayer').play()">🔁</button>
                </div>
            </div>

            <script>
                function updateProgress() {{
                    var audio = document.getElementById('audioPlayer');
                    var progress = document.getElementById('progressBar');
                    var value = (audio.currentTime / audio.duration) * 100;
                    progress.style.width = value + '%';
                }}
                function initProgress() {{
                    updateProgress();
                }}
            </script>
            """
            html(player_html, height=230)
        else:
             st.error("Audio generation failed.")