from fastapi import APIRouter

from app.modules.ai.router import router as ai_router
from app.modules.alerts.router import router as alerts_router
from app.modules.analytics.router import router as analytics_router
from app.modules.auth.router import router as auth_router
from app.modules.companies.router import router as companies_router
from app.modules.contracts.router import router as contracts_router
from app.modules.documents.router import router as documents_router
from app.modules.lawyers.router import router as lawyers_router
from app.modules.matching.router import router as matching_router
from app.modules.opportunities.router import router as opportunities_router
from app.modules.secop.router import router as secop_router
from app.modules.users.router import router as users_router


router = APIRouter()

router.include_router(auth_router)
router.include_router(users_router)
router.include_router(companies_router)
router.include_router(secop_router)
router.include_router(opportunities_router)
router.include_router(matching_router)
router.include_router(alerts_router)
router.include_router(documents_router)
router.include_router(ai_router)
router.include_router(analytics_router)
router.include_router(contracts_router)
router.include_router(lawyers_router)


@router.get("/status", tags=["System"])
async def api_status() -> dict[str, str]:
    return {
        "api": "v1",
        "status": "online",
    }