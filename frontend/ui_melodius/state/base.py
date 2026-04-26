import reflex as rx
from ..services.api import Track, MelodiusAPI
import json
import os
import random
import asyncio

from .constants import DATA_FILE

class State(rx.State):
    """The main state for the Melodius application."""
    tracks: list[Track] = []
    search_query: str = ""
    show_settings: bool = False
    is_loading: bool = True
    is_mounting: bool = False
    
    # Settings
    library_directory: str = ""
    hardware_acceleration: bool = True
    experimental_eq: bool = False
    
    # Persistent Data
    last_played_track: dict = {}
    last_played_time: float = 0.0
    
    current_track: Track = Track(id=0, title="", artist="", url="", duration=0.0)
    is_playing: bool = False
    is_shuffled: bool = False
    
    # Audio State
    current_time: float = 0.0
    duration: float = 0.0
    volume: float = 1.0
    is_dragging: bool = False
    
    _timer_running: bool = False

    @rx.var
    def filtered_tracks(self) -> list[Track]:
        if not self.search_query:
            return self.tracks
        query = self.search_query.lower()
        return [
            track for track in self.tracks
            if query in track.title.lower() or query in track.artist.lower()
        ]

    def set_search_query(self, value: str):
        """Explicit setter for search_query (replaces auto_setter)."""
        self.search_query = value

    def set_library_directory(self, value: str):
        """Explicit setter for library_directory (replaces auto_setter)."""
        self.library_directory = value
        self.save_data()

    def toggle_settings(self):
        self.show_settings = not self.show_settings

    def toggle_hardware_acceleration(self, value: bool):
        self.hardware_acceleration = value
        self.save_data()

    def toggle_experimental_eq(self, value: bool):
        self.experimental_eq = value
        self.save_data()
        # Reset EQ initialized flags to force re-init when switching
        from ..components.equalizer.equalizer import EqualizerState
        from ..components.equalizer.equalizer_lab import EqualizerState as LabEqualizerState
        return [EqualizerState.reload_eq(), LabEqualizerState.reload_eq()]

    def clear_player_state(self):
        """Resets the active player state."""
        self.current_track = Track(id=0, title="", artist="", url="", duration=0.0)
        self.last_played_track = {}
        self.is_playing = False
        self.current_time = 0.0
        self.save_data()

    def save_data(self):
        """Saves current state to JSON."""
        data = {}
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r") as f:
                    data = json.load(f)
            except:
                pass
                
        data["last_played_track"] = self.last_played_track
        data["last_played_time"] = self.last_played_time
        data["is_shuffled"] = self.is_shuffled
        data["volume"] = self.volume
        data["library_directory"] = self.library_directory
        data["hardware_acceleration"] = self.hardware_acceleration
        data["experimental_eq"] = self.experimental_eq
        
        with open(DATA_FILE, "w") as f:
            json.dump(data, f, indent=4)

    def on_load(self):
        """Restore previous session data."""
        self.is_playing = False
        self._timer_running = False
        
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r") as f:
                    data = json.load(f)
                    self.last_played_track = data.get("last_played_track", {})
                    self.last_played_time = float(data.get("last_played_time", 0.0))
                    self.is_shuffled = bool(data.get("is_shuffled", False))
                    self.volume = float(data.get("volume", 1.0))
                    self.library_directory = data.get("library_directory", "")
                    self.hardware_acceleration = bool(data.get("hardware_acceleration", True))
                    self.experimental_eq = bool(data.get("experimental_eq", False))
            except Exception as e:
                # Use console.error for client-side debugging if needed, 
                # or just handle it silently as we do here.
                pass
        
        if self.last_played_track and self.last_played_track.get("title"):
            self.current_track = Track(**self.last_played_track)
            self.duration = float(self.current_track.duration)
            self.current_time = float(self.last_played_time)
            return [State.fetch_tracks, State.find_player_by_url, State.finish_loading]
        else:
            self.current_time = 0.0
            return [State.fetch_tracks, State.finish_loading]

    async def finish_loading(self):
        await asyncio.sleep(1.5) # Artificial delay for splash effect
        self.is_loading = False
        self.is_mounting = True

    async def fetch_tracks(self):
        try:
            tracks_data = await MelodiusAPI.get_tracks()
            self.tracks = [Track(**track) for track in tracks_data]
        except Exception as e:
            return rx.toast(f"Error fetching tracks: {str(e)}")

    async def scan_music(self):
        try:
            yield rx.toast("Scanning library...")
            await MelodiusAPI.scan_music(directory=self.library_directory)
            await self.fetch_tracks()
            yield rx.toast("Library scan complete!")
        except Exception as e:
            yield rx.toast(f"Scan failed: {str(e)}")

    @rx.event(background=True)
    async def select_library_directory(self):
        """Open a native folder selection dialog and reset DB on change."""
        import os
        directory = self._open_native_folder_dialog()
        
        if directory:
            async with self:
                # Normalize path for the OS
                directory = os.path.abspath(directory)
                self.library_directory = directory
                self.save_data()
            
            # 1. Reset Database
            yield rx.toast("Resetting database for new folder...")
            await MelodiusAPI.clear_library()
            async with self:
                self.clear_player_state()
            
            # 2. Re-scan
            async for event in self.scan_music():
                yield event

            yield rx.toast(f"Library updated and reset to: {directory}")

    @staticmethod
    def _open_native_folder_dialog() -> str:
        """Open a native Windows folder picker using COM shell dialog.
        
        Falls back to tkinter if available (dev environment), and to a 
        PowerShell picker as a last resort. Returns the selected path 
        or an empty string if cancelled.
        """
        import sys

        if sys.platform == "win32":
            try:
                return State._win32_folder_dialog()
            except Exception:
                pass

        # Fallback: try tkinter (available in full Python installs)
        try:
            import tkinter as tk
            from tkinter import filedialog
            root = tk.Tk()
            root.withdraw()
            root.attributes('-topmost', True)
            directory = filedialog.askdirectory(title="Select Music Folder")
            root.destroy()
            return directory or ""
        except ImportError:
            pass

        return ""

    @staticmethod
    def _win32_folder_dialog() -> str:
        """Use the Windows Shell COM IFileDialog for a modern folder picker."""
        import ctypes
        import ctypes.wintypes
        import subprocess

        # --- Try the modern IFileDialog via PowerShell (clean & reliable) ---
        # This gives us the nice modern folder picker without COM boilerplate.
        ps_script = (
            'Add-Type -AssemblyName System.Windows.Forms; '
            '$f = New-Object System.Windows.Forms.FolderBrowserDialog; '
            '$f.Description = "Select Music Folder"; '
            '$f.ShowNewFolderButton = $true; '
            '$topForm = New-Object System.Windows.Forms.Form; '
            '$topForm.TopMost = $true; '
            'if ($f.ShowDialog($topForm) -eq "OK") { $f.SelectedPath } '
            'else { "" }'
        )

        try:
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps_script],
                capture_output=True,
                text=True,
                timeout=120,  # generous timeout for user interaction
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            path = result.stdout.strip()
            return path if path else ""
        except Exception:
            return ""

    async def reset_database(self):
        """Manually clear the library storage."""
        try:
            yield rx.toast("Clearing library storage...")
            await MelodiusAPI.clear_library()
            async with self:
                self.clear_player_state()
            await self.fetch_tracks()
            yield rx.toast("Library storage cleared!")
        except Exception as e:
            yield rx.toast(f"Reset failed: {str(e)}")

    @rx.event(background=True)
    async def find_player_by_url(self):
        # Get the API port from environment variable (consistent with api.py)
        api_port = os.getenv("MELODIUS_API_PORT", "8001")
        base_url = f"http://127.0.0.1:{api_port}/tracks/stream/"
        script = f"""
        setTimeout(() => {{
            var p = document.querySelector('video[src^="{base_url}"]');
            if (p) {{
                p.id = 'audio-player';
                p.style.display = 'none';
                p.style.width = '0px';
                p.style.height = '0px';
                if ({self.current_time} > 0 && Math.abs(p.currentTime - {self.current_time}) > 1) {{
                    p.currentTime = {self.current_time};
                }}
            }}
        }}, 500);
        """
        yield rx.call_script(script)
        await asyncio.sleep(0.1)
        yield State.tick_time
        if self.experimental_eq:
            from ..components.equalizer.equalizer_lab import EqualizerState as LabEqualizerState
            yield LabEqualizerState.apply_eq()
        else:
            from ..components.equalizer.equalizer import EqualizerState
            yield EqualizerState.apply_eq()

    @rx.event(background=True)
    async def tick_time(self):
        async with self:
            if getattr(self, "_timer_running", False):
                return
            self._timer_running = True

        while True:
            await asyncio.sleep(1)
            async with self:
                if not self.is_playing:
                    self._timer_running = False
                    break
                yield State.update_time()
                if self.current_time >= (self.duration - 0.5) and self.duration > 0:
                    self.is_playing = False
                    self._timer_running = False
                    yield State.next_track
                    break
        async with self:
            self._timer_running = False

    def play_track(self, track: Track):
        new_url = f"{track.url.split('?')[0]}?t={random.random()}"
        self.current_track = Track(
            id=track.id,
            title=track.title,
            artist=track.artist,
            url=new_url,
            cover_url=track.cover_url,
            duration=track.duration
        )
        self.duration = float(track.duration)
        self.last_played_track = {
            "id": track.id,
            "title": track.title,
            "artist": track.artist,
            "url": new_url,
            "cover_url": track.cover_url,
            "duration": track.duration
        }
        self.current_time = 0.0
        self.last_played_time = 0.0
        self.is_playing = True
        self.save_data()
        
        if self.experimental_eq:
            from ..components.equalizer.equalizer_lab import EqualizerState as LabEqualizerState
            return [State.tick_time, State.find_player_by_url, LabEqualizerState.initialize_engine()]
        else:
            from ..components.equalizer.equalizer import EqualizerState
            return [State.tick_time, State.find_player_by_url, EqualizerState.initialize_engine()]

    def toggle_play(self):
        if self.current_track.url != "":
            self.is_playing = not self.is_playing
            if not self.is_playing:
                self.save_data()
            else:
                yield State.tick_time
                if self.experimental_eq:
                    from ..components.equalizer.equalizer_lab import EqualizerState as LabEqualizerState
                    yield LabEqualizerState.initialize_engine()
                else:
                    from ..components.equalizer.equalizer import EqualizerState
                    yield EqualizerState.initialize_engine()

    def sync_time(self, data: dict):
        if not self.is_dragging:
            self.current_time = float(data.get("time", 0))
            self.last_played_time = float(self.current_time)

    def update_time(self):
        script = """
        (() => {
            var p = document.getElementById('audio-player');
            return { "time": p ? p.currentTime : 0 };
        })()
        """
        return rx.call_script(script, callback=State.sync_time)
    
    def toggle_shuffle(self):
        self.is_shuffled = not self.is_shuffled
        self.save_data()

    def next_track(self):
        current_list = self.filtered_tracks
        if not current_list or not self.current_track.title:
            return
        if self.is_shuffled:
            next_idx = random.randint(0, len(current_list) - 1)
        else:
            current_idx = next((i for i, t in enumerate(current_list) if t.url == self.current_track.url.split('?')[0]), -1)
            if current_idx == -1:
                next_idx = 0
            else:
                next_idx = (current_idx + 1) % len(current_list)
        return self.play_track(current_list[next_idx])

    def prev_track(self):
        current_list = self.filtered_tracks
        if not current_list or not self.current_track.title:
            return
        current_idx = next((i for i, t in enumerate(current_list) if t.url == self.current_track.url.split('?')[0]), -1)
        if current_idx == -1:
            prev_idx = len(current_list) - 1
        else:
            prev_idx = (current_idx - 1) % len(current_list)
        return self.play_track(current_list[prev_idx])

    def start_dragging(self, value: list[float]):
        self.is_dragging = True
        self.current_time = float(value[0])

    def set_volume(self, value: list[float]):
        self.volume = value[0] / 100
        self.save_data()

    def seek(self, value: list[float]):
        target_time = float(value[0])
        self.is_dragging = False
        self.is_playing = True  
        self.last_played_time = target_time
        self.current_time = target_time
        self.save_data()
        return [
            rx.call_script(f"document.getElementById('audio-player').currentTime = {target_time};"),
            State.tick_time 
        ]

    def seek_from_bar(self, percent: int):
        """Calculates seconds from a 0-100 percentage and jumps the song."""
        if self.duration <= 0:
            return
        target_time = (percent / 100) * self.duration
        self.current_time = float(target_time)

    @rx.var
    def progress_percentage(self) -> int:
        """Calculates the 0-100 percentage for the progress bar."""
        if self.duration <= 0 or self.current_time <= 0:
            return 0
        return int((self.current_time / self.duration) * 100)

    @rx.var
    def formatted_current_time(self) -> str:
        m, s = divmod(int(self.current_time), 60)
        return f"{m}:{s:02d}"

    @rx.var
    def formatted_duration(self) -> str:
        m, s = divmod(int(self.duration), 60)
        return f"{m}:{s:02d}"

    def hide_ghost_box(self):
        script = """
        var p = document.querySelector('video, audio');
        if (p) {
            p.style.display = 'none';
            p.style.width = '0px';
            p.style.height = '0px';
            p.style.position = 'fixed';
            p.style.top = '-9999px';
        }
        """
        return rx.call_script(script)
