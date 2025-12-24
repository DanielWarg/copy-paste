"""Export download endpoint - streams ZIP files to client.

This endpoint allows clients to download export ZIPs by package_id.
ZIP files are stored in /app/data/export-{package_id}.zip.
"""
from pathlib import Path
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse

from app.core.logging import logger

router = APIRouter()


@router.get("/export/{package_id}/download")
async def download_export(package_id: str):
    """Download export ZIP file by package_id.
    
    Args:
        package_id: Export package ID (UUID from export endpoint)
        
    Returns:
        ZIP file as FileResponse with Content-Type: application/zip
    """
    # Construct ZIP file path
    zip_path = Path("/app/data") / f"export-{package_id}.zip"
    
    # Check if file exists
    if not zip_path.exists():
        logger.warning("export_download_not_found", extra={"package_id": package_id})
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Export file not found",
        )
    
    # Return file with proper content type
    logger.info("export_download", extra={"package_id": package_id})
    return FileResponse(
        path=str(zip_path),
        media_type="application/zip",
        filename=f"export-{package_id}.zip",
    )

