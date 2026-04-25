<div align="center">

<img src="assets/melodius_icon_512.png" alt="Melodius Logo" width="120"/>

# 🎵 Melodius

**A Modern Desktop Music Player for Windows**

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python 3.11](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Reflex](https://img.shields.io/badge/Reflex-6C3BF5?logo=reflex&logoColor=white)](https://reflex.dev)

Melodius is a high-performance, beautifully designed music player built with a modern web-native architecture. It combines the power of **FastAPI**, **Reflex**, and **pywebview** to deliver a seamless desktop experience with a stunning reactive UI.

---

[Features](#-features) • [Installation](#-installation) • [Architecture](#-architecture) • [Development](#-development) • [Roadmap](#-roadmap) • [License](#-license)

</div>

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🎧 **Modern Player** | Full-featured music player with track list, playback controls, and metadata display |
| 🎛️ **Audio Equalizer** | Built-in equalizer with customizable frequency bands |
| 🖥️ **Native Desktop** | Runs as a native Windows application via pywebview — no browser required |
| ⚡ **Dynamic Ports** | Smart 3-port architecture that auto-detects free ports to avoid conflicts |
| 🔒 **Single Instance** | Prevents duplicate launches — brings existing window to front instead |
| 📦 **Portable Engine** | Ships with an embedded Python runtime — zero dependencies for end users |
| 🎨 **Reactive UI** | Built with Reflex for a fast, responsive, and beautiful interface |
| 💾 **SQLite Database** | Lightweight, file-based database for managing your music library |

---

## 📥 Installation

### For Users

1. Download the latest **`Melodius_Setup.exe`** from the [Releases](https://github.com/Madhusha2003/Melodius/releases) page.
2. Run the installer — it will:
   - Install Melodius to `Program Files`
   - Create Desktop and Start Menu shortcuts
   - Optionally install the **Microsoft Edge WebView2 Runtime** if not already present
3. Launch Melodius from the Desktop shortcut.

### System Requirements

| Requirement | Minimum |
|------------|---------|
| **OS** | Windows 10 (64-bit) or later |
| **RAM** | 4 GB |
| **Disk** | ~200 MB |
| **Runtime** | Microsoft Edge WebView2 *(auto-installed)* |

---

## 🏗️ Architecture

Melodius uses a **3-port architecture** to cleanly separate concerns:

```
┌─────────────────────────────────────────────────────────┐
│                    Melodius.exe                          │
│                  (PyInstaller Launcher)                  │
│                         │                               │
│            ┌────────────┼────────────┐                  │
│            ▼            ▼            ▼                  │
│     ┌────────────┐ ┌─────────┐ ┌──────────┐            │
│     │  Static    │ │ Reflex  │ │ FastAPI  │            │
│     │  Server    │ │ Backend │ │ Backend  │            │
│     │ (Port A)   │ │(Port B) │ │(Port C)  │            │
│     │            │ │         │ │          │            │
│     │ HTML/CSS/JS│ │  State  │ │  REST    │            │
│     │  Assets    │ │  Mgmt   │ │  API     │            │
│     └────────────┘ └─────────┘ └──────────┘            │
│            │            │            │                  │
│            └────────────┼────────────┘                  │
│                         ▼                               │
│                   ┌──────────┐                          │
│                   │ SQLite   │                          │
│                   │ Database │                          │
│                   └──────────┘                          │
│                  (%APPDATA%/Melodius)                    │
└─────────────────────────────────────────────────────────┘
```

| Component | Role | Default Port |
|-----------|------|-------------|
| **Static Server** | Serves pre-compiled frontend assets (HTML, CSS, JS) | `8000` |
| **Reflex Backend** | Manages reactive UI state and WebSocket connections | `8001` |
| **FastAPI Backend** | REST API for music library, file scanning, and metadata | `8002` |

> Ports are dynamically assigned at startup. If the defaults are busy, Melodius automatically selects the next available triplet (8100→8102, 8200→8202, etc.)

---

## 🛠️ Development

### Prerequisites

- **Python 3.11+**
- **Node.js 18+** *(for Reflex frontend compilation)*
- **Git**

### Setup

```bash
# Clone the repository
git clone https://github.com/Madhusha2003/Melodius.git
cd Melodius

# Create and activate a virtual environment
python -m venv venv
venv\Scripts\Activate.ps1    # PowerShell
# or
venv\Scripts\activate.bat    # CMD

# Install dependencies
pip install -r requirements.txt
```

### Running in Development

```bash
# Run the desktop application
python melodius_3ports.py
```

### Building the Installer

1. **Export the frontend** (one-time, or after UI changes):
   ```powershell
   $env:REFLEX_API_URL="http://127.0.0.1:8000"
   reflex export --frontend-only --no-zip
   ```

2. **Build the launcher executable**:
   ```powershell
   .\create_launcher.ps1
   ```

3. **Compile the installer** using [Inno Setup](https://jrsoftware.org/isinfo.php):
   - Open `melodius_installer.iss` in Inno Setup Compiler
   - Press **Ctrl+F9** to compile
   - The output will be at `dist/Melodius_Setup.exe`

> **Note:** You must create an `app_id.iss` file (see `app_id.iss.example`) before compiling the installer.

### Project Structure

```
Melodius/
├── melodius_3ports.py       # Main launcher (3-port orchestrator)
├── melodius_installer.iss   # Inno Setup installer script
├── Melodius.exe             # Compiled launcher executable
├── create_launcher.ps1      # Build script for launcher
├── app_id.iss               # Application GUID (git-ignored)
├── app_id.iss.example       # Template for app_id.iss
│
├── backend/                 # FastAPI REST API
│   └── main.py              # API entry point
│
├── frontend/                # Reflex application
│   ├── ui_melodius/         # Reflex components & state
│   ├── rxconfig.py          # Reflex configuration
│   └── .web/build/client/   # Compiled frontend assets
│
├── assets/                  # Branding (icons, images)
├── python_11/               # Embedded Python runtime
├── tools/                   # Build tools (WebView2 bootstrapper)
│
├── requirements.txt
├── LICENSE.txt               # GNU GPLv3
└── README.md
```

---

## 🗺️ Roadmap

### Current Focus — Audio Experience

| Status | Feature | Details |
|--------|---------|--------|
| ✅ | **Core Infrastructure** | FastAPI backend, SQLite integration, Desktop packaging |
| ✅ | **Audio Equalizer** | Built-in 8-band EQ |
| 🔄 | **Audio Enhancements** | Volume normalization, crossfade transitions, gapless playback |
| 🔄 | **Advanced EQ** | More bands eq , visualizer integration |

### Future Ideas

| Idea | Description |
|------|-------------|
| 🤖 **AI Vibe Matching** | `VibeVector` similarity search for intelligent, mood-based playlist generation |
| 👥 **Social & Collaborative** | Shared listening sessions and real-time collaborative playlists |
| 🌐 **Online Platform** | Cloud sync, cross-device library access, and a web-based companion player |

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the **GNU General Public License v3.0** — see the [LICENSE.txt](LICENSE.txt) file for details.

```
Melodius Desktop Music Player
Copyright (C) 2026 Madhusha Nirmal

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
```

---

<div align="center">

**Made with ❤️ by [Madhusha Nirmal](https://github.com/Madhusha2003)**

</div>