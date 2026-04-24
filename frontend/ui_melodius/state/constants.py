import os

# Base directory of the frontend source
FRONTEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Path to the user data JSON file
DATA_FILE = os.path.join(FRONTEND_DIR, "user_data.json")
