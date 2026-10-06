"""Cliente asíncrono de la API Socrata (SODA) de datos.gov.co."""

import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import Any

import httpx

from app.modules.secop.exceptions import SecopBadResponseError, SecopUnavailableError

logger = logging.getLogger(__name__)

RETRYABLE_STATUS = {429, 500, 502, 503, 504}
MAX_RETRY_AFTER = 10.0


class SecopClient:
    def __init__(
        self,
        base_url: str,
        *,
        timeout: float = 30.0,
        app_token: str | None = None,
        max_retries: int = 3,
        backoff: float = 0.5,
        transport: httpx.AsyncBaseTransport | None = None,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    ):
        headers = {"Accept": "application/json"}
        if app_token:
            headers["X-App-Token"] = app_token
        self._base_url = base_url.rstrip("/")
        self._max_retries = max(0, max_retries)
        self._backoff = backoff
        self._sleep = sleep
        self._http = httpx.AsyncClient(
            timeout=timeout, headers=headers, transport=transport
        )

    async def aclose(self) -> None:
        await self._http.aclose()

    @staticmethod
    def _retry_after(response: httpx.Response) -> float | None:
        raw = response.headers.get("Retry-After")
        if raw and raw.strip().isdigit():
            return min(float(raw.strip()), MAX_RETRY_AFTER)
        return None

    async def query(self, dataset_id: str, params: dict[str, str]) -> list[dict[str, Any]]:
        url = f"{self._base_url}/{dataset_id}.json"
        last_error = "sin detalle"

        for attempt in range(self._max_retries + 1):
            delay = self._backoff * (2**attempt)
            try:
                response = await self._http.get(url, params=params)
            except httpx.TransportError as exc:
                last_error = f"{type(exc).__name__}"
            else:
                status = response.status_code
                if status in RETRYABLE_STATUS:
                    last_error = f"HTTP {status}"
                    delay = self._retry_after(response) or delay
                elif status >= 400:
                    logger.error(
                        "SECOP respondió HTTP %s para %s: %s",
                        status, dataset_id, response.text[:300],
                    )
                    raise SecopBadResponseError(
                        f"datos.gov.co rechazó la consulta (HTTP {status})"
                    )
                else:
                    return self._parse(response)

            if attempt < self._max_retries:
                logger.warning(
                    "SECOP intento %d/%d falló (%s); reintento en %.1fs",
                    attempt + 1, self._max_retries + 1, last_error, delay,
                )
                await self._sleep(delay)

        logger.error("SECOP no disponible tras %d intentos: %s",
                     self._max_retries + 1, last_error)
        raise SecopUnavailableError()

    @staticmethod
    def _parse(response: httpx.Response) -> list[dict[str, Any]]:
        try:
            data = response.json()
        except ValueError as exc:
            raise SecopBadResponseError("datos.gov.co devolvió un JSON inválido") from exc
        if not isinstance(data, list):
            raise SecopBadResponseError("Formato de respuesta inesperado")
        return [row for row in data if isinstance(row, dict)]
