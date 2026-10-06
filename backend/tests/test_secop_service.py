import pytest

from app.core.exceptions import AppException, NotFoundError
from app.modules.secop.schemas import ProcesoFiltros
from app.modules.secop.service import SecopService
from tests.secop_fixtures import AHORA, fila_directa, fila_vigente

pytestmark = pytest.mark.anyio


class FakeClient:
    def __init__(self, rows):
        self.rows = rows
        self.calls: list[tuple[str, dict]] = []

    async def query(self, dataset, params):
        self.calls.append((dataset, params))
        return self.rows

    async def aclose(self):
        pass


def make_service(rows, **kw):
    fake = FakeClient(rows)
    return SecopService(fake, dataset="p6dx-8zbt", clock=lambda: AHORA, **kw), fake


async def test_buscar_maps_dedupes_and_reports_pagination():
    rows = [fila_vigente(), fila_vigente(), fila_directa()]
    service, fake = make_service(rows)
    page = await service.buscar(ProcesoFiltros(limit=3))
    assert page.count == 2  # duplicado eliminado
    assert [p.id_proceso for p in page.items] == ["CO1.REQ.11069913", "CO1.REQ.9845111"]
    assert page.has_more is True  # 3 filas == limit
    assert page.fuente.startswith("SECOP II")
    assert fake.calls[0][0] == "p6dx-8zbt"
    assert page.items[0].dias_para_cierre == 3


async def test_buscar_has_more_false_on_short_page():
    service, _ = make_service([fila_vigente()])
    page = await service.buscar(ProcesoFiltros(limit=20))
    assert page.has_more is False


async def test_buscar_skips_rows_without_id():
    service, _ = make_service([{"entidad": "sin id"}, fila_vigente()])
    page = await service.buscar(ProcesoFiltros())
    assert page.count == 1


async def test_identical_queries_hit_cache_but_different_ones_do_not():
    service, fake = make_service([fila_vigente()], cache_ttl=60)
    await service.buscar(ProcesoFiltros())
    await service.buscar(ProcesoFiltros())
    assert len(fake.calls) == 1
    await service.buscar(ProcesoFiltros(q="obra"))
    assert len(fake.calls) == 2


async def test_cache_disabled_when_ttl_zero():
    service, fake = make_service([fila_vigente()], cache_ttl=0)
    await service.buscar(ProcesoFiltros())
    await service.buscar(ProcesoFiltros())
    assert len(fake.calls) == 2


async def test_obtener_returns_detail():
    service, _ = make_service([fila_vigente()])
    d = await service.obtener("CO1.REQ.11069913")
    assert d.descripcion and d.vigente


async def test_obtener_not_found():
    service, _ = make_service([])
    with pytest.raises(NotFoundError):
        await service.obtener("CO1.REQ.999")


@pytest.mark.parametrize("bad", ["a b", "x'; drop", "", "ab", "x" * 65])
async def test_obtener_rejects_malformed_ids_without_querying(bad):
    service, fake = make_service([fila_vigente()])
    with pytest.raises(AppException) as exc:
        await service.obtener(bad)
    assert exc.value.status_code == 422
    assert fake.calls == []
