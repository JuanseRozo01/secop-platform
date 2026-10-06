from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.exceptions import UnauthorizedError
from app.core.security import TokenExpiredError, TokenInvalidError, decode_token

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_subject(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> str:
    """Devuelve el `sub` del access token o responde 401."""
    if credentials is None:
        raise UnauthorizedError("Falta el token de autenticación")
    try:
        return str(decode_token(credentials.credentials)["sub"])
    except TokenExpiredError:
        raise UnauthorizedError("El token ha expirado") from None
    except TokenInvalidError:
        raise UnauthorizedError("Token inválido") from None
