"""Readiness endpoint - returns 200/503 based on DB status."""
from fastapi import APIRouter, HTTPException, status

from app.core.config import settings
from app.core.database import check_db_health, engine

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
        if not engine:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "status": "db_uninitialized",
                    "message": "Database engine not initialized",
                    "reason": "Database connection not established during startup"
                },
            )
        
        is_healthy = await check_db_health()
        if is_healthy:
            return {"status": "ready", "db": "connected"}
        else:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "status": "db_down",
                    "message": "Database health check failed",
                    "reason": "Database connection timeout or connection refused"
                },
            )

    return {"status": "ready", "db": "not_configured"}

