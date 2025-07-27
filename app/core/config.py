import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    """
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str = "postgresql://user:password@localhost:5432/chivesave_db"
    SECRET_KEY: str = "your-super-secret-jwt-key-change-this-in-production!" # IMPORTANT: Change this in production!
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

@lru_cache()
def get_settings() -> Settings:
    """
    Cached function to get application settings.
    """
    return Settings()
