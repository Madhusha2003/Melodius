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
