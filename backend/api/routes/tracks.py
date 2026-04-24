import os
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session
import mutagen
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC
from mutagen.flac import FLAC
import models
import schemas
from database import get_db
from services.audio import get_audio_stream
from scanner import scan_local_music

router = APIRouter(prefix="/tracks", tags=["tracks"])

@router.get("/", response_model=list[schemas.Track])
def read_tracks(skip: int = 0, limit: int = 1000, db: Session = Depends(get_db)):
    tracks = db.query(models.Track).offset(skip).limit(limit).all()
    return tracks

@router.post("/", response_model=schemas.Track)
def create_track(track: schemas.TrackCreate, db: Session = Depends(get_db)):
    db_track = models.Track(**track.model_dump())
    db.add(db_track)
    db.commit()
    db.refresh(db_track)
    return db_track

@router.post("/scan")
def scan_tracks(directory: str = None, db: Session = Depends(get_db)):
    tracks_data = scan_local_music(directory)
    added_count = 0
    
    for track_data in tracks_data:
        existing = db.query(models.Track).filter(models.Track.file_path == track_data["file_path"]).first()
        if not existing:
            new_track = models.Track(
                title=track_data["title"],
                artist=track_data["artist"],
                file_path=track_data["file_path"],
                duration=track_data.get("duration", 0.0),
                has_cover=track_data.get("has_cover", False)
            )
            db.add(new_track)
            added_count += 1
            
    db.commit()
    return {"status": "success", "added_count": added_count, "total_found": len(tracks_data)}

@router.delete("/")
def delete_all_tracks(db: Session = Depends(get_db)):
    db.query(models.Track).delete()
    db.commit()
    return {"status": "success", "message": "All tracks deleted"}

@router.get("/stream/{track_id}")
def stream_track(track_id: int, request: Request, db: Session = Depends(get_db)):
    track = db.query(models.Track).filter(models.Track.id == track_id).first()
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    return get_audio_stream(track.file_path, request)

@router.get("/cover/{track_id}")
def get_track_cover(track_id: int, db: Session = Depends(get_db)):
    track = db.query(models.Track).filter(models.Track.id == track_id).first()
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    
    try:
        file_path = track.file_path
        if not os.path.exists(file_path):
             raise HTTPException(status_code=404, detail="File not found")

        # Try to extract art based on extension
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext == ".mp3":
            try:
                audio = ID3(file_path)
                for tag in audio.values():
                    if isinstance(tag, APIC):
                        return Response(content=tag.data, media_type=tag.mime)
            except:
                pass
        elif ext == ".flac":
            try:
                audio = FLAC(file_path)
                if audio.pictures:
                    return Response(content=audio.pictures[0].data, media_type=audio.pictures[0].mime)
            except:
                pass
        else:
            # General mutagen attempt
            try:
                audio = mutagen.File(file_path)
                if hasattr(audio, 'pictures') and audio.pictures:
                    return Response(content=audio.pictures[0].data, media_type=audio.pictures[0].mime)
                # Some formats use tags for art
                if audio.tags:
                    for tag in audio.tags.values():
                        if hasattr(tag, 'data') and hasattr(tag, 'mime'):
                             return Response(content=tag.data, media_type=tag.mime)
            except:
                pass
                
    except Exception as e:
        from core.logger import logger
        logger.error(f"Error extracting cover for {track_id}: {e}")
        
    # Return 404 or a default image if no cover found
    raise HTTPException(status_code=404, detail="No cover found")
