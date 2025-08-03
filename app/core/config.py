from __future__ import annotations

from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str
    API_URL: str
    GEMINI_API_KEY: str
    EMBEDDING_MODEL: str
    LLM_MODEL: str

    model_config = SettingsConfigDict(env_file='.env')


settings = Settings()
