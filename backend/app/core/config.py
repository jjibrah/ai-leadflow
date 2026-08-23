from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    APP_NAME: str
    APP_ENV: str
    DATABASE_URL: str
    FRONTEND_URL: str
    REDIS_URL: str
    JWT_SECRET_KEY: str
    WEBHOOK_SECRET: str
    OPENAI_API_KEY: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()