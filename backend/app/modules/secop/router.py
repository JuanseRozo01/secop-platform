from fastapi import APIRouter

router = APIRouter(prefix="/secop", tags=["secop"])


@router.get("/status")
async def status() -> dict[str, str]:
    return {"module": "secop", "status": "ready"}
