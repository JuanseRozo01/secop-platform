import pytest
from pydantic import ValidationError

from app.core.config import Settings

STRONG = "a-very-strong-secret-key-with-more-than-32-chars"


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    """Evita que variables de entorno (p. ej. del conftest) afecten estos tests."""
    for var in ("SECRET_KEY", "ENVIRONMENT", "DEBUG"):
        monkeypatch.delenv(var, raising=False)


def make(**kwargs) -> Settings:
    return Settings(_env_file=None, **kwargs)


def test_production_requires_secret_key():
    with pytest.raises(ValidationError):
        make(ENVIRONMENT="production")


@pytest.mark.parametrize("weak", ["change-this-secret-key", "short", ""])
def test_production_rejects_weak_secret(weak):
    with pytest.raises(ValidationError):
        make(ENVIRONMENT="production", SECRET_KEY=weak)


def test_production_accepts_strong_secret_and_hides_docs():
    s = make(ENVIRONMENT="production", SECRET_KEY=STRONG)
    assert s.SECRET_KEY == STRONG
    assert s.docs_enabled is False


def test_development_generates_random_key_with_warning():
    with pytest.warns(UserWarning):
        a = make(ENVIRONMENT="development")
    with pytest.warns(UserWarning):
        b = make(ENVIRONMENT="development")
    assert len(a.SECRET_KEY) >= 32
    assert a.SECRET_KEY != b.SECRET_KEY
    assert a.docs_enabled is True


def test_debug_is_off_by_default():
    assert make(SECRET_KEY=STRONG).DEBUG is False
