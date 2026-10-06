from app.core.exceptions import AppException


class SecopUnavailableError(AppException):
    """datos.gov.co no respondió (red, timeout, 429 o 5xx tras reintentos)."""

    def __init__(self, message: str = "El servicio de datos del SECOP no está disponible"):
        super().__init__(message, 503)


class SecopBadResponseError(AppException):
    """Respuesta inesperada de datos.gov.co (4xx o formato no válido)."""

    def __init__(self, message: str = "Respuesta inválida del servicio de datos del SECOP"):
        super().__init__(message, 502)
