"""Meta endpoint - version/build info (optional, behind ENABLE_META flag)."""
import os

from fastapi import APIRouter

from app.core.config import settings

router = APIRouter()


@router.get("/meta")
async def meta() -> dict:
    """Meta information endpoint.

    Returns:
        Version, build, and commit information
    """
    return {
        "version": settings.app_version,
        "build": os.getenv("BUILD_ID", "local"),
        "commit": os.getenv("GIT_COMMIT", "unknown"),
    }

