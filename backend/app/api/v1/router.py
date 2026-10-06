from fastapi import APIRouter

from app.modules.auth.router import router as auth_router
from app.modules.secop.router import router as secop_router

# Registra aquí cada módulo SOLO cuando exista su router:
# ai, alerts, analytics, companies, contracts, documents,
# lawyers, matching, opportunities, users.

router = APIRouter()

router.include_router(auth_router)
router.include_router(secop_router)


@router.get("/status", tags=["System"])
async def api_status() -> dict[str, str]:
    return {"api": "v1", "status": "online"}
