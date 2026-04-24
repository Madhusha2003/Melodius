import os
import sys
import threading
import time
import uvicorn
import webview
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

# Ensure Python can find both folders
sys.path.insert(0, BASE_DIR)
sys.path.append(FRONTEND_DIR)
sys.path.append(BACKEND_DIR)

# --- 2. THE DIRECTORY DANCE ---
# Step A: Go to Frontend so Reflex can read rxconfig.py
os.chdir(FRONTEND_DIR)
from frontend.frontend import app as reflex_app

# Step B: IMMEDIATELY go to Backend so your FastAPI app can find its database and files!
os.chdir(BACKEND_DIR)
from backend.main import app as custom_backend

# --- 3. THE MAGIC MOUNT ---
static_dir = os.path.join(FRONTEND_DIR, ".web", "build", "client")
if not os.path.exists(static_dir):
    print(f"ERROR: No built UI found! Run 'reflex export --frontend-only --no-zip' in {FRONTEND_DIR}")
    sys.exit(1)

# Serve the pre-built UI directly from the Reflex API port
reflex_app._api.mount("/", StaticFiles(directory=static_dir, html=True), name="frontend_ui")

# --- 4. RUNNERS (Thread-Safe Uvicorn) ---
def start_reflex_fast():
    print("[Melodius] Instant Boot: Reflex State Engine + UI (Port 8000)...")
    # Using uvicorn.Config and Server prevents signal handler crashes in threads
    config = uvicorn.Config(reflex_app._api, host="127.0.0.1", port=8000, log_level="warning")
    server = uvicorn.Server(config)
    server.run()

def start_custom_backend():
    print("[Melodius] Starting Audio Backend (Port 8001)...")
    config = uvicorn.Config(custom_backend, host="127.0.0.1", port=8001, log_level="warning")
    server = uvicorn.Server(config)
    server.run()

def main():
    print("Booting Melodius (Fast Mode)...")
    
    # Start both threads
    threading.Thread(target=start_custom_backend, daemon=True).start()
    threading.Thread(target=start_reflex_fast, daemon=True).start()
    
    # Wait for the servers to bind
    time.sleep(2) 
    
    print("Opening Desktop App window...")
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