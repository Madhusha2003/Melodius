from sqlalchemy import Column, Integer, String, Boolean
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
    has_cover = Column(Boolean, default=False)

    @property
    def url(self):
        # Stream the source file directly from the FastAPI backend securely
        import os
        api_port = os.getenv("MELODIUS_API_PORT", "8001")
        return f"http://127.0.0.1:{api_port}/tracks/stream/{self.id}"

    @property
    def cover_url(self):
        # Dynamically fetch cover from the file via the backend if it has one
        if not self.has_cover:
            return ""
        import os
        api_port = os.getenv("MELODIUS_API_PORT", "8001")
        return f"http://127.0.0.1:{api_port}/tracks/cover/{self.id}"
