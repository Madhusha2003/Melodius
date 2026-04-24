import os
from pathlib import Path
import mutagen
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC
from mutagen.flac import FLAC
from core.logger import logger

def has_embedded_cover(file_path: str) -> bool:
    try:
        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".mp3":
            audio = ID3(file_path)
            for tag in audio.values():
                if isinstance(tag, APIC):
                    return True
        elif ext == ".flac":
            audio = FLAC(file_path)
            if audio.pictures:
                return True
        else:
            audio = mutagen.File(file_path)
            if hasattr(audio, 'pictures') and audio.pictures:
                return True
            if audio.tags:
                for tag in audio.tags.values():
                    if hasattr(tag, 'data') and hasattr(tag, 'mime'):
                         return True
    except:
        pass
    return False

def scan_local_music(directory: str = None) -> list[dict]:
    if directory is None:
        onedrive_music = os.path.join(os.path.expanduser("~"), "OneDrive", "Music")
        default_music = os.path.join(os.path.expanduser("~"), "Music")
        
        if os.path.exists(onedrive_music):
            directory = onedrive_music
        else:
            directory = default_music
            
    if os.name == "nt":
        abs_dir = os.path.abspath(directory)
        if not abs_dir.startswith("\\\\?\\"):
            directory = "\\\\?\\" + abs_dir
        
    found_tracks = []
    supported_extensions = {".mp3", ".wav", ".flac", ".m4a", ".ogg"}

    logger.info(f"Starting Scan in: {directory}")
    
    if not os.path.exists(directory):
        logger.warning(f"Directory not found: {directory}")
        return found_tracks
        
    for root, _, files in os.walk(directory):
        for file in files:
            try:
                path = Path(root) / file
                if path.suffix.lower() in supported_extensions:
                    title = path.stem
                    artist = "Unknown Artist"
                    duration = 0.0
                    has_cover = False

                    try:
                        has_cover = has_embedded_cover(str(path))
                        
                        if path.suffix.lower() == ".mp3":
                            audio_tags = EasyID3(str(path))
                            title = audio_tags.get("title", [path.stem])[0]
                            artist = audio_tags.get("artist", ["Unknown Artist"])[0]
                            
                            audio_info = MP3(str(path))
                            duration = audio_info.info.length
                        else:
                            audio = mutagen.File(str(path))
                            if audio:
                                if hasattr(audio, "tags") and audio.tags:
                                    title = audio.tags.get("title", [path.stem])[0]
                                    artist = audio.tags.get("artist", ["Unknown Artist"])[0]
                                
                                if hasattr(audio.info, "length"):
                                    duration = audio.info.length

                    except Exception as e:
                        logger.debug(f"Metadata error for {file}: {e}")

                    clean_path = str(path)
                    if clean_path.startswith("\\\\?\\"):
                        clean_path = clean_path[4:]
                    
                    found_tracks.append({
                        "title": str(title)[:255],
                        "artist": str(artist)[:255],
                        "file_path": clean_path,
                        "duration": duration,
                        "has_cover": has_cover
                    })
                    
            except Exception as e:
                logger.error(f"Error processing {file}: {e}")
                
    logger.info(f"Scan complete. Found {len(found_tracks)} tracks.")
    return found_tracks