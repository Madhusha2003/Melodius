from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import models
from database import engine
from api.routes import tracks
from core.config import settings
from core.logger import setup_logging, logger

# Initialize logging
setup_logging()

# Initialize database
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="Backend API for Melodius Music Player"
)

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(tracks.router)

@app.on_event("startup")
def startup_event():
    logger.info(f"--- {settings.PROJECT_NAME} Started ---")
    logger.info("Database connected successfully.")

@app.get("/", tags=["health"])
def read_root():
    return {
        "app": settings.PROJECT_NAME,
        "status": "healthy",
        "version": "1.0.0"
    }