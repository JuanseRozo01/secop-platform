from app.core.security import (
    create_access_token,
    decode_access_token,
)


def test_token_roundtrip():

    token = create_access_token(
        "usuario-demo"
    )

    assert decode_access_token(token) == "usuario-demo"


def test_invalid_token():

    assert decode_access_token(
        "token-invalido"
    ) is None