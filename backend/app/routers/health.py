"""Health check endpoint - always returns 200 if process is alive."""
from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health() -> dict:
    """Health check endpoint.

    Returns:
        {"status": "ok"} - Always 200 if process is alive
    """
    return {"status": "ok"}

