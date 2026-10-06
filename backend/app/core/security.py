import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt

from app.core.config import settings

ALGORITHM = "HS256"
ACCESS_TOKEN_TYPE = "access"


class TokenError(Exception):
    """Error base al validar un token."""


class TokenExpiredError(TokenError):
    """El token es válido pero ya expiró."""


class TokenInvalidError(TokenError):
    """El token está mal formado, manipulado o no cumple los claims."""


def create_access_token(
    subject: str,
    *,
    expires_delta: timedelta | None = None,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    now = datetime.now(timezone.utc)
    expire = now + (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    payload: dict[str, Any] = {
        **(extra_claims or {}),
        "sub": subject,
        "iat": now,
        "exp": expire,
        "jti": uuid.uuid4().hex,
        "type": ACCESS_TOKEN_TYPE,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str, expected_type: str = ACCESS_TOKEN_TYPE) -> dict[str, Any]:
    """Valida firma, expiración y claims. Lanza TokenError si algo falla."""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[ALGORITHM],
            options={"require": ["exp", "iat", "sub", "jti"]},
        )
    except jwt.ExpiredSignatureError as exc:
        raise TokenExpiredError("El token ha expirado") from exc
    except jwt.InvalidTokenError as exc:
        raise TokenInvalidError("Token inválido") from exc

    if payload.get("type") != expected_type:
        raise TokenInvalidError("Tipo de token incorrecto")
    if not payload["sub"]:
        raise TokenInvalidError("Token sin sujeto")
    return payload


def decode_access_token(token: str) -> str | None:
    """Atajo: devuelve el subject o None si el token no es válido."""
    try:
        return str(decode_token(token)["sub"])
    except TokenError:
        return None
