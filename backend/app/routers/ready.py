"""Readiness endpoint - returns 200/503 based on DB status."""
from fastapi import APIRouter, HTTPException, status

from app.core.config import settings
from app.core.database import check_db_health

router = APIRouter()


@router.get("/ready")
def ready() -> dict:
    """Readiness check endpoint.

    Returns:
        200 if DB is OK (or no DB required)
        503 if DB is down (when DATABASE_URL is set)

    Raises:
        HTTPException: 503 if DB is configured but down
    """
    if settings.database_url:
        # Import engine at runtime to get current value (not cached import)
        from app.core.database import engine
        if not engine:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "status": "db_uninitialized",
                    "message": "Database engine not initialized",
                    "reason": "Database connection not established during startup"
                },
            )
        
        # Use sync check directly - it's fast enough (0.002-0.005s)
        from app.core.database import _check_db_health_sync
        try:
            is_healthy = _check_db_health_sync()
        except Exception:
            is_healthy = False
        
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

