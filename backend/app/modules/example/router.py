"""Example module router - demonstrates Module Contract v1.

This module serves as a reference implementation showing:
- How to structure a module according to Module Contract v1
- Privacy-safe logging using core logging
- Simple endpoint without business logic
"""
from fastapi import APIRouter, Query

from app.core.logging import logger

router = APIRouter()


@router.get("/example")
async def example(q: str = Query(..., description="Required query parameter for testing")) -> dict:
    """Example endpoint demonstrating Module Contract v1.

    Args:
        q: Required query parameter (used for testing validation errors)

    Returns:
        Simple status response with module identifier
    """
    # Privacy-safe logging (no headers, no body, no PII)
    logger.info(
        "example_module_called",
        extra={
            "module": "example",
            "endpoint": "/api/v1/example",
        },
    )

    return {
        "status": "ok",
        "module": "example",
        "query": q,
    }

