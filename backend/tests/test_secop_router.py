import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.security import create_access_token
from app.main import app
from app.modules.secop.deps import get_secop_service
from app.modules.secop.exceptions import SecopUnavailableError
from app.modules.secop.service import SecopService
from tests.secop_fixtures import AHORA, fila_directa, fila_vigente


class FakeClient:
    def __init__(self, rows=None, error=None):
        self.rows, self.error, self.calls = rows or [], error, []

    async def query(self, dataset, params):
        self.calls.append(params)
        if self.error:
            raise self.error
        return self.rows

    async def aclose(self):
        pass


@pytest.fixture
def make_client():
    def _make(rows=None, error=None):
        fake = FakeClient(rows, error)
        service = SecopService(fake, dataset="p6dx-8zbt", clock=lambda: AHORA, cache_ttl=0)
        app.dependency_overrides[get_secop_service] = lambda: service
        return TestClient(app, raise_server_exceptions=False), fake

    yield _make
    app.dependency_overrides.clear()


def test_status_is_public(client):
    r = client.get("/api/v1/secop/status")
    assert r.status_code == 200
    assert r.json()["dataset"] == "p6dx-8zbt"


def test_catalogos(make_client):
    c, _ = make_client()
    data = c.get("/api/v1/secop/catalogos").json()
    assert "Mínima cuantía" in data["modalidades"]
    assert data["ordenes"] == ["publicacion", "cierre", "valor"]


def test_buscar_procesos_ok_and_params_forwarded(make_client):
    c, fake = make_client([fila_vigente(), fila_directa()])
    r = c.get(
        "/api/v1/secop/procesos",
        params={"q": "obra", "departamento": "Cauca", "unspsc": "7210", "limit": 2,
                "orden": "cierre"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["count"] == 2 and body["has_more"] is True
    assert body["items"][0]["vigente"] is True
    assert body["items"][1]["vigente"] is False
    sent = fake.calls[0]
    assert sent["$q"] == "obra" and sent["$limit"] == "2"
    assert "CAUCA" in sent["$where"] and "V1.7210%" in sent["$where"]


@pytest.mark.parametrize(
    "params",
    [
        {"unspsc": "abc"},
        {"limit": 1000},
        {"orden": "random"},
        {"precio_min": 10, "precio_max": 5},
        {"q": "a"},
        {"nit_entidad": "xx"},
    ],
)
def test_invalid_filters_return_422_uniform_format(make_client, params):
    c, fake = make_client()
    r = c.get("/api/v1/secop/procesos", params=params)
    assert r.status_code == 422
    assert r.json()["error"] in {"AppException", "ValidationError"}
    assert fake.calls == []


def test_detalle_ok_404_and_422(make_client):
    c, _ = make_client([fila_vigente()])
    assert c.get("/api/v1/secop/procesos/CO1.REQ.11069913").json()["descripcion"]
    c, _ = make_client([])
    assert c.get("/api/v1/secop/procesos/CO1.REQ.1").status_code == 404
    assert c.get("/api/v1/secop/procesos/a%20b").status_code == 422


def test_upstream_down_maps_to_503_with_uniform_error(make_client):
    c, _ = make_client(error=SecopUnavailableError())
    r = c.get("/api/v1/secop/procesos")
    assert r.status_code == 503
    assert r.json()["error"] == "SecopUnavailableError"


def test_auth_required_when_enabled(make_client, monkeypatch):
    c, _ = make_client([fila_vigente()])
    monkeypatch.setattr(settings, "SECOP_REQUIRE_AUTH", True)
    assert c.get("/api/v1/secop/procesos").status_code == 401
    assert c.get("/api/v1/secop/status").status_code == 200  # status sigue público
    token = create_access_token("empresa-1")
    ok = c.get("/api/v1/secop/procesos", headers={"Authorization": f"Bearer {token}"})
    assert ok.status_code == 200


def test_auth_default_follows_environment(monkeypatch):
    monkeypatch.setattr(settings, "SECOP_REQUIRE_AUTH", None)
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    assert settings.secop_auth_required is True
    monkeypatch.setattr(settings, "ENVIRONMENT", "development")
    assert settings.secop_auth_required is False
