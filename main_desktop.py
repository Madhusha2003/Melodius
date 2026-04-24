import os
import sys
import time
import subprocess
import atexit
import socket
import psutil
import json


def wait_for_server(name, port, timeout=30):
    """Wait for a local port to become active."""
    print(f"Waiting for {name} to be ready on port {port}...")
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with socket.socket(socket.socket().family, socket.socket().type) as s:
                s.settimeout(0.5)
                s.connect(("127.0.0.1", port))
                print(f"{name} is ready!")
                return True
        except:
            time.sleep(0.5)
    return False

try:
    import webview
except ImportError:
    print("Error: pywebview is not installed.")
    print("Please install it by running: pip install pywebview")
    sys.exit(1)

try:
    import psutil
except ImportError:
    print("Error: psutil is not installed.")
    print("Please install it by running: pip install psutil")
    sys.exit(1)

backend_process = None
frontend_process = None

def kill_process_tree(pid):
    """Kills a process and all of its children on Windows."""
    try:
        parent = psutil.Process(pid)
        for child in parent.children(recursive=True):
            child.terminate()
        parent.terminate()
    except psutil.NoSuchProcess:
        pass

def cleanup():
    print("Cleaning up Melodius processes...")
    if backend_process:
        kill_process_tree(backend_process.pid)
    if frontend_process:
        kill_process_tree(frontend_process.pid)

atexit.register(cleanup)

# Dynamically set hardware acceleration based on user settings
def setup_hardware_acceleration():
    data_path = os.path.join("frontend", "ui_melodius", "user_data.json")
    hw_accel = True # Default
    if os.path.exists(data_path):
        try:
            with open(data_path, "r") as f:
                data = json.load(f)
                hw_accel = data.get("hardware_acceleration", True)
        except:
            pass
    
    if not hw_accel:
        print("Hardware acceleration is DISABLED (Low GPU mode)")
        os.environ["WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS"] = "--disable-gpu --disable-gpu-compositing --disable-gpu-rasterization --disable-software-rasterizer"
    else:
        print("Hardware acceleration is ENABLED")
        # Ensure any previous disable flags are cleared for this session
        if "WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS" in os.environ:
            del os.environ["WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS"]

setup_hardware_acceleration()

def start_backend():
    global backend_process
    print("Starting FastAPI backend (port 8000)...")

    backend_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--port", "8001"],
        cwd="backend"
    )

def start_frontend():
    global frontend_process
    print("Starting Reflex frontend (port 3000)...")

    frontend_process = subprocess.Popen(
        [sys.executable, "-m", "reflex", "run"],
        cwd="frontend"
    )

def main():
    start_backend()
    start_frontend()

    backend_ok = wait_for_server("Backend", 8001)
    frontend_ok = wait_for_server("Frontend", 3000)

    if not backend_ok or not frontend_ok:
        print("Error: Servers failed to start in time.")
        sys.exit(1)

    print("Opening Desktop Window...")
    # Open PyWebView targeting the Reflex app port
    window = webview.create_window('Melodius', 'http://localhost:3000', width=1280, height=800, min_size=(1280, 800))
    
    # WebView2 (Windows Edge) strictly blocks auto-playing audio contexts which breaks the EQ
    # We pass chromium flags to disable this policy
    webview.start(
        private_mode=False, 
        debug=False,
        # Allow EQ AudioContext to run immediately
        user_agent="MelodiusDesktop/1.0",
    )

if __name__ == "__main__":
    main()

