import os
import requests
import time
import glob
from datetime import datetime

class TTSAgent:
    def __init__(self, comfyui_output_dir, audio_output_dir, comfyui_api_url="http://localhost:8188/prompt"):
        self.COMFYUI_OUTPUT_DIR = os.path.abspath(comfyui_output_dir)
        self.AUDIO_OUTPUT_DIR = os.path.abspath(audio_output_dir)
        self.COMFYUI_API_URL = comfyui_api_url
        os.makedirs(self.AUDIO_OUTPUT_DIR, exist_ok=True)

    def validate_paths(self):
        errors = []

        if os.name == 'nt':
            drives = {os.path.splitdrive(p)[0].upper() for p in [self.COMFYUI_OUTPUT_DIR, self.AUDIO_OUTPUT_DIR]}
            if len(drives) > 1:
                errors.append(f"Paths span multiple drives: {drives}")

        for name, path in [("ComfyUI Output", self.COMFYUI_OUTPUT_DIR), 
                           ("Audio Output", self.AUDIO_OUTPUT_DIR)]:
            if not os.path.exists(path):
                errors.append(f"{name} directory does not exist: {path}")
            elif not os.access(path, os.W_OK):
                errors.append(f"No write permissions for {name} directory: {path}")

        return errors

    def generate_workflow(self, text, speaker, speed, lang):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"tts_output_{timestamp}"
        return {
            "1": {"inputs": {"speaker_name": speaker}, "class_type": "KokoroSpeaker"},
            "2": {
                "inputs": {
                    "text": text, "speed": speed, "lang": lang, "speaker": ["1", 0]
                },
                "class_type": "KokoroGenerator"
            },
            "5": {
                "inputs": {
                    "filename_prefix": filename, "quality": "V0", "audio": ["2", 0]
                },
                "class_type": "SaveAudioMP3"
            }
        }, filename

    def find_generated_file(self, base_filename):
        pattern = os.path.join(self.COMFYUI_OUTPUT_DIR, f"{base_filename}*.mp3")
        files = glob.glob(pattern)
        if not files:
            pattern = os.path.join(self.COMFYUI_OUTPUT_DIR, f"{base_filename}_*.mp3")
            files = glob.glob(pattern)
        return max(files, key=os.path.getmtime) if files else None

    def copy_to_output(self, src_path):
        filename = os.path.basename(src_path)
        dest_path = os.path.join(self.AUDIO_OUTPUT_DIR, filename)
        with open(src_path, "rb") as src, open(dest_path, "wb") as dest:
            dest.write(src.read())
        return dest_path

    def synthesize(self, text, speaker="af_sarah", speed=1.0, lang="English", timeout=120):
        workflow, base_filename = self.generate_workflow(text, speaker, speed, lang)
        response = requests.post(self.COMFYUI_API_URL, json={"prompt": workflow})
        response.raise_for_status()

        start_time = time.time()
        while time.time() - start_time < timeout:
            generated = self.find_generated_file(base_filename)
            if generated:
                return self.copy_to_output(generated)
            time.sleep(1)

        raise TimeoutError(f"Audio generation timed out after {timeout} seconds.")

