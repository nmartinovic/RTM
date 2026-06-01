from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = Field(default="development", alias="APP_ENV")
    app_username: str = Field(default="admin", alias="APP_USERNAME")
    app_password: str = Field(default="change-me", alias="APP_PASSWORD")
    frontend_origin: str = Field(default="http://localhost:5173", alias="FRONTEND_ORIGIN")
    session_secret_key: str = Field(
        default="dev-session-secret-change-me",
        alias="SESSION_SECRET_KEY",
    )
    session_cookie_name: str = Field(default="rtm_session", alias="SESSION_COOKIE_NAME")
    session_cookie_secure: bool = Field(default=False, alias="SESSION_COOKIE_SECURE")
    session_ttl_seconds: int = Field(default=60 * 60 * 12, alias="SESSION_TTL_SECONDS")


@lru_cache
def get_settings() -> Settings:
    return Settings()
