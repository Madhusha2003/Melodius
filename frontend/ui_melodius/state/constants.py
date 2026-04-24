import os

# Base directory of the frontend source
FRONTEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Path to the user data JSON file (Moved to AppData for persistence)
APPDATA_DIR = os.path.join(os.getenv('APPDATA', os.path.expanduser("~")), "Melodius")
os.makedirs(APPDATA_DIR, exist_ok=True)
DATA_FILE = os.path.join(APPDATA_DIR, "user_data.json")
