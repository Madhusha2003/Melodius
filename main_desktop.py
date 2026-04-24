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
# Configuration
# ---------------------------------------------------------------------------
# In production Reflex serves frontend + state backend on one port
REFLEX_PORT = 8000   # Reflex single-port (frontend + state backend)
FASTAPI_PORT = 8001  # Your FastAPI data backend

APP_URL = f"http://127.0.0.1:{REFLEX_PORT}"

# Process handles for cleanup
backend_process = None
frontend_process = None

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
def start_backend():
    """Launch the FastAPI / Uvicorn backend on FASTAPI_PORT."""
    global backend_process
    print(f"Starting FastAPI backend (port {FASTAPI_PORT})...")
    backend_process = subprocess.Popen(
        [
            sys.executable, "-m", "uvicorn",
            "main:app",
            "--host", "127.0.0.1",
            "--port", str(FASTAPI_PORT),
        ],
        cwd="backend",
    )


def start_frontend():
    """Launch the Reflex app in production single-port mode."""
    global frontend_process
    print(f"Starting Reflex app (single-port: {REFLEX_PORT})...")
    frontend_process = subprocess.Popen(
        [
            sys.executable, "-m", "reflex", "run",
            "--env", "prod",
            "--single-port",
            "--backend-port", str(REFLEX_PORT),
        ],
        cwd="frontend",
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main():
    print("--- Melodius Desktop Launcher ---")
    setup_hardware_acceleration()

    # Guard against port collisions
    busy_ports = [
        p for p in (REFLEX_PORT, FASTAPI_PORT)
        if is_port_open(p)
    ]
    if busy_ports:
        print(f"ERROR: Port(s) already in use: {busy_ports}")
        print("Close the conflicting applications and try again.")
        sys.exit(1)

    # Launch servers
    start_backend()
    start_frontend()

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