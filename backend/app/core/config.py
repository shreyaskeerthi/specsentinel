"""Application configuration."""

from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "SpecSentinel"
    ENV: str = "dev"
    DEBUG: bool = True

    # SQLite database
    DATABASE_URL: str = "sqlite:///./specsentinel.db"

    # JWT Auth
    SECRET_KEY: str = "specsentinel-demo-secret-key-change-in-prod"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # File Storage
    FILE_STORAGE_PATH: str = "./uploads"
    MAX_FILE_SIZE_MB: int = 50

    # Anthropic API
    ANTHROPIC_API_KEY: str = ""
    USE_LLM_EXTRACTION: bool = True

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
