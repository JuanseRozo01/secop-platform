from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.loggings import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan,
)

register_exception_handlers(app)
app.include_router(api_router, prefix=settings.API_PREFIX)


@app.get("/", tags=["System"])
async def root() -> dict[str, str]:
    return {
        "message": settings.APP_NAME,
        "status": "online",
        "version": settings.APP_VERSION,
    }


@app.get("/health", tags=["System"])
async def health_check() -> dict[str, str]:
    return {"status": "healthy"}