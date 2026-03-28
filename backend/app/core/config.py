"""Application configuration using Pydantic settings."""

from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "SpecSentinel"
    ENV: str = "dev"
    DEBUG: bool = True

    # Database (psycopg3 uses postgresql+psycopg)
    DATABASE_URL: str = "postgresql+psycopg://specsentinel:specsentinel@localhost:5432/specsentinel"

    # Security
    SECRET_KEY: str = "change-this-in-production-use-openssl-rand-hex-32"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # File Storage
    FILE_STORAGE_PATH: str = "./uploads"
    MAX_FILE_SIZE_MB: int = 50

    # Stripe (TODO: integrate actual Stripe)
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""

    # Anthropic API
    ANTHROPIC_API_KEY: str = ""
    USE_LLM_EXTRACTION: bool = True  # Set to False to use regex-only

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
