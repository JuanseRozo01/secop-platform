"""Pruebas contra datos.gov.co REAL. Se omiten por defecto.

    RUN_LIVE_TESTS=1 pytest -m live -s

Sirven para validar nombres de columnas, tipos (p. ej. precio_base numérico)
y el filtro de 'oportunidad vigente' con datos reales.
"""

import os

import pytest

from app.core.config import settings
from app.modules.secop.client import SecopClient
from app.modules.secop.mapper import now_colombia
from app.modules.secop.schemas import ProcesoFiltros
from app.modules.secop.service import SecopService

pytestmark = [
    pytest.mark.live,
    pytest.mark.anyio,
    pytest.mark.skipif(os.getenv("RUN_LIVE_TESTS") != "1", reason="RUN_LIVE_TESTS=1 requerido"),
]


@pytest.fixture
async def service():
    client = SecopClient(
        settings.SECOP_API_BASE_URL,
        timeout=60,
        app_token=settings.SECOP_APP_TOKEN or None,
    )
    yield SecopService(client, dataset=settings.SECOP_PROCESOS_DATASET, cache_ttl=0)
    await client.aclose()


async def test_vigentes_search_returns_valid_opportunities(service):
    page = await service.buscar(ProcesoFiltros(limit=20, orden="cierre"))
    print(f"\n{page.count} procesos vigentes; primero: ",
          page.items[0].model_dump(include={"id_proceso", "entidad", "modalidad",
                                            "fecha_cierre_ofertas"}) if page.items else None)
    today = now_colombia().date()
    for p in page.items:
        assert p.vigente, p.id_proceso
        assert p.modalidad and p.modalidad.lower() != "contratación directa"
        assert p.fecha_cierre_ofertas.date() >= today


async def test_price_filter_is_numeric(service):
    page = await service.buscar(
        ProcesoFiltros(solo_vigentes=False, precio_min=1_000_000_000, precio_max=2_000_000_000,
                       limit=10)
    )
    assert page.items, "sin resultados: ¿precio_base es texto en vez de número?"
    assert all(1_000_000_000 <= p.precio_base <= 2_000_000_000 for p in page.items)


async def test_unspsc_and_keyword_filters(service):
    page = await service.buscar(ProcesoFiltros(solo_vigentes=False, unspsc="80", q="servicios",
                                               limit=5))
    assert page.items


async def test_detail_roundtrip(service):
    page = await service.buscar(ProcesoFiltros(limit=1))
    assert page.items
    detalle = await service.obtener(page.items[0].id_proceso)
    assert detalle.id_proceso == page.items[0].id_proceso
