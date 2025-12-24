"""Readiness endpoint - returns 200/503 based on DB status."""
from fastapi import APIRouter, HTTPException

from app.core.config import settings
from app.core.database import check_db_health

router = APIRouter()


@router.get("/ready")
async def ready() -> dict:
    """Readiness check endpoint.

    Returns:
        200 if DB is OK (or no DB required)
        503 if DB is down (when DATABASE_URL is set)

    Raises:
        HTTPException: 503 if DB is configured but down
    """
    if settings.database_url:
        is_healthy = await check_db_health()
        if is_healthy:
            return {"status": "ready"}
        else:
            raise HTTPException(
                status_code=503,
                detail={"status": "db_down", "message": "Database health check failed"},
            )

    return {"status": "ready", "db": "not_configured"}

