import os
import sys
import time
import subprocess
import atexit
import socket
import json
import ctypes
import threading
import shutil


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# User Data Directory (System-standard location)
APPDATA_DIR = os.path.join(os.getenv('APPDATA', os.path.expanduser("~")), "Melodius")
os.makedirs(APPDATA_DIR, exist_ok=True)

# Shared configuration and database
CONFIG_FILE = os.path.join(APPDATA_DIR, "config.json")
DATABASE_PATH = os.path.join(APPDATA_DIR, "melodius.db")
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

# Python and Reflex paths
PYTHON_PATH = os.path.join(BASE_DIR, "python_11")
PYTHON = os.path.join(PYTHON_PATH, "python.exe")
# Standard Python layout uses Lib/site-packages
SITE_PACKAGES = os.path.join(PYTHON_PATH, "Lib", "site-packages")
if not os.path.exists(SITE_PACKAGES):
    # Fallback for some embedded distributions
    SITE_PACKAGES = os.path.join(PYTHON_PATH, "site-packages")

# ---------------------------------------------------------------------------
# Path Mapping (Ensures Python always finds our code)
# ---------------------------------------------------------------------------
pth_file = os.path.join(SITE_PACKAGES, "melodius_paths.pth")
try:
    with open(pth_file, "w") as f:
        f.write(f"{BASE_DIR}\n")
        f.write(f"{os.path.join(BASE_DIR, 'backend')}\n")
        f.write(f"{os.path.join(BASE_DIR, 'frontend')}\n")
except Exception:
    pass

# Move to AppData immediately for write permissions
os.chdir(APPDATA_DIR)

sys.path.insert(0, SITE_PACKAGES)
sys.path.insert(0, BASE_DIR)

# ---------------------------------------------------------------------------
# Dependency checks
# ---------------------------------------------------------------------------
try:
    import psutil
    import webview
except ImportError as e:
    print(f"Error: Missing dependency ({e}). Run: pip install psutil pywebview")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Configuration & Port Management
# ---------------------------------------------------------------------------
BASE_TRIPLETS = [
    (8000, 8001, 8002),
    (8100, 8101, 8102),
    (8200, 8201, 8202),
    (8300, 8301, 8302),
]
UI_PORT = 8000           # Frontend static hosting
REFLEX_API_PORT = 8001   # Reflex state backend
FASTAPI_PORT = 8002      # FastAPI data backend
APP_URL = f"http://127.0.0.1:{UI_PORT}"

# Process handles for cleanup
backend_process = None
reflex_backend_process = None
static_process = None


def is_free(port: int) -> bool:
    """Return True if port is available."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", port)) != 0


def find_port_triplet():
    """Finds a free triplet of ports, optionally reusing from config."""
    # 1. Try to reuse last working ports
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                config = json.load(f)
                u_p = config.get("ui_port")
                r_p = config.get("reflex_port")
                a_p = config.get("api_port")
                if all(is_free(p) for p in (u_p, r_p, a_p)):
                    print(f"Reusing ports from {CONFIG_FILE}: UI={u_p}, Reflex={r_p}, API={a_p}")
                    return u_p, r_p, a_p
        except Exception:
            pass

    # 2. Fallback to predefined triplets
    for u_p, r_p, a_p in BASE_TRIPLETS:
        if all(is_free(p) for p in (u_p, r_p, a_p)):
            return u_p, r_p, a_p

    raise RuntimeError("No free port triplets available in the 8000-8302 range.")


def save_ports(u_p, r_p, a_p):
    """Saves the chosen ports to config_3ports.json."""
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump({"ui_port": u_p, "reflex_port": r_p, "api_port": a_p}, f)
    except Exception as e:
        print(f"Warning: Could not save {CONFIG_FILE}: {e}")

# ---------------------------------------------------------------------------
# Hardware acceleration (reads user preference from user_data.json)
# ---------------------------------------------------------------------------
def setup_hardware_acceleration():
    # Hardware acceleration preference is stored in the user_data.json in AppData
    data_path = os.path.join(APPDATA_DIR, "user_data.json")
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


def set_win32_icon():
    """Sets the window icon using Win32 API (runs in background)."""
    import time
    icon_path = os.path.join(BASE_DIR, "assets", "melodius_icon_512.ico")
    if not os.path.exists(icon_path):
        return

    # LoadImageW constants
    IMAGE_ICON = 1
    LR_LOADFROMFILE = 0x00000010
    LR_DEFAULTSIZE = 0x00000040
    
    try:
        h_icon = ctypes.windll.user32.LoadImageW(
            None, icon_path, IMAGE_ICON, 0, 0, LR_LOADFROMFILE | LR_DEFAULTSIZE
        )
        if not h_icon:
            return

        # Wait for the window to appear and set its icon
        def find_and_set():
            for _ in range(40): # Try for 20 seconds
                hwnd = ctypes.windll.user32.FindWindowW(None, "Melodius")
                if hwnd:
                    WM_SETICON = 0x0080
                    ICON_SMALL = 0
                    ICON_BIG = 1
                    ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, ICON_SMALL, h_icon)
                    ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, ICON_BIG, h_icon)
                    break
                time.sleep(0.5)
        
        threading.Thread(target=find_and_set, daemon=True).start()
    except Exception:
        pass


def cleanup():
    """Called on exit – tears down all server processes."""
    print("\nShutting down Melodius...")
    if backend_process:
        kill_process_tree(backend_process.pid)
    if reflex_backend_process:
        kill_process_tree(reflex_backend_process.pid)
    if static_process:
        kill_process_tree(static_process.pid)
    print("Cleanup complete.")


atexit.register(cleanup)


def sync_web_assets():
    """Sync static assets from installation to AppData for writable access."""
    src_dir = os.path.join(BASE_DIR, "frontend", ".web", "build", "client")
    dest_dir = os.path.join(APPDATA_DIR, "web_assets")
    
    # Also sync env.json (Reflex uses this to find the backend)
    env_json_src = os.path.join(BASE_DIR, "frontend", ".web", "env.json")
    env_json_dest = os.path.join(dest_dir, "env.json")

    if not os.path.exists(src_dir):
        print(f"Error: Static assets not found at {src_dir}")
        return

    print(f"Syncing web assets to {dest_dir}...")
    try:
        # To avoid stale hashed files from previous builds, we clear the dest
        if os.path.exists(dest_dir):
            shutil.rmtree(dest_dir)
        
        shutil.copytree(src_dir, dest_dir)
        
        # Copy env.json into the static root
        if os.path.exists(env_json_src):
            shutil.copy2(env_json_src, env_json_dest)
            
    except Exception as e:
        print(f"Warning: Web asset sync failed: {e}")


def patch_frontend_ports(reflex_api_port: int):
    """Patch ONLY the environment config files in the writable AppData copy."""
    import re
    web_assets = os.path.join(APPDATA_DIR, "web_assets")
    assets_sub = os.path.join(web_assets, "assets")
    
    target_files = []
    # 1. env.json (now in web_assets root)
    env_json = os.path.join(web_assets, "env.json")
    if os.path.exists(env_json):
        target_files.append(env_json)
        
    # 2. reflex-env-*.js
    if os.path.exists(assets_sub):
        for f in os.listdir(assets_sub):
            if f.startswith("reflex-env-") and f.endswith(".js"):
                target_files.append(os.path.join(assets_sub, f))

    if not target_files:
        print("  No environment files found to patch in AppData.")
        return

    print(f"Patching {len(target_files)} environment config files in AppData...")
    
    # In 3-port mode, the browser only needs to know the Reflex port.
    # Data API calls are handled server-side in api_3.py.
    url_pattern = re.compile(r"(http://|ws://)(127\.0\.0\.1|localhost):(\d+)")
    replacement = r"\g<1>127.0.0.1:" + str(reflex_api_port)
    
    patched_count = 0
    for filepath in target_files:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            
            new_content = url_pattern.sub(replacement, content)
            
            if new_content != content:
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(new_content)
                patched_count += 1
        except Exception:
            pass
    
    if patched_count > 0:
        print(f"  Successfully patched {patched_count} env file(s).")
    else:
        print("  Env files are already up to date.")


# ---------------------------------------------------------------------------
# Server launchers
# ---------------------------------------------------------------------------
def log_streamer(pipe, prefix):
    """Thread function to stream logs from a pipe to the console."""
    try:
        import sys
        for line in iter(pipe.readline, ''):
            if line:
                print(f"[{prefix}] {line.strip()}")
            else:
                break
    except Exception:
        pass
    finally:
        pipe.close()

def start_backend(port: int):
    """Launch the FastAPI backend using a junction."""
    global backend_process
    print(f"Starting FastAPI (port {port})...")
    
    # Create a "Ghost Link" (Junction) named 'backend' in AppData
    backend_src = os.path.join(BASE_DIR, "backend")
    backend_dest = os.path.join(APPDATA_DIR, "backend")
    
    # CLEANUP: Remove old junction if it exists to prevent path conflicts
    if os.path.exists(backend_dest):
        try: subprocess.run(['cmd', '/c', 'rd', '/s', '/q', 'backend'], cwd=APPDATA_DIR, creationflags=subprocess.CREATE_NO_WINDOW)
        except Exception: pass
        
    try:
        subprocess.run(['cmd', '/c', 'mklink', '/J', 'backend', backend_src], 
                        cwd=APPDATA_DIR, check=True, capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
    except Exception as e:
        print(f"Warning: Could not create FastAPI junction: {e}")

    env = os.environ.copy()
    env["MELODIUS_API_PORT"] = str(port)
    env["DATABASE_URL"] = DATABASE_URL
    
    # Run from WITHIN the junctioned backend folder
    backend_process = subprocess.Popen(
        [PYTHON, "-m", "uvicorn", "main:app", "--port", str(port), "--host", "127.0.0.1"],
        cwd=backend_dest,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        encoding='utf-8',
        creationflags=subprocess.CREATE_NO_WINDOW
    )
    import threading
    threading.Thread(target=log_streamer, args=(backend_process.stdout, "FastAPI"), daemon=True).start()


def start_frontend_static(port: int):
    """Launch a simple HTTP server for the static files from AppData."""
    global static_process
    print(f"Starting Static Hosting (port {port})...")
    static_dir = os.path.join(APPDATA_DIR, "web_assets")
    static_process = subprocess.Popen(
        [PYTHON, "-m", "http.server", str(port), "--directory", static_dir],
        cwd=APPDATA_DIR,
        env=os.environ.copy(),
        creationflags=subprocess.CREATE_NO_WINDOW
    )


def start_reflex_backend(port: int, ui_port: int, api_port: int):
    """Launch the Reflex backend using a junction for module resolution."""
    global reflex_backend_process
    print(f"Starting Reflex (port {port})...")
    
    # 1. Sync config to AppData
    src_config = os.path.join(BASE_DIR, "frontend", "rxconfig.py")
    dest_config = os.path.join(APPDATA_DIR, "rxconfig.py")
    try: shutil.copy2(src_config, dest_config)
    except Exception: pass

    # 2. Create a "Ghost Link" (Junction) to the app module in AppData
    app_module_src = os.path.join(BASE_DIR, "frontend", "ui_melodius")
    app_module_dest = os.path.join(APPDATA_DIR, "ui_melodius")
    
    # CLEANUP: Remove old junction if it exists
    if os.path.exists(app_module_dest):
        try: subprocess.run(['cmd', '/c', 'rd', '/s', '/q', 'ui_melodius'], cwd=APPDATA_DIR, creationflags=subprocess.CREATE_NO_WINDOW)
        except Exception: pass
        
    try:
        subprocess.run(['cmd', '/c', 'mklink', '/J', 'ui_melodius', app_module_src], 
                        cwd=APPDATA_DIR, check=True, capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
    except Exception as e:
        print(f"Warning: Could not create Reflex junction: {e}")

    env = os.environ.copy()
    env["REFLEX_PORT"] = str(port)
    env["MELODIUS_UI_PORT"] = str(ui_port)
    env["MELODIUS_API_PORT"] = str(api_port)
    
    reflex_backend_process = subprocess.Popen(
        [PYTHON, "-m", "reflex", "run", "--env", "prod", "--backend-only", "--backend-port", str(port)],
        cwd=APPDATA_DIR,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        encoding='utf-8',
        creationflags=subprocess.CREATE_NO_WINDOW
    )
    import threading
    threading.Thread(target=log_streamer, args=(reflex_backend_process.stdout, "Reflex"), daemon=True).start()


def check_single_instance():
    """Prevent multiple instances using a Windows Mutex."""
    # Using a Global prefix makes it work across sessions (optional)
    mutex_name = "Global\\Melodius_SingleInstance_Mutex"
    
    # CreateMutexW returns a handle to the mutex
    # ERROR_ALREADY_EXISTS = 183
    mutex_handle = ctypes.windll.kernel32.CreateMutexW(None, False, mutex_name)
    last_error = ctypes.windll.kernel32.GetLastError()
    
    if last_error == 183: # ERROR_ALREADY_EXISTS
        # Try to find the existing window and bring it to front
        hwnd = ctypes.windll.user32.FindWindowW(None, "Melodius")
        if hwnd:
            # 9 = SW_RESTORE, 5 = SW_SHOW
            ctypes.windll.user32.ShowWindow(hwnd, 9)
            ctypes.windll.user32.SetForegroundWindow(hwnd)
        sys.exit(0)
    
    return mutex_handle


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main():
    global UI_PORT, REFLEX_API_PORT, FASTAPI_PORT, APP_URL
    # Keep the mutex handle alive for the duration of the process
    _mutex = check_single_instance()
    
    print("--- Melodius Desktop Launcher (3-Port Mode) ---")
    setup_hardware_acceleration()

    # Find and assign ports
    try:
        UI_PORT, REFLEX_API_PORT, FASTAPI_PORT = find_port_triplet()
        APP_URL = f"http://127.0.0.1:{UI_PORT}/?cache_bust={int(time.time())}"
        print(f"Using ports: UI={UI_PORT}, Reflex={REFLEX_API_PORT}, DataAPI={FASTAPI_PORT}")
        save_ports(UI_PORT, REFLEX_API_PORT, FASTAPI_PORT)
    except Exception as e:
        print(f"FATAL ERROR: {e}")
        sys.exit(1)

    # Sync and Patch frontend assets in AppData
    sync_web_assets()
    patch_frontend_ports(REFLEX_API_PORT)

    # Launch servers
    start_backend(FASTAPI_PORT)
    start_reflex_backend(REFLEX_API_PORT, UI_PORT, FASTAPI_PORT)
    start_frontend_static(UI_PORT)

    # Wait for servers to be ready
    backend_ok = wait_for_server("FastAPI Backend", FASTAPI_PORT)
    reflex_ok = wait_for_server("Reflex Backend", REFLEX_API_PORT)
    ui_ok = wait_for_server("Static Hosting", UI_PORT)

    if not all((backend_ok, reflex_ok, ui_ok)):
        print("One or more servers failed to start. Aborting.")
        sys.exit(1)

    # Open the desktop window
    print(f"Launching desktop window -> {APP_URL}")
    
    # --- Windows Taskbar & Icon Fix ---
    try:
        myappid = 'Madhusha.Melodius.1.2.0' # Unique ID for taskbar grouping
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except Exception:
        pass
    # ----------------------------------

    # Center the window on the primary screen
    x, y = None, None
    try:
        screens = webview.screens
        if screens:
            primary = screens[0]
            x = (primary.width - 1280) // 2
            y = (primary.height - 800) // 2
    except Exception:
        pass

    window = webview.create_window(
        "Melodius",
        APP_URL,
        width=1280,
        height=800,
        min_size=(1280, 800),
        x=x,
        y=y
    )

    # Start the icon setter in the background
    set_win32_icon()

    webview.start(
        private_mode=False,
        debug=False,
        user_agent="MelodiusDesktop/1.0",
    )


if __name__ == "__main__":
    main()