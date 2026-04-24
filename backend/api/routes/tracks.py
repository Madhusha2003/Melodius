from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
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
def scan_tracks(db: Session = Depends(get_db)):
    tracks_data = scan_local_music()
    added_count = 0
    
    for track_data in tracks_data:
        existing = db.query(models.Track).filter(models.Track.file_path == track_data["file_path"]).first()
        if not existing:
            new_track = models.Track(
                title=track_data["title"],
                artist=track_data["artist"],
                file_path=track_data["file_path"],
                duration=track_data.get("duration", 0.0)
            )
            db.add(new_track)
            added_count += 1
            
    db.commit()
    return {"status": "success", "added_count": added_count, "total_found": len(tracks_data)}

@router.get("/stream/{track_id}")
def stream_track(track_id: int, request: Request, db: Session = Depends(get_db)):
    track = db.query(models.Track).filter(models.Track.id == track_id).first()
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    return get_audio_stream(track.file_path, request)
