import reflex as rx
import httpx
import random
import asyncio
from datetime import datetime, timedelta
import time
from .components.equalizer.equalizer import equalizer_ui
from .components.visualizer.visualizer import visualizer_ui
from .components.equalizer.equalizer import EqualizerState
import json
import os

DATA_FILE = "user_data.json"
class Track(rx.Base):
    title: str
    artist: str
    url: str
    duration: float = 0.0

class State(rx.State):
    tracks: list[Track] = []
    
    # Persistent Data
    last_played_track: dict = {}
    last_played_time: float = 0.0
    
    current_track: Track = Track(title="", artist="", url="", duration=0.0)
    is_playing: bool = False
    is_shuffled: bool = False
    
    # Audio State
    current_time: float = 0.0
    duration: float = 0.0
    volume: float = 1.0
    is_dragging: bool = False
    
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
        
        with open(DATA_FILE, "w") as f:
            json.dump(data, f, indent=4)

    _timer_running: bool = False

    def on_load(self):
        """Restore previous session data from JSON if available."""
        self.is_playing = False
        self._timer_running = False
        
        # Load from JSON
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r") as f:
                    data = json.load(f)
                    self.last_played_track = data.get("last_played_track", {})
                    self.last_played_time = float(data.get("last_played_time", 0.0))
                    self.is_shuffled = bool(data.get("is_shuffled", False))
                    self.volume = float(data.get("volume", 1.0))
            except Exception as e:
                print("Error loading frontend data:", e)
        
        if self.last_played_track and self.last_played_track.get("title"):
            self.current_track = Track(**self.last_played_track)
            self.duration = float(self.current_track.duration)
            self.current_time = float(self.last_played_time)
            return [State.fetch_tracks, State.find_player_by_url]
        else:
            self.current_time = 0.0
            return [State.fetch_tracks]

    def hide_ghost_box(self):
        """🚀 THE QUICK FIX: Hides the engine immediately on load."""
        script = """
        // Find the first video or audio element rendered by Reflex
        var p = document.querySelector('video, audio');
        if (p) {
            p.style.display = 'none';
            p.style.width = '0px';
            p.style.height = '0px';
            p.style.position = 'fixed';
            p.style.top = '-9999px';
            console.log('Ghost box hidden by simple selector.');
        }
        """
        return rx.call_script(script)

    async def fetch_tracks(self):
        # Fetching from your FastAPI backend
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8001/tracks/")
            if response.status_code == 200:
                self.tracks = [Track(**track) for track in response.json()]

    async def scan_music(self):
        # Trigger the backend to scan the local music folder
        async with httpx.AsyncClient() as client:
            # Increase timeout since mutagen extraction might take time on large libraries
            response = await client.post("http://localhost:8001/scan/", timeout=120.0)
            if response.status_code == 200:
                # Refresh the UI track list
                await self.fetch_tracks()
    
    # THE GREAT FIX AFTER MANY TRIES 👌👌👌👌👌👌👌👌👌👌👌
    @rx.event(background=True)
    async def find_player_by_url(self):
        # 🚀 THE FIX: Target the 'video' tag that starts with your stream URL
        # This will find it even if the class is 'css-1hyfx7x'
        base_url = "http://localhost:8001/stream/"
        
        script = f"""
        setTimeout(() => {{
            var p = document.querySelector('video[src^="{base_url}"]');
            if (p) {{
                p.id = 'audio-player';
                p.style.display = 'none';
                p.style.width = '0px';
                p.style.height = '0px';
                console.log('Found and hidden by URL!');
                console.log('ID "audio-player" successfully mapped to media element!');
                
                // If we have a saved time, restore it
                if ({self.current_time} > 0 && Math.abs(p.currentTime - {self.current_time}) > 1) {{
                    p.currentTime = {self.current_time};
                    console.log('Time restored to: ' + {self.current_time});
                }}
            }}
        }}, 500);
        """
        yield rx.call_script(script)
        await asyncio.sleep(0.1)
        yield State.tick_time()
        from .components.equalizer.equalizer import EqualizerState
        yield EqualizerState.apply_eq()

    # App timer
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
                
                # Ask the hardware for the real time.
                yield State.update_time()

                # Check if song is finished (hardware based)
                if self.current_time >= (self.duration - 0.5) and self.duration > 0:
                    self.is_playing = False
                    self._timer_running = False
                    yield State.next_track
                    break

        async with self:
            self._timer_running = False

    def play_track(self, track: Track):
        """Resets everything for a fresh start."""
        new_url = f"{track.url.split('?')[0]}?t={random.random()}"
        self.current_track = Track(
            title=track.title,
            artist=track.artist,
            url=new_url,
            duration=track.duration
        )
        self.duration = float(track.duration)
        
        self.last_played_track = {
            "title": track.title,
            "artist": track.artist,
            "url": new_url,
            "duration": track.duration
        }
        
        # 🚀 RESET: Start from 0
        self.current_time = 0.0
        self.last_played_time = 0.0
        self.is_playing = True
        
        self.save_data()
        
        # 🚀 START: Trigger the manual timer
        return [State.tick_time, State.find_player_by_url]

    def toggle_play(self):
        """Pauses or Resumes the manual timer."""
        if self.current_track.url != "":
            self.is_playing = not self.is_playing
            if not self.is_playing:
                self.save_data()  # Save progress when paused
            else:
                yield State.tick_time
                yield EqualizerState.initialize_engine()

    def sync_time(self, data: dict):
        # Reflex catches the 'detail' from our JS CustomEvent here
        if not self.is_dragging:
            self.current_time = float(data.get("time", 0))
            self.last_played_time = float(self.current_time)

    def update_time(self):
        """Fetches the actual hardware time and sends it to sync_time."""
        # 🚀 THE FIX: Use an IIFE to return the time dictionary safely to Reflex
        script = """
        (() => {
            var p = document.getElementById('audio-player');
            return { "time": p ? p.currentTime : 0 };
        })()
        """
        # Execute the script and map the returned JS object to your sync_time method
        return rx.call_script(script, callback=State.sync_time)
    
    def toggle_shuffle(self):
        self.is_shuffled = not self.is_shuffled
        self.save_data()

    def next_track(self):
        if not self.tracks or not self.current_track.title:
            return
            
        if self.is_shuffled:
            next_idx = random.randint(0, len(self.tracks) - 1)
        else:
            current_idx = next((i for i, t in enumerate(self.tracks) if t.url == self.current_track.url.split('?')[0]), -1)
            next_idx = (current_idx + 1) % len(self.tracks)
            
        self.play_track(self.tracks[next_idx])

    def prev_track(self):
        if not self.tracks or not self.current_track.title:
            return
            
        current_idx = next((i for i, t in enumerate(self.tracks) if t.url == self.current_track.url.split('?')[0]), -1)
        prev_idx = (current_idx - 1) % len(self.tracks)
        self.play_track(self.tracks[prev_idx])

    def start_dragging(self, value: list[float]):
        self.is_dragging = True
        self.current_time = float(value[0])

    def set_volume(self, value: list[float]):
        self.volume = value[0] / 100
        self.save_data()

    def go_to_time(self, time: float):
        self.current_time = time

    def seek(self, value: list[float]):
        """Standard seeker with an immediate hardware refresh."""
        target_time = float(value[0])
        self.is_dragging = False
        self.is_playing = True  
        self.last_played_time = target_time
        self.save_data()
        # 🚀 We do two things: 1. Jump the music, 2. Tell the UI to refresh immediately
        return [
            rx.call_script(f"document.getElementById('audio-player').currentTime = {target_time};"),
            State.go_to_time(target_time),
            State.tick_time 
        ]
    
    def seek_from_bar(self, percent: int):
        """Calculates seconds from a 0-100 percentage and jumps the song."""
        if self.duration <= 0:
            return
            
        # Formula: (Percent / 100) * Total Duration
        target_time = (percent / 100) * self.duration
        self.current_time = float(target_time)

    @rx.var
    def progress_percentage(self) -> int:
        """Calculates the 0-100 percentage for the progress bar."""
        # Check if duration is zero or current_time is zero to avoid float math
        if self.duration <= 0 or self.current_time <= 0:
            return 0 # Return a plain integer 0, not 0.0
        
        # 1. Perform the division (result is a float)
        # 2. Multiply by 100 (result is still a float)
        # 3. Convert the final result to an integer
        return int((self.current_time / self.duration) * 100)

    @rx.var
    def formatted_current_time(self) -> str:
        """Converts raw seconds into M:SS format."""
        m, s = divmod(int(self.current_time), 60)
        return f"{m}:{s:02d}"

    @rx.var
    def formatted_duration(self) -> str:
        """Converts total duration into M:SS format."""
        m, s = divmod(int(self.duration), 60)
        return f"{m}:{s:02d}"

    """
    @rx.var
    def formatted_current_time(self) -> str:
        minutes = int(self.current_time // 60)
        seconds = int(self.current_time % 60)
        return f"{minutes}:{seconds:02d}"

    @rx.var
    def formatted_duration(self) -> str:
        minutes = int(self.duration // 60)
        seconds = int(self.duration % 60)
        return f"{minutes}:{seconds:02d}"
    """
def index() -> rx.Component:
    return rx.box(
        # 🚀 1. THE ENGINE (Always Stay Audio Player)
            
        rx.audio(
            id="audio-player",
            src=State.current_track.url,
            playing=State.is_playing,
            volume=State.volume,
            #on_time_update=State.update_time,
            on_ended=State.next_track,
            controls=False,
            custom_attrs={"crossOrigin": "anonymous"}
        ),

        # 🌟 Header (Top Left)
        rx.hstack(
            rx.icon(tag="audio-waveform", size=32, color="var(--accent-9)"),
            rx.heading("Melodius", size="7", font_weight="bold", letter_spacing="-0.02em"),
            width="100%",
            padding="2em",
            align_items="center",
            spacing="3",
        ),

        # 2. Main Layout (Scrollable Track List + Equalizer)
        rx.center(
            rx.hstack(
                rx.vstack(
                    rx.hstack(
                        rx.heading("Your Library", size="5", font_weight="600"),
                        rx.spacer(),
                        rx.button(
                            rx.icon(tag="folder_sync"),
                            "Scan Local Library",
                            on_click=State.scan_music,
                            size="2",
                            variant="soft",
                            color_scheme="blue",
                            border_radius="full",
                            cursor="pointer",
                        ),
                        width="100%",
                        padding_bottom="1.5em",
                        align_items="center",
                        border_bottom="1px solid var(--gray-4)",
                        margin_bottom="1em",
                    ),
                    rx.box(
                        rx.foreach(
                            State.tracks,
                            lambda track: rx.hstack(
                                rx.box(
                                    rx.icon(tag="play", size=18),
                                    padding="0.8em",
                                    border_radius="full",
                                    background="var(--accent-3)",
                                    color="var(--accent-11)",
                                    cursor="pointer",
                                    _hover={"background": "var(--accent-4)", "transform": "scale(1.05)"},
                                    transition="all 0.2s ease",
                                    on_click=lambda: State.play_track(track),
                                ),
                                rx.vstack(
                                    rx.text(track.title, font_weight="600", size="3"),
                                    rx.text(track.artist, size="2", color="gray"),
                                    align_items="start",
                                    spacing="1",
                                ),
                                width="100%",
                                padding="1em",
                                border_radius="12px",
                                _hover={"background": "var(--gray-3)"},
                                transition="background 0.2s ease",
                                align_items="center",
                                spacing="4",
                            )
                        ),
                        width="100%",
                        display="flex",
                        flex_direction="column",
                        gap="0.5em",
                        max_height="60vh",
                        overflow_y="auto",
                        padding_right="0.5em",
                    ),
                    width="100%",
                    padding="2.5em",
                    background="var(--gray-2)",
                    border_radius="24px",
                    box_shadow="0 10px 40px rgba(0,0,0,0.1)",
                    flex="1",
                ),
                
                # Right Side: Visualizer and Equalizer Component
                rx.cond(
                    State.current_track.url != "",
                    rx.vstack(
                        visualizer_ui(),
                        equalizer_ui(),
                        width="100%",
                        flex="1",
                        spacing="6",
                    )
                ),
                
                # Container settings
                width="100%",
                max_width="1200px",
                align_items="stretch",
                spacing="6",
                margin_bottom="150px", # Space for bottom player
            ),
            width="100%",
            on_mount=State.fetch_tracks,
        ),

        # 🚀 3. THE VISUAL UI (Only show when a song is picked)
        rx.cond(
            State.current_track.url != "",
            rx.box(
                rx.hstack(
                    # Left: Track Info
                    rx.hstack(
                        rx.vstack(
                            rx.text(State.current_track.title, font_weight="bold", size="3"),
                            rx.text(State.current_track.artist, size="2", color="gray"),
                            align_items="start",
                            width="200px",
                        ),
                    ),
                    rx.spacer(),
                    
                    # Middle: Playback Controls & Scrubber
                    rx.vstack(
                        rx.hstack(
                            rx.button(rx.icon(tag="shuffle"), variant="ghost", color_scheme=rx.cond(State.is_shuffled, "accent", "gray"), on_click=State.toggle_shuffle),
                            rx.button(rx.icon(tag="skip_back"), variant="ghost", on_click=State.prev_track),
                            rx.button(
                                rx.icon(tag=rx.cond(State.is_playing, "pause", "play")), 
                                size="3", variant="solid", radius="full", 
                                on_click=State.toggle_play,
                                box_shadow=rx.cond(State.is_playing, "0 0 15px rgba(66, 153, 225, 0.6)", "none"),
                            ),
                            rx.button(rx.icon(tag="skip_forward"), variant="ghost", on_click=State.next_track),
                            spacing="4",
                            align_items="center",
                        ),
                       rx.hstack(
                            rx.text(State.formatted_current_time, size="1", color="gray", width="40px", text_align="right"),
                            
                            rx.slider(
                                value=[State.current_time], 
                                min=0, 
                                max=State.duration,
                                on_change=State.start_dragging, 
                                on_value_commit=State.seek,           
                                width="100%",                         
                                #color_scheme="blue",
                                cursor="pointer",
                                # 🚀 THE MAGIC: Hide thumb by default, show on hover
                                style={
                                    # 1. The background track (the grey empty part)
                                    "& .rt-SliderTrack": {
                                        "height": "4px !important",
                                        "background-color": "rgba(255, 255, 255, 0.2) !important",
                                        "cursor": "pointer !important",
                                    },
                                    # 2. The filled progress part (pure white)
                                    "& .rt-SliderRange": {
                                        "height": "4px !important",
                                        "background-color": "white !important",
                                        "transition": "background-color 0.1s ease",
                                    },
                                    # 3. The thumb (hidden by default using opacity)
                                    "& .rt-SliderThumb": {
                                        "opacity": "0 !important", 
                                        "width": "12px !important",
                                        "height": "12px !important",
                                        "background-color": "white !important",
                                        "box-shadow": "0 2px 4px rgba(0,0,0,0.5) !important",
                                        "transition": "opacity 0.1s ease !important",
                                        "cursor": "pointer !important",
                                    },
                                    # 4. HOVER EFFECTS: Show thumb and change bar color
                                    "&:hover .rt-SliderThumb": {
                                        "opacity": "1 !important"
                                    },
                                    "&:hover .rt-SliderRange": {
                                        # Spotify turns green on hover; you can use "var(--accent-9)" for blue, or keep it white!
                                        "background-color": "var(--accent-9) !important", 
                                    }
                                }
                            ),
                            
                            rx.text(State.formatted_duration, size="1", color="gray", width="40px"),
                            width="100%",
                            spacing="4",
                            align_items="center",
                        ),
                        align_items="center",
                        width="100%",
                    ),
                    rx.spacer(),
                    
                    # Right: Volume Control
                    rx.hstack(
                        rx.icon(tag="volume_2", size=18, color="gray"),
                        rx.slider(
                            default_value=[100], 
                            min=0, max=100, 
                            on_value_commit=State.set_volume, 
                            width="100px"
                        ),
                        width="200px",
                        justify="end",
                    ),
                    width="100%",
                    align_items="center",
                ),
                position="fixed",
                bottom="0",
                width="100%",
                padding="1em 2em",
                background="rgba(10, 10, 10, 0.9)",
                backdrop_filter="blur(20px)",
                border_top="1px solid rgba(255,255,255,0.08)",
            )
        ),
        background="black",
        color="white",
        min_height="100vh",
        overflow="hidden",
    on_mount=[State.fetch_tracks, State.hide_ghost_box],
    )

app = rx.App()
app.add_page(index, on_load=[State.on_load])