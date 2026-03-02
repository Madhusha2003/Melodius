import os
from pathlib import Path
import mutagen

def scan_local_music(directory: str = None) -> list[dict]:
    # Default to the user's Music directory on Windows
    if directory is None:
        directory = os.path.expanduser("~\\Music")
        
    found_tracks = []
    # Supported audio formats for the web player
    supported_extensions = {".mp3", ".wav", ".flac", ".m4a", ".ogg"}
    
    if not os.path.exists(directory):
        print(f"Directory not found: {directory}")
        return found_tracks
        
    print(f"Scanning directory: {directory}")
    for root, _, files in os.walk(directory):
        for file in files:
            path = Path(root) / file
            if path.suffix.lower() in supported_extensions:
                # Basic metadata extraction using filename
                title = path.stem
                artist = "Unknown Artist"
                
                # Attempt to split "Artist - Title" convention
                if " - " in title:
                    parts = title.split(" - ", 1)
                    artist = parts[0].strip()
                    title = parts[1].strip()
                    
                # Extract exact duration using mutagen
                try:
                    audio_info = mutagen.File(str(path))
                    duration = audio_info.info.length if audio_info and hasattr(audio_info.info, "length") else 0.0
                except Exception:
                    duration = 0.0

                found_tracks.append({
                    "title": title[:255], # Cap length to avoid DB errors
                    "artist": artist[:255],
                    "file_path": str(path),
                    "duration": duration,
                })
                
    return found_tracks
