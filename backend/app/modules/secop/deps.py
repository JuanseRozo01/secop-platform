from functools import lru_cache

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials

from app.core.config import settings
from app.core.deps import bearer_scheme, get_current_subject
from app.modules.secop.client import SecopClient
from app.modules.secop.service import SecopService


@lru_cache
def get_secop_service() -> SecopService:
    client = SecopClient(
        settings.SECOP_API_BASE_URL,
        timeout=settings.SECOP_API_TIMEOUT,
        app_token=settings.SECOP_APP_TOKEN or None,
        max_retries=settings.SECOP_MAX_RETRIES,
    )
    return SecopService(
        client,
        dataset=settings.SECOP_PROCESOS_DATASET,
        cache_ttl=settings.SECOP_CACHE_TTL_SECONDS,
    )


async def close_secop_service() -> None:
    if get_secop_service.cache_info().currsize:
        await get_secop_service().aclose()
        get_secop_service.cache_clear()


def secop_access(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> str | None:
    """Exige token solo si SECOP_REQUIRE_AUTH (por defecto: en producción)."""
    if not settings.secop_auth_required:
        return None
    return get_current_subject(credentials)
