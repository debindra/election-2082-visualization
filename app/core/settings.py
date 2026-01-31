"""
Application settings using Pydantic Settings.
"""
from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import Optional, Union


def _parse_cors_origins(v: Union[str, list]) -> list[str]:
    """Parse CORS_ORIGINS from env: comma-separated string or list."""
    if isinstance(v, list):
        return [str(x).strip() for x in v if x and str(x).strip()]
    s = (v or "").strip()
    if not s:
        return []
    return [x.strip() for x in s.split(",") if x.strip()]


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
    # Set CORS_ORIGINS in .env for production, e.g. CORS_ORIGINS=https://your-domain.com,https://www.your-domain.com
    cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:5173", "http://127.0.0.1:5173"]
    cors_allow_credentials: bool = True
    cors_allow_methods: list[str] = ["*"]
    cors_allow_headers: list[str] = ["*"]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Optional[Union[str, list]]) -> Optional[Union[str, list]]:
        """Parse CORS_ORIGINS from env (comma-separated string)."""
        if v is None:
            return None
        if isinstance(v, str) and not v.strip():
            return None
        if isinstance(v, str):
            return _parse_cors_origins(v)
        if isinstance(v, list):
            return _parse_cors_origins(v)
        return v


# Global settings instance
settings = Settings()
