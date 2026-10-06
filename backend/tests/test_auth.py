from datetime import timedelta

from app.core.security import create_access_token


def test_me_without_token_returns_401(client):
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"
    assert response.json()["error"] == "UnauthorizedError"


def test_me_with_valid_token(client):
    token = create_access_token("usuario-demo")
    response = client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json() == {"subject": "usuario-demo"}


def test_me_with_expired_token(client):
    token = create_access_token("u1", expires_delta=timedelta(seconds=-5))
    response = client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 401
    assert "expirado" in response.json()["message"]


def test_me_with_garbage_token(client):
    response = client.get(
        "/api/v1/auth/me", headers={"Authorization": "Bearer basura"}
    )
    assert response.status_code == 401
