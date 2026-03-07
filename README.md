# Melodius
Melodius is a modern music player application with a FastAPI backend and a Reflex-based frontend.

## 2026 Feature Roadmap
- **Q1: Core Infrastructure**: Basic FastAPI backend, SQLite database integration, Docker containerization.
- **Q2: AI Vibe Matching**: Implement `VibeVector` similarity search for intelligent playlist generation.
- **Q3: Advanced Audio Processing**: Client-side audio equalizers, volume normalizations, and smooth transitions.
- **Q4: Social & Collaborative**: Shared active sessions and real-time collaborative playlists.


## current state
- **frontend**: 
    - Main page with tracks list and player
    - Equalizer with basic functionality
    - Visualizer with basic functionality

- **backend**: 
    - FastAPI server
    - SQLite database


## Bugs

- Eq automatically cannot initialize when reloaded. (Low priority)
- Visualizer is small windows just to show something. (Low priority)
- Reading / finding songs cannot read metadata. (Medium priority)


## Deployment

- Export Data Command `$env:REFLEX_API_URL="http://127.0.0.1:8000"; reflex export --frontend-only --no-zip`

    ** Note: This command is run in the venv **
- ` pyinstaller --name "Melodius" --windowed --add-data "frontend;frontend" --add-data "backend;backend" --collect-all webview --collect-all reflex --collect-all uvicorn --hidden-import "frontend.frontend" --hidden-import "backend.main" test.py `

- ` pyinstaller --name "Melodius" --windowed --add-data "frontend/.web/build/client;frontend/.web/build/client" --add-data "frontend/rxconfig.py;frontend" --add-data "frontend/frontend;frontend/frontend" --add-data "backend;backend" --exclude-module tkinter --exclude-module numpy --exclude-module pandas --collect-all webview --collect-all reflex --collect-all uvicorn --hidden-import "frontend.frontend" --hidden-import "backend.main" --hidden-import "httpx" --hidden-import "mutagen" test.py `
                                                                                                               

## Test run
- python test.py
- python main_app.py
- python main_desktop.py