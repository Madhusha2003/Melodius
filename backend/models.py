from sqlalchemy import Column, Integer, String
from database import Base

class Track(Base):
    __tablename__ = "tracks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    artist = Column(String, index=True)
    album = Column(String, index=True, nullable=True)
    file_path = Column(String, unique=True, index=True)
    duration = Column(Integer, default=0)
    vibe_vector = Column(String, nullable=True)

    @property
    def url(self):
        # Stream the source file directly from the FastAPI backend securely
        return f"http://127.0.0.1:8001/tracks/stream/{self.id}"
