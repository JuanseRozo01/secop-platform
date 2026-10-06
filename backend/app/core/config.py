from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "SECOP Intelligence API"

    APP_DESCRIPTION: str = (
        "Backend de inteligencia y gestión para empresas "
        "que contratan con el Estado."
    )

    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True
    API_PREFIX: str = "/api/v1"

    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"

    SECRET_KEY: str = "change-this-secret-key"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    SECOP_API_BASE_URL: str = "https://www.datos.gov.co/resource"
    SECOP_API_TIMEOUT: int = 30

    AI_PROVIDER: str = "none"
    AI_API_KEY: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()