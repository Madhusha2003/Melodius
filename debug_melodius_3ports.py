import os
import sys
import time
import subprocess
import atexit
import socket
import json
import ctypes
import threading
import psutil
import webview

# 1. Base Directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Data still persists in AppData
APPDATA_DIR = os.path.join(os.getenv('APPDATA', os.path.expanduser("~")), "Melodius")
os.makedirs(APPDATA_DIR, exist_ok=True)

# 2. Configuration & Paths
CONFIG_FILE = os.path.join(APPDATA_DIR, "config.json")
DATABASE_PATH = os.path.join(APPDATA_DIR, "melodius.db")
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

# Using the embedded Python or VENV if available
PYTHON = os.path.join(BASE_DIR, "python_11", "python.exe")
if not os.path.exists(PYTHON):
    PYTHON = sys.executable

# 3. Process Management
backend_process = None
reflex_dev_process = None

def kill_process_tree(pid: int):
    try:
        parent = psutil.Process(pid)
        for child in parent.children(recursive=True):
            child.terminate()
        parent.terminate()
    except psutil.NoSuchProcess:
        pass

def cleanup():
    print("\nShutting down Melodius Debug...")
    if backend_process: kill_process_tree(backend_process.pid)
    if reflex_dev_process: kill_process_tree(reflex_dev_process.pid)

atexit.register(cleanup)

# 4. Port Management
def is_port_open(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", port)) == 0

def wait_for_server(name: str, port: int, timeout: int = 120):
    print(f"  Waiting for {name} on port {port}...")
    deadline = time.time() + timeout
    while time.time() < deadline:
        if is_port_open(port): return True
        time.sleep(1)
    return False

# 5. Server Launchers
def start_backend(port: int):
    global backend_process
    print(f"Starting FastAPI (port {port})...")
    env = os.environ.copy()
    env["MELODIUS_API_PORT"] = str(port)
    env["DATABASE_URL"] = DATABASE_URL
    
    backend_process = subprocess.Popen(
        [PYTHON, "-m", "uvicorn", "main:app", "--port", str(port), "--host", "127.0.0.1"],
        cwd=os.path.join(BASE_DIR, "backend"),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
    )
    def log_api():
        for line in iter(backend_process.stdout.readline, ''):
            if line: print(f"[FastAPI] {line.strip()}")
    threading.Thread(target=log_api, daemon=True).start()

def start_reflex_dev(ui_port: int, reflex_port: int, api_port: int):
    global reflex_dev_process
    print(f"Starting Reflex DEV (UI={ui_port}, Backend={reflex_port})...")
    env = os.environ.copy()
    env["REFLEX_PORT"] = str(reflex_port)
    env["MELODIUS_UI_PORT"] = str(ui_port)
    env["MELODIUS_API_PORT"] = str(api_port)
    
    reflex_dev_process = subprocess.Popen(
        [PYTHON, "-m", "reflex", "run", "--frontend-port", str(ui_port), "--backend-port", str(reflex_port)],
        cwd=os.path.join(BASE_DIR, "frontend"),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding='utf-8',
        errors='replace',
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
    )
    def log_reflex():
        for line in iter(reflex_dev_process.stdout.readline, ''):
            if line: print(f"[Reflex-Dev] {line.strip()}")
    threading.Thread(target=log_reflex, daemon=True).start()

# 6. Main App
def main():
    # Fixed debug ports to prevent confusion
    UI_PORT = 3000
    REFLEX_PORT = 8001
    API_PORT = 8002
    APP_URL = f"http://127.0.0.1:{UI_PORT}"

    print("--- Melodius DEBUG Launcher ---")
    
    start_backend(API_PORT)
    start_reflex_dev(UI_PORT, REFLEX_PORT, API_PORT)

    if wait_for_server("FastAPI", API_PORT) and wait_for_server("Reflex Backend", REFLEX_PORT) and wait_for_server("Vite Frontend", UI_PORT):
        print(f"Launching window -> {APP_URL}")
        
        # Center the window
        x, y = None, None
        try:
            screens = webview.screens
            if screens:
                primary = screens[0]
                x = (primary.width - 1280) // 2
                y = (primary.height - 800) // 2
        except: pass

        window = webview.create_window(
            "Melodius [DEBUG]",
            APP_URL,
            width=1280,
            height=800,
            min_size=(1280, 800),
            x=x, y=y
        )
        
        webview.start(private_mode=False, debug=True)

if __name__ == "__main__":
    main()