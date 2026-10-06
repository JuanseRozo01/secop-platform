from fastapi import APIRouter, Depends

from app.core.deps import get_current_subject

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/status")
async def status() -> dict[str, str]:
    return {"module": "auth", "status": "ready"}


@router.get("/me")
async def me(subject: str = Depends(get_current_subject)) -> dict[str, str]:
    """Ruta protegida de ejemplo; luego devolverá el usuario real."""
    return {"subject": subject}
