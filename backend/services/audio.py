import os
from fastapi import HTTPException, Request
from fastapi.responses import StreamingResponse
from core.config import settings

def get_audio_stream(file_path: str, request: Request):
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Audio file not found")

    file_size = os.stat(file_path).st_size
    range_header = request.headers.get("range")

    start, end = 0, file_size - 1
    if range_header:
        try:
            h_range = range_header.replace("bytes=", "").split("-")
            if h_range[0]:
                start = int(h_range[0])
            if h_range[1]:
                end = int(h_range[1])
            if end >= file_size:
                end = file_size - 1
        except (ValueError, IndexError):
            pass

    chunk_size = (end - start) + 1
    
    def file_iterator():
        with open(file_path, "rb") as f:
            f.seek(start)
            bytes_left = chunk_size
            while bytes_left > 0:
                to_read = min(bytes_left, settings.CHUNK_SIZE)
                data = f.read(to_read)
                if not data:
                    break
                yield data
                bytes_left -= len(data)

    return StreamingResponse(
        file_iterator(),
        status_code=206, 
        headers={
            "Content-Range": f"bytes {start}-{end}/{file_size}",
            "Accept-Ranges": "bytes",
            "Content-Length": str(chunk_size),
            "Content-Type": "audio/mpeg",
            "Cache-Control": "no-cache",
            "Access-Control-Allow-Origin": "*",
        },
    )
