from datetime import timedelta

import jwt
import pytest

from app.core.config import settings
from app.core.security import (
    ALGORITHM,
    TokenExpiredError,
    TokenInvalidError,
    create_access_token,
    decode_access_token,
    decode_token,
)


def test_token_roundtrip():
    token = create_access_token("usuario-demo")
    assert decode_access_token(token) == "usuario-demo"


def test_token_contains_standard_claims():
    payload = decode_token(create_access_token("u1"))
    assert {"sub", "iat", "exp", "jti", "type"} <= payload.keys()
    assert payload["type"] == "access"


def test_tokens_have_unique_jti():
    a = decode_token(create_access_token("u1"))["jti"]
    b = decode_token(create_access_token("u1"))["jti"]
    assert a != b


def test_invalid_token():
    assert decode_access_token("token-invalido") is None


def test_expired_token():
    token = create_access_token("u1", expires_delta=timedelta(seconds=-5))
    with pytest.raises(TokenExpiredError):
        decode_token(token)
    assert decode_access_token(token) is None


def test_tampered_signature_is_rejected():
    token = create_access_token("u1")
    assert decode_access_token(token[:-2] + "xx") is None


def test_token_signed_with_other_key_is_rejected():
    forged = jwt.encode(
        {"sub": "admin", "iat": 1, "exp": 9999999999, "jti": "x", "type": "access"},
        "change-this-secret-key",
        algorithm=ALGORITHM,
    )
    assert decode_access_token(forged) is None


def test_alg_none_is_rejected():
    forged = jwt.encode(
        {"sub": "admin", "exp": 9999999999, "iat": 1, "jti": "x", "type": "access"},
        key=None,
        algorithm="none",
    )
    assert decode_access_token(forged) is None


def test_wrong_token_type_is_rejected():
    token = jwt.encode(
        {"sub": "u1", "iat": 1, "exp": 9999999999, "jti": "x", "type": "refresh"},
        settings.SECRET_KEY,
        algorithm=ALGORITHM,
    )
    with pytest.raises(TokenInvalidError):
        decode_token(token)


def test_missing_sub_is_rejected():
    token = jwt.encode(
        {"iat": 1, "exp": 9999999999, "jti": "x", "type": "access"},
        settings.SECRET_KEY,
        algorithm=ALGORITHM,
    )
    assert decode_access_token(token) is None
