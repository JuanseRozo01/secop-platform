def test_root(client):
    response = client.get("/")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "online"
    assert data["version"] == "0.1.0"


def test_health(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy"
    }


def test_api_status(client):
    response = client.get("/api/v1/status")

    assert response.status_code == 200
    assert response.json()["api"] == "v1"