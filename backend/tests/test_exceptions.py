from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel

from app.core.exceptions import (
    NotFoundError,
    register_exception_handlers,
)


class Item(BaseModel):
    name: str


def build_app() -> TestClient:
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/boom")
    async def boom():
        raise RuntimeError("secreto interno")

    @app.get("/missing")
    async def missing():
        raise NotFoundError("No existe")

    @app.post("/items")
    async def create(item: Item):
        return item

    return TestClient(app, raise_server_exceptions=False)


def test_unhandled_error_hides_details_and_returns_error_id():
    response = build_app().get("/boom")
    assert response.status_code == 500
    body = response.json()
    assert body["error"] == "InternalServerError"
    assert body["error_id"]
    assert "secreto" not in response.text


def test_app_exception_format():
    response = build_app().get("/missing")
    assert response.status_code == 404
    assert response.json()["message"] == "No existe"


def test_validation_error_uses_uniform_format():
    response = build_app().post("/items", json={})
    assert response.status_code == 422
    body = response.json()
    assert body["error"] == "ValidationError"
    assert body["details"]
