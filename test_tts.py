import requests
import os
import time
import webbrowser

def test_tts_service():
    """Test the TTS service by sending a request and playing the audio"""
    
    # URL of the TTS service
    url = "http://localhost:8000/speak"
    
    # Test text
    text = "Hello, this is a test of the pyttsx3 text to speech service. How does it sound?"
    
    # Send request to TTS service
    print(f"Sending request to {url} with text: '{text}'")
    response = requests.post(url, json={"text": text})
    
    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        print(response.text)
        return
    
    # Get the audio URL
    data = response.json()
    if "error" in data:
        print(f"Error: {data['error']}")
        return
    
    audio_url = data.get("audio_url")
    if not audio_url:
        print("No audio URL returned")
        return
    
    # Full URL to the audio file
    full_audio_url = f"http://localhost:8000{audio_url}"
    print(f"Audio generated successfully: {full_audio_url}")
    
    # Open the audio in the browser
    print("Opening audio in browser...")
    webbrowser.open(full_audio_url)

if __name__ == "__main__":
    test_tts_service()
