import secrets
import warnings
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]

_WEAK_SECRETS = {"", "change-this-secret-key", "changeme", "secret"}
_MIN_SECRET_LENGTH = 32


class Settings(BaseSettings):
    APP_NAME: str = "SECOP Intelligence API"
    APP_DESCRIPTION: str = (
        "Backend de inteligencia y gestión para empresas "
        "que contratan con el Estado."
    )
    APP_VERSION: str = "0.1.0"
    API_PREFIX: str = "/api/v1"

    ENVIRONMENT: Literal["development", "testing", "production"] = "development"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # Obligatoria en producción. En desarrollo/testing, si falta o es débil,
    # se genera una clave aleatoria por proceso (los tokens dejan de ser
    # válidos al reiniciar).
    SECRET_KEY: str = ""
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Lista JSON, p. ej. ["http://localhost:3000"]
    CORS_ORIGINS: list[str] = []

    SECOP_API_BASE_URL: str = "https://www.datos.gov.co/resource"
    SECOP_API_TIMEOUT: int = 30
    # Token de aplicación de Socrata (opcional, evita throttling agresivo).
    SECOP_APP_TOKEN: str = ""
    # SECOP II - Procesos de Contratación (datos.gov.co)
    SECOP_PROCESOS_DATASET: str = "p6dx-8zbt"
    SECOP_MAX_RETRIES: int = 3
    SECOP_CACHE_TTL_SECONDS: int = 300
    # None => se exige autenticación solo en producción.
    SECOP_REQUIRE_AUTH: bool | None = None

    AI_PROVIDER: str = "none"
    AI_API_KEY: str = ""

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @property
    def secop_auth_required(self) -> bool:
        if self.SECOP_REQUIRE_AUTH is None:
            return self.is_production
        return self.SECOP_REQUIRE_AUTH

    @property
    def docs_enabled(self) -> bool:
        """Swagger/ReDoc/OpenAPI solo fuera de producción."""
        return not self.is_production

    @model_validator(mode="after")
    def _validate_secret_key(self) -> "Settings":
        is_weak = (
            self.SECRET_KEY in _WEAK_SECRETS
            or len(self.SECRET_KEY) < _MIN_SECRET_LENGTH
        )
        if not is_weak:
            return self

        if self.is_production:
            raise ValueError(
                "SECRET_KEY es obligatoria en producción y debe tener al "
                f"menos {_MIN_SECRET_LENGTH} caracteres. Genera una con: "
                'python -c "import secrets; print(secrets.token_urlsafe(48))"'
            )

        warnings.warn(
            "SECRET_KEY ausente o débil: se usa una clave aleatoria temporal. "
            "Define SECRET_KEY en .env para sesiones estables.",
            stacklevel=2,
        )
        self.SECRET_KEY = secrets.token_urlsafe(48)
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
