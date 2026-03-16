from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    # App
    APP_NAME: str = "AI Field Technician Copilot"
    DEBUG: bool = False

    # Gemini
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-1.5-flash"  # Use flash for cost efficiency

    # Data
    DATA_DIR: str = os.path.join(os.path.dirname(__file__), "..", "data")

    # Cache
    CACHE_TTL_SECONDS: int = 300  # 5 minutes

    # LLM
    USE_MOCK_LLM: bool = False  # Set True in tests
    LLM_TIMEOUT_SECONDS: int = 30

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
