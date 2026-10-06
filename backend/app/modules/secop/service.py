import json
from collections.abc import Callable
from datetime import datetime
from typing import Any

from app.core.cache import TTLCache
from app.core.exceptions import AppException, NotFoundError
from app.modules.secop import constants as c
from app.modules.secop.client import SecopClient
from app.modules.secop.mapper import now_colombia, to_detalle, to_resumen
from app.modules.secop.query import build_detail_params, build_list_params
from app.modules.secop.schemas import (
    ID_PROCESO_RE,
    ProcesoDetalle,
    ProcesoFiltros,
    ProcesosPage,
)


class SecopService:
    def __init__(
        self,
        client: SecopClient,
        *,
        dataset: str,
        cache_ttl: float = 300,
        clock: Callable[[], datetime] = now_colombia,
        cache: TTLCache[list[dict[str, Any]]] | None = None,
    ):
        self._client = client
        self._dataset = dataset
        self._clock = clock
        self._cache = cache if cache is not None else TTLCache(cache_ttl)

    async def aclose(self) -> None:
        await self._client.aclose()

    async def _fetch(self, params: dict[str, str]) -> list[dict[str, Any]]:
        key = json.dumps(params, sort_keys=True)
        cached = self._cache.get(key)
        if cached is not None:
            return cached
        rows = await self._client.query(self._dataset, params)
        self._cache.set(key, rows)
        return rows

    async def buscar(self, filtros: ProcesoFiltros) -> ProcesosPage:
        now = self._clock()
        today = now.date()
        rows = await self._fetch(build_list_params(filtros, today))

        # El dataset puede traer el mismo proceso repetido: se conserva la
        # primera aparición (la más relevante según el orden pedido).
        seen: set[str] = set()
        items = []
        for row in rows:
            pid = row.get(c.COL_ID)
            if not pid or pid in seen:
                continue
            seen.add(pid)
            items.append(to_resumen(row, today))

        return ProcesosPage(
            items=items,
            limit=filtros.limit,
            offset=filtros.offset,
            count=len(items),
            has_more=len(rows) >= filtros.limit,
            fuente=c.FUENTE,
            consultado_en=now,
        )

    async def obtener(self, id_proceso: str) -> ProcesoDetalle:
        if not ID_PROCESO_RE.match(id_proceso):
            raise AppException("Identificador de proceso inválido", 422)
        today = self._clock().date()
        rows = await self._fetch(build_detail_params(id_proceso))
        if not rows:
            raise NotFoundError(f"No se encontró el proceso {id_proceso}")
        return to_detalle(rows[0], today)
