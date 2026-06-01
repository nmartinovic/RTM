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
    rtm_api_key: str = Field(default="", alias="RTM_API_KEY")
    rtm_shared_secret: str = Field(default="", alias="RTM_SHARED_SECRET")
    rtm_perms: str = Field(default="read", alias="RTM_PERMS")
    rtm_auth_url: str = Field(default="https://www.rememberthemilk.com/services/auth/", alias="RTM_AUTH_URL")
    rtm_rest_url: str = Field(default="https://api.rememberthemilk.com/services/rest/", alias="RTM_REST_URL")
    rtm_request_timeout_seconds: float = Field(default=10.0, alias="RTM_REQUEST_TIMEOUT_SECONDS")
    rtm_token_store_path: str = Field(default="local-data/rtm-token.json", alias="RTM_TOKEN_STORE_PATH")


@lru_cache
def get_settings() -> Settings:
    return Settings()
