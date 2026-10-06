from app.core.config import settings


def test_root(client):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert data["version"] == settings.APP_VERSION


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_api_status(client):
    response = client.get("/api/v1/status")
    assert response.status_code == 200
    assert response.json()["api"] == "v1"


def test_module_routes_are_not_duplicated(client):
    paths = client.get("/openapi.json").json()["paths"]
    assert "/api/v1/auth/status" in paths
    assert "/api/v1/secop/status" in paths
    assert client.get("/api/v1/auth/status").json()["module"] == "auth"
    assert client.get("/api/v1/secop/status").json()["module"] == "secop"
