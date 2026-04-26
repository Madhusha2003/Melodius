import os
import subprocess

# 1. Base Directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Use a local debug_data folder for development
APPDATA_DIR = os.path.join(BASE_DIR, "debug_data")
os.makedirs(APPDATA_DIR, exist_ok=True)

# 2. Configuration
DATABASE_PATH = os.path.join(APPDATA_DIR, "melodius.db")
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

# Using the embedded Python
PYTHON = os.path.join(BASE_DIR, "python_11", "python.exe")
if not os.path.exists(PYTHON):
    # Fallback to current sys.executable if embedded python_11 is missing
    PYTHON = sys.executable

# 3. Ports
UI_PORT = 3000
REFLEX_PORT = 8000
API_PORT = 8002

def kill_port_owners():
    """Kills any processes using our target ports to prevent port-jumping (e.g. 3000 -> 3001)."""
    try:
        import psutil
        target_ports = [UI_PORT, REFLEX_PORT, API_PORT]
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                for conn in proc.connections(kind='inet'):
                    if conn.laddr.port in target_ports:
                        print(f"  Cleaning up old process {proc.name()} (PID: {proc.pid}) on port {conn.laddr.port}...")
                        proc.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
    except ImportError:
        pass

def start_terminals():
    print("--- Launching Melodius Dev Terminals ---")
    kill_port_owners()
    
    # Environment Setup and Command for FastAPI
    fastapi_cmd = (
        f'set "MELODIUS_API_PORT={API_PORT}" && '
        f'set "DATABASE_URL={DATABASE_URL}" && '
        f'"{PYTHON}" -m uvicorn main:app --port {API_PORT} --host 127.0.0.1'
    )
    
    # Environment Setup and Command for Reflex
    reflex_cmd = (
        f'set "REFLEX_PORT={REFLEX_PORT}" && '
        f'set "MELODIUS_UI_PORT={UI_PORT}" && '
        f'set "MELODIUS_API_PORT={API_PORT}" && '
        f'"{PYTHON}" -m reflex run --frontend-port {UI_PORT} --backend-port {REFLEX_PORT}'
    )

    # Launch FastAPI in a new window
    print("Opening FastAPI Terminal...")
    subprocess.Popen(
        f'start cmd /k "title Melodius-FastAPI && cd /d {os.path.join(BASE_DIR, "backend")} && {fastapi_cmd}"', 
        shell=True
    )

    # Launch Reflex in a new window
    print("Opening Reflex Terminal...")
    subprocess.Popen(
        f'start cmd /k "title Melodius-Reflex && cd /d {os.path.join(BASE_DIR, "frontend")} && {reflex_cmd}"', 
        shell=True
    )

    print("\nWindows launched! Check your taskbar for two new terminal windows.")
    print(f"Browser URL: http://localhost:{UI_PORT}")

if __name__ == "__main__":
    import sys
    start_terminals()
