import os
from pathlib import Path
import mutagen
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3

def scan_local_music(directory: str = None) -> list[dict]:
    if directory is None:
        # Check for OneDrive paths
        onedrive_music = os.path.join(os.path.expanduser("~"), "OneDrive", "Music")
        default_music = os.path.join(os.path.expanduser("~"), "Music")
        
        if os.path.exists(onedrive_music):
            directory = onedrive_music
        else:
            directory = default_music
            
    # Handle Windows Long Paths
    if os.name == "nt":
        abs_dir = os.path.abspath(directory)
        if not abs_dir.startswith("\\\\?\\"):
            directory = "\\\\?\\" + abs_dir
        
    found_tracks = []
    supported_extensions = {".mp3", ".wav", ".flac", ".m4a", ".ogg"}

    print(f"--- Starting Scan in: {directory} ---")
    
    if not os.path.exists(directory):
        print(f"Directory not found: {directory}")
        return found_tracks
        
    for root, _, files in os.walk(directory):
        for file in files:
            try:
                # Log every single file encountered
                print(f"Encountered: {os.path.join(root, file)}")
                
                path = Path(root) / file
                if path.suffix.lower() in supported_extensions:
                    
                    # Default fallbacks
                    title = path.stem
                    artist = "Unknown Artist"
                    duration = 0.0

                    try:
                        # 1. Handle MP3 specifically for EasyID3 (very reliable for Artist/Title)
                        if path.suffix.lower() == ".mp3":
                            audio_tags = EasyID3(str(path))
                            title = audio_tags.get("title", [path.stem])[0]
                            artist = audio_tags.get("artist", ["Unknown Artist"])[0]
                            
                            audio_info = MP3(str(path))
                            duration = audio_info.info.length
                        
                        # 2. Handle other formats (FLAC, OGG, etc.)
                        else:
                            audio = mutagen.File(str(path))
                            if audio:
                                # Mutagen's general File object uses a dict-like interface for tags
                                if hasattr(audio, "tags") and audio.tags:
                                    # Standard tag keys for non-MP3s
                                    title = audio.tags.get("title", [path.stem])[0]
                                    artist = audio.tags.get("artist", ["Unknown Artist"])[0]
                                
                                if hasattr(audio.info, "length"):
                                    duration = audio.info.length

                    except Exception as e:
                        print(f"Error reading metadata for {file}: {e}")
                        # Keep defaults if tag reading fails

                    # Clean up the \\?\ prefix for the UI and DB path
                    clean_path = str(path)
                    if clean_path.startswith("\\\\?\\"):
                        clean_path = clean_path[4:]
                    
                    found_tracks.append({
                        "title": str(title)[:255],
                        "artist": str(artist)[:255],
                        "file_path": clean_path,
                        "duration": duration,
                    })
                    
            except Exception as e:
                # Try/Except block around the entire loop body so that one 'Permission Denied' 
                # error doesn't kill the scan for the remaining songs.
                print(f"Error processing file {file} in {root}: {e}")
                
    return found_tracks