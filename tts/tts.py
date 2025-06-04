import streamlit as st
import os
import requests
import base64
from datetime import datetime
import time
import glob

# Configuration - MUST USE ABSOLUTE PATHS
# Declare as globals first
global COMFYUI_OUTPUT_DIR, AUDIO_OUTPUT_DIR
COMFYUI_API_URL = "http://localhost:8188/prompt"
COMFYUI_OUTPUT_DIR = "E:\ComfyUI_windows_portable\ComfyUI\output"  # MUST match ComfyUI's output directory
AUDIO_OUTPUT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "audio_output"))

# Ensure directories exist
os.makedirs(AUDIO_OUTPUT_DIR, exist_ok=True)

# Set page config
st.set_page_config(page_title="Kokoro TTS Generator", layout="wide")
st.title("Kokoro Text-to-Speech Generator")

def validate_paths():
    """Ensure all paths are on the same drive and properly formatted."""
    global COMFYUI_OUTPUT_DIR, AUDIO_OUTPUT_DIR  # Declare as globals
    
    errors = []
    
    # Convert all paths to absolute and normalized
    COMFYUI_OUTPUT_DIR = os.path.abspath(COMFYUI_OUTPUT_DIR)
    AUDIO_OUTPUT_DIR = os.path.abspath(AUDIO_OUTPUT_DIR)
    
    # Check if paths are on same drive (Windows only)
    if os.name == 'nt':
        drives = {os.path.splitdrive(p)[0].upper() for p in [COMFYUI_OUTPUT_DIR, AUDIO_OUTPUT_DIR] if p}
        if len(drives) > 1:
            errors.append(f"Paths span multiple drives: {drives}. All paths must be on the same drive.")
    
    # Verify directories exist
    for name, path in [("ComfyUI Output", COMFYUI_OUTPUT_DIR), 
                      ("Audio Output", AUDIO_OUTPUT_DIR)]:
        if not os.path.exists(path):
            errors.append(f"{name} directory does not exist: {path}")
        elif not os.access(path, os.W_OK):
            errors.append(f"No write permissions for {name} directory: {path}")
    
    return errors

def generate_workflow(text, speaker, speed, lang):
    """Generate workflow that saves directly to ComfyUI's output directory."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"tts_output_{timestamp}"
    
    return {
        "1": {
            "inputs": {"speaker_name": speaker},
            "class_type": "KokoroSpeaker"
        },
        "2": {
            "inputs": {
                "text": text,
                "speed": speed,
                "lang": lang,
                "speaker": ["1", 0]
            },
            "class_type": "KokoroGenerator"
        },
        "5": {
            "inputs": {
                "filename_prefix": filename,  # Relative to ComfyUI's output dir
                "quality": "V0",
                "audio": ["2", 0]
            },
            "class_type": "SaveAudioMP3"
        }
    }, filename

def find_generated_file(base_filename):
    """Find the generated file in ComfyUI's output directory."""
    pattern = os.path.join(COMFYUI_OUTPUT_DIR, f"{base_filename}*.mp3")
    files = glob.glob(pattern)
    
    if not files:
        # Check with counter suffix (ComfyUI adds _00001, _00002, etc.)
        pattern = os.path.join(COMFYUI_OUTPUT_DIR, f"{base_filename}_*.mp3")
        files = glob.glob(pattern)
    
    if files:
        # Get most recently modified file
        return max(files, key=os.path.getmtime)
    return None

def copy_to_final_location(src_path, dest_dir):
    """Copy file to our final output directory."""
    filename = os.path.basename(src_path)
    dest_path = os.path.join(dest_dir, filename)
    
    try:
        with open(src_path, "rb") as src, open(dest_path, "wb") as dest:
            dest.write(src.read())
        return dest_path
    except Exception as e:
        st.error(f"Failed to copy file: {str(e)}")
        return None

# Validate paths at startup
path_errors = validate_paths()
if path_errors:
    st.error("Configuration Errors:")
    for error in path_errors:
        st.error(error)
    st.stop()

# Main form
with st.form("tts_form"):
    text = st.text_area("Text to synthesize", "I am a synthesized robot", height=100)
    speaker = st.selectbox("Speaker", ["af_sarah", "af_emma", "af_liam", "af_olivia"])
    speed = st.slider("Speed", 0.5, 2.0, 1.0, 0.1)
    lang = st.selectbox("Language", ["English", "Japanese", "Spanish", "French", "German"])
    
    if st.form_submit_button("Generate Speech"):
        if not text.strip():
            st.warning("Please enter text to synthesize")
        else:
            workflow, base_filename = generate_workflow(text, speaker, speed, lang)
            
            with st.expander("Workflow Details"):
                st.json(workflow)
                st.info(f"Files will be saved with prefix: {base_filename}")
                st.info(f"ComfyUI Output Directory: {COMFYUI_OUTPUT_DIR}")
                st.info(f"Final Output Directory: {AUDIO_OUTPUT_DIR}")
            
            try:
                # Submit to ComfyUI
                response = requests.post(COMFYUI_API_URL, json={"prompt": workflow})
                response.raise_for_status()
                prompt_id = response.json()["prompt_id"]
                
                # Monitor for completion
                st.info(f"Processing with prompt ID: {prompt_id}")
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                start_time = time.time()
                timeout = 120  # seconds
                success = False
                
                while time.time() - start_time < timeout:
                    # Check for file generation
                    generated_path = find_generated_file(base_filename)
                    if generated_path:
                        success = True
                        break
                    
                    # Update progress
                    elapsed = time.time() - start_time
                    progress = min(elapsed / timeout, 1.0)
                    progress_bar.progress(progress)
                    status_text.text(f"Status: Processing ({elapsed:.1f}s)")
                    time.sleep(1)
                
                progress_bar.empty()
                
                if success:
                    # Copy to our final location
                    final_path = copy_to_final_location(generated_path, AUDIO_OUTPUT_DIR)
                    
                    if final_path:
                        st.success(f"Audio generated successfully!")
                        
                        # Display audio
                        with open(final_path, "rb") as f:
                            audio_bytes = f.read()
                        st.audio(audio_bytes, format="audio/mp3")
                        
                        # Download link
                        b64 = base64.b64encode(audio_bytes).decode()
                        filename = os.path.basename(final_path)
                        href = f'<a href="data:file/mp3;base64,{b64}" download="{filename}">Download MP3</a>'
                        st.markdown(href, unsafe_allow_html=True)
                    else:
                        st.error("Failed to move generated file to final location")
                else:
                    st.error("Audio generation timed out")
                    st.info(f"Checked for files matching: {os.path.join(COMFYUI_OUTPUT_DIR, base_filename)}*.mp3")
                    
            except Exception as e:
                st.error(f"Generation failed: {str(e)}")

# Debug information
with st.expander("Debug Information"):
    st.subheader("Directory Contents")
    
    col1, col2 = st.columns(2)
    with col1:
        st.write("ComfyUI Output Directory:")
        try:
            st.write(os.listdir(COMFYUI_OUTPUT_DIR))
        except Exception as e:
            st.error(str(e))
    
    with col2:
        st.write("Audio Output Directory:")
        try:
            st.write(os.listdir(AUDIO_OUTPUT_DIR))
        except Exception as e:
            st.error(str(e))
    
    st.subheader("System Information")
    st.write(f"Current working directory: {os.getcwd()}")
    st.write(f"Python version: {os.sys.version}")