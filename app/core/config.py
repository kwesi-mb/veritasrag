from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "VeritasRAG"
    debug: bool = False

    database_url: str

    embedding_model: str = "BAAI/bge-base-en-v1.5"
    embedding_dimension: int = 768

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore", 
    )

@lru_cache
def get_settings() -> Settings:
    return Settings()

settings = get_settings()