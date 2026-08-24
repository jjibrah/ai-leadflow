from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    APP_NAME: str
    APP_ENV: str
    DATABASE_URL: str
    FRONTEND_URL: str
    REDIS_URL: str = "redis://localhost:6379/0"
    BACKGROUND_JOBS_ENABLED: bool = False
    JWT_SECRET_KEY: str
    WEBHOOK_SECRET: str
    AI_PROVIDER: Literal["gemini", "openai"] = "gemini"
    OPENAI_API_KEY: str | None = None
    OPENAI_MODEL: str = "gpt-4o-mini"
    GEMINI_API_KEY: str | None = None
    GEMINI_MODEL: str = "gemini-3.5-flash"
    AI_TIMEOUT_SECONDS: float = Field(default=25.0, gt=0, le=120)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()
