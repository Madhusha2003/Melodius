import os
from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import models
import mimetypes
import schemas
from database import engine, get_db

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Melodius API")

@app.on_event("startup")
def connection_check():
    print("Database connected successfully.")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Welcome to Melodius API"}

@app.post("/tracks/", response_model=schemas.Track)
def create_track(track: schemas.TrackCreate, db: Session = Depends(get_db)):
    db_track = models.Track(**track.model_dump())
    db.add(db_track)
    db.commit()
    db.refresh(db_track)
    return db_track

@app.get("/tracks/", response_model=list[schemas.Track])
def read_tracks(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    tracks = db.query(models.Track).offset(skip).limit(limit).all()
    return tracks

@app.post("/scan/")
def scan_music_library(db: Session = Depends(get_db)):
    from scanner import scan_local_music
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
from fastapi import Request
from fastapi.responses import StreamingResponse
import os
@app.get("/stream/{track_id}")
def stream_track(track_id: int, request: Request, db: Session = Depends(get_db)):
    track = db.query(models.Track).filter(models.Track.id == track_id).first()

    if not track or not track.file_path or not os.path.exists(track.file_path):
        raise HTTPException(status_code=404, detail="Audio file not found")

    file_path = track.file_path
    file_size = os.stat(file_path).st_size
    range_header = request.headers.get("range")

    # 1. Parse Range Header properly
    start, end = 0, file_size - 1
    if range_header:
        # Format is usually 'bytes=0-1023'
        try:
            h_range = range_header.replace("bytes=", "").split("-")
            if h_range[0]:
                start = int(h_range[0])
            if h_range[1]:
                end = int(h_range[1])
            # Ensure 'end' doesn't exceed file size
            if end >= file_size:
                end = file_size - 1
        except (ValueError, IndexError):
            pass

    # 2. Calculate actual chunk size
    chunk_size = (end - start) + 1
    
    # 3. Memory-efficient file iterator
    def file_iterator():
        with open(file_path, "rb") as f:
            f.seek(start)
            bytes_left = chunk_size
            while bytes_left > 0:
                # Read in 128KB chunks (bigger is often better for local disk)
                to_read = min(bytes_left, 128 * 1024)
                data = f.read(to_read)
                if not data:
                    break
                yield data
                bytes_left -= len(data)

    # 4. Return 206 with ALL necessary headers
    return StreamingResponse(
        file_iterator(),
        status_code=206, 
        headers={
            "Content-Range": f"bytes {start}-{end}/{file_size}",
            "Accept-Ranges": "bytes",
            "Content-Length": str(chunk_size),
            "Content-Type": "audio/mpeg",
            "Cache-Control": "no-cache", # Prevents the "stuck at 0" cache bug
            "Access-Control-Allow-Origin": "*",
        },
    )