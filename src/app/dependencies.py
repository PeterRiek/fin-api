from functools import lru_cache

from app.config import Settings
from app.database import Database


@lru_cache
def get_settings() -> Settings:
    return Settings()


@lru_cache
def get_db() -> Database:
    settings = get_settings()
    return Database(settings.database_uri)
