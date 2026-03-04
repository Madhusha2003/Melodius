import os
import sys
import threading
import time
import uvicorn
import webview
import psutil
import atexit
import subprocess
from fastapi.staticfiles import StaticFiles

# --- 1. ENVIRONMENT & PATHS ---
os.environ["REFLEX_API_URL"] = "http://127.0.0.1:8000"

def get_resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

BASE_DIR = get_resource_path(".")
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
BACKEND_DIR = os.path.join(BASE_DIR, "backend")

# Essential for Reflex to find its config
os.chdir(FRONTEND_DIR)
sys.path.append(FRONTEND_DIR)
sys.path.append(BACKEND_DIR)

audio_backend_process = None

def cleanup():
    print("\n[Melodius] Shutting down...")
    if audio_backend_process:
        try:
            parent = psutil.Process(audio_backend_process.pid)
            for child in parent.children(recursive=True):
                child.kill()
            parent.kill()
        except psutil.NoSuchProcess:
            pass

atexit.register(cleanup)

# --- 2. IMPORT BACKENDS ---
# Import your Reflex State engine
from frontend.frontend import app as reflex_app
from backend.main import app as custom_backend

# --- 3. THE MAGIC MOUNT (NO COMPILING) ---
static_dir = os.path.join(FRONTEND_DIR, ".web", "build", "client")
if not os.path.exists(static_dir):
    print(f"ERROR: No built UI found! Run 'reflex export --frontend-only --no-zip' in {FRONTEND_DIR}")
    sys.exit(1)

# Serve the pre-built UI directly from the Reflex API port
reflex_app._api.mount("/", StaticFiles(directory=static_dir, html=True), name="frontend_ui")

# --- 4. RUNNERS ---
def start_reflex_fast():
    print("[Melodius] Instant Boot: Reflex State Engine + UI (Port 8000)...")
    # Run the raw ASGI app, bypassing the Reflex CLI compiler entirely
    uvicorn.run(reflex_app._api, host="127.0.0.1", port=8000, log_level="warning")

def start_custom_backend():
    global audio_backend_process
    print("[Melodius] Starting Audio Backend (Port 8001)...")
    
    python_exe = os.path.join(BACKEND_DIR, "venv", "Scripts", "python.exe")
    if not os.path.exists(python_exe):
        python_exe = "python"
        
    audio_backend_process = subprocess.Popen(
        [python_exe, "-m", "uvicorn", "main:app", "--port", "8001", "--host", "127.0.0.1"],
        cwd=BACKEND_DIR
    )

def main():
    print("Booting Melodius (Fast Mode)...")
    
    start_custom_backend()
    threading.Thread(target=start_reflex_fast, daemon=True).start()
    
    # We only need 2 seconds now because there is no Javascript compiler running!
    time.sleep(2) 
    
    print("Opening Desktop App window...")
    # Point the window to port 8000, which now serves BOTH the logic and the static HTML
    window = webview.create_window(
        'Melodius', 
        'http://127.0.0.1:8000', 
        width=1280, 
        height=800,
        background_color='#000000'
    )
    
    webview.start(
        user_agent="MelodiusDesktop/1.0",
        private_mode=False
    )

if __name__ == "__main__":
    main()