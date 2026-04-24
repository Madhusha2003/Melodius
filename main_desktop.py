import os
import sys
import time
import subprocess
import atexit
import socket
import json

# ---------------------------------------------------------------------------
# Dependency checks (fail fast with clear messages)
# ---------------------------------------------------------------------------
try:
    import psutil
except ImportError:
    print("Error: psutil is not installed.  Run:  pip install psutil")
    sys.exit(1)

try:
    import webview
except ImportError:
    print("Error: pywebview is not installed.  Run:  pip install pywebview")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Configuration & Port Management
# ---------------------------------------------------------------------------
BASE_PAIRS = [
    (8000, 8001),
    (8100, 8101),
    (8200, 8201),
    (8300, 8301),
]

CONFIG_FILE = "config.json"

# These will be set dynamically in main()
REFLEX_PORT = 8000
FASTAPI_PORT = 8001
APP_URL = f"http://127.0.0.1:{REFLEX_PORT}"

# Process handles for cleanup
backend_process = None
frontend_process = None


def is_free(port: int) -> bool:
    """Return True if port is available."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", port)) != 0


def find_port_pair():
    """Finds a free pair of ports, optionally reusing from config."""
    # 1. Try to reuse last working ports
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                config = json.load(f)
                ui_p = config.get("ui_port")
                api_p = config.get("api_port")
                if ui_p and api_p and is_free(ui_p) and is_free(api_p):
                    print(f"Reusing ports from {CONFIG_FILE}: UI={ui_p}, API={api_p}")
                    return ui_p, api_p
        except Exception:
            pass

    # 2. Fallback to predefined pairs
    for ui_p, api_p in BASE_PAIRS:
        if is_free(ui_p) and is_free(api_p):
            return ui_p, api_p

    raise RuntimeError("No free port pairs available in the 8000-8301 range.")


def save_ports(ui_p, api_p):
    """Saves the chosen ports to config.json."""
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump({"ui_port": ui_p, "api_port": api_p}, f)
    except Exception as e:
        print(f"Warning: Could not save {CONFIG_FILE}: {e}")

# ---------------------------------------------------------------------------
# Hardware acceleration (reads user preference from user_data.json)
# ---------------------------------------------------------------------------
def setup_hardware_acceleration():
    data_path = os.path.join("frontend", "ui_melodius", "user_data.json")
    hw_accel = True  # Default: enabled
    if os.path.exists(data_path):
        try:
            with open(data_path, "r") as f:
                data = json.load(f)
                hw_accel = data.get("hardware_acceleration", True)
        except Exception:
            pass

    if not hw_accel:
        print("Hardware acceleration: DISABLED (Low-GPU mode)")
        os.environ["WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS"] = (
            "--disable-gpu --disable-gpu-compositing "
            "--disable-gpu-rasterization --disable-software-rasterizer"
        )
    else:
        print("Hardware acceleration: ENABLED")
        os.environ.pop("WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS", None)


# ---------------------------------------------------------------------------
# Port helpers
# ---------------------------------------------------------------------------
def is_port_open(port: int) -> bool:
    """Return True if something is already listening on *port*."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", port)) == 0


def wait_for_server(name: str, port: int, timeout: int = 120) -> bool:
    """Block until *port* accepts connections or *timeout* seconds pass."""
    print(f"  Waiting for {name} on port {port} (timeout {timeout}s)...")
    deadline = time.time() + timeout
    while time.time() < deadline:
        if is_port_open(port):
            print(f"  {name} is ready!")
            return True
        time.sleep(0.5)
    print(f"  ERROR: {name} did not start within {timeout}s.")
    return False


# ---------------------------------------------------------------------------
# Process management
# ---------------------------------------------------------------------------
def kill_process_tree(pid: int):
    """Terminate a process and all its children (Windows-safe)."""
    try:
        parent = psutil.Process(pid)
        for child in parent.children(recursive=True):
            child.terminate()
        parent.terminate()
    except psutil.NoSuchProcess:
        pass


def cleanup():
    """Called on exit – tears down both server processes."""
    print("\nShutting down Melodius...")
    if backend_process:
        kill_process_tree(backend_process.pid)
    if frontend_process:
        kill_process_tree(frontend_process.pid)
    print("Cleanup complete.")


atexit.register(cleanup)


# ---------------------------------------------------------------------------
# Server launchers
# ---------------------------------------------------------------------------
def start_backend(port: int):
    """Launch the FastAPI / Uvicorn backend on port."""
    global backend_process
    print(f"Starting FastAPI backend (port {port})...")
    
    # Ensure environment is passed
    env = os.environ.copy()
    
    backend_process = subprocess.Popen(
        [
            sys.executable, "-m", "uvicorn",
            "main:app",
            "--host", "127.0.0.1",
            "--port", str(port),
        ],
        cwd="backend",
        env=env,
    )


def start_frontend(ui_port: int, api_port: int):
    """Launch the Reflex app in production single-port mode."""
    global frontend_process
    print(f"Starting Reflex app (single-port: {ui_port})...")
    
    # Pass ports to Reflex via environment variables
    env = os.environ.copy()
    env["REFLEX_PORT"] = str(ui_port)
    env["MELODIUS_API_PORT"] = str(api_port)
    
    frontend_process = subprocess.Popen(
        [
            sys.executable, "-m", "reflex", "run",
            "--env", "prod",
            "--single-port",
            "--backend-port", str(ui_port),
        ],
        cwd="frontend",
        env=env,
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main():
    global REFLEX_PORT, FASTAPI_PORT, APP_URL
    print("--- Melodius Desktop Launcher ---")
    setup_hardware_acceleration()

    # Find and assign ports
    try:
        REFLEX_PORT, FASTAPI_PORT = find_port_pair()
        APP_URL = f"http://127.0.0.1:{REFLEX_PORT}"
        print(f"Using ports: UI={REFLEX_PORT}, API={FASTAPI_PORT}")
        save_ports(REFLEX_PORT, FASTAPI_PORT)
    except Exception as e:
        print(f"FATAL ERROR: {e}")
        sys.exit(1)

    # Launch servers
    start_backend(FASTAPI_PORT)
    start_frontend(REFLEX_PORT, FASTAPI_PORT)

    # Wait for both to be ready
    backend_ok = wait_for_server("FastAPI Backend", FASTAPI_PORT)
    frontend_ok = wait_for_server("Reflex App", REFLEX_PORT)

    if not backend_ok or not frontend_ok:
        print("One or more servers failed to start. Aborting.")
        sys.exit(1)

    # Open the desktop window
    print(f"Launching desktop window -> {APP_URL}")
    webview.create_window(
        "Melodius",
        APP_URL,
        width=1280,
        height=800,
        min_size=(1280, 800),
    )
    webview.start(
        private_mode=False,
        debug=False,
        user_agent="MelodiusDesktop/1.0",
    )


if __name__ == "__main__":
    main()