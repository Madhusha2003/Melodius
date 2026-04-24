from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

class Settings(BaseSettings):
    PROJECT_NAME: str = "Melodius API"
    DATABASE_URL: str = "sqlite:///./melodius.db"
    CORS_ORIGINS: List[str] = ["*"]
    
    # Audio streaming settings
    CHUNK_SIZE: int = 128 * 1024  # 128KB
    
    # Logging
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )

settings = Settings()
