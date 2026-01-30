"""
Application settings using Pydantic Settings.
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings."""
    
    # API Settings
    api_title: str = "Nepal House of Representatives Election Data API"
    api_version: str = "1.0.0"
    api_prefix: str = "/api/v1"
    
    # Server Settings
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = False
    
    # Data Settings
    data_dir: str = "data"
    elections_dir: str = "data/elections"
    
    # Validation Settings
    strict_validation: bool = False  # If True, fail on missing required columns
    log_warnings: bool = True  # Log warnings for missing optional columns
    
    # CORS Settings (use specific origins when allow_credentials=True; "*" is rejected by browsers)
    cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:5173", "http://127.0.0.1:5173"]
    cors_allow_credentials: bool = True
    cors_allow_methods: list[str] = ["*"]
    cors_allow_headers: list[str] = ["*"]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()
