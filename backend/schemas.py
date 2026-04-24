from pydantic import BaseModel

from typing import Optional

class TrackBase(BaseModel):
    title: str
    artist: str
    album: Optional[str] = None
    file_path: str
    duration: float = 0.0
    vibe_vector: Optional[str] = None
    url: Optional[str] = None
    cover_url: Optional[str] = None

class TrackCreate(TrackBase):
    pass

class Track(TrackBase):
    id: int
    
    model_config = {"from_attributes": True}
