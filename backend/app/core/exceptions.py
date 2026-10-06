import logging
import uuid

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class AppException(Exception):
    def __init__(
        self,
        message: str,
        status_code: int = 400,
        headers: dict[str, str] | None = None,
    ):
        self.message = message
        self.status_code = status_code
        self.headers = headers
        super().__init__(message)


class UnauthorizedError(AppException):
    def __init__(self, message: str = "No autenticado"):
        super().__init__(
            message, 401, headers={"WWW-Authenticate": "Bearer"}
        )


class ForbiddenError(AppException):
    def __init__(self, message: str = "No tienes permisos para esta acción"):
        super().__init__(message, 403)


class NotFoundError(AppException):
    def __init__(self, message: str = "Recurso no encontrado"):
        super().__init__(message, 404)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppException)
    async def app_exception_handler(
        request: Request, exc: AppException
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            headers=exc.headers,
            content={
                "error": exc.__class__.__name__,
                "message": exc.message,
                "path": request.url.path,
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                "error": "ValidationError",
                "message": "Los datos enviados no son válidos",
                "details": jsonable_encoder(exc.errors()),
                "path": request.url.path,
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        error_id = uuid.uuid4().hex[:12]
        logger.exception(
            "Error no controlado [%s] en %s", error_id, request.url.path
        )
        return JSONResponse(
            status_code=500,
            content={
                "error": "InternalServerError",
                "message": "Ocurrió un error inesperado",
                "error_id": error_id,
                "path": request.url.path,
            },
        )
