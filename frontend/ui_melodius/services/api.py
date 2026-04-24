import os
import httpx
from pydantic import BaseModel

# Get the API port from environment variable (set by launcher)
api_port = os.getenv("MELODIUS_API_PORT", "8002")

class Track(BaseModel):
    id: int = 0
    title: str
    artist: str
    url: str
    cover_url: str = ""
    duration: float = 0.0

class MelodiusAPI:
    BASE_URL = f"http://127.0.0.1:{api_port}"

    @classmethod
    async def get_tracks(cls):
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{cls.BASE_URL}/tracks/")
            response.raise_for_status()
            return response.json()

    @classmethod
    async def scan_music(cls, directory: str = None):
        async with httpx.AsyncClient() as client:
            params = {"directory": directory} if directory else {}
            response = await client.post(f"{cls.BASE_URL}/tracks/scan", params=params, timeout=120.0)
            response.raise_for_status()
            return response.json()

    @classmethod
    async def clear_library(cls):
        async with httpx.AsyncClient() as client:
            response = await client.delete(f"{cls.BASE_URL}/tracks/")
            response.raise_for_status()
            return response.json()
