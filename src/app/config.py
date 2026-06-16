from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_uri: str = 'sqlite:///:memory:'

    model_config = SettingsConfigDict(env_file='.env', extra='ignore')
