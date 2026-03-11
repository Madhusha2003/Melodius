import os
import sys
import time
import subprocess
import atexit

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

def start_backend():
    global backend_process
    print("Starting FastAPI backend (port 8000)...")
    
    venv_python = os.path.join("backend", ".venv_backend", "Scripts", "python.exe")
    if not os.path.exists(venv_python):
        venv_python = "python"
        
    backend_process = subprocess.Popen(
        [venv_python, "-m", "uvicorn", "main:app", "--port", "8001"],
        cwd="backend"
    )

def start_frontend():
    global frontend_process
    print("Starting Reflex frontend (port 3000)...")
    
    venv_reflex = os.path.join("frontend", ".venv_frontend", "Scripts", "reflex.exe")
    if not os.path.exists(venv_reflex):
        venv_reflex = "reflex"
        
    frontend_process = subprocess.Popen(
        [venv_reflex, "run"],
        cwd="frontend"
    )

def main():
    start_backend()
    start_frontend()

    print("Waiting 10 seconds for servers to start...")
    time.sleep(10)

    print("Opening Desktop Window...")
    # Open PyWebView targeting the Reflex app port
    window = webview.create_window('Melodius', 'http://localhost:3000', width=1280, height=800)
    
    # WebView2 (Windows Edge) strictly blocks auto-playing audio contexts which breaks the EQ
    # We pass chromium flags to disable this policy
    webview.start(
        private_mode=False, 
        debug=True,
        # Allow EQ AudioContext to run immediately
        user_agent="MelodiusDesktop/1.0",
    )

if __name__ == "__main__":
    main()

