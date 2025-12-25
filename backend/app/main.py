"""Main FastAPI application - wires everything together."""
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import settings
from app.core.errors import (
    general_exception_handler,
    http_exception_handler,
    validation_exception_handler,
)
from app.core.lifecycle import shutdown, startup
from app.core.middleware import RequestIDMiddleware
from app.modules.example import router as example_router
from app.modules.transcripts.router import router as transcripts_router
from app.modules.projects.router import router as projects_router
from app.modules.autonomy_guard.router import router as autonomy_router
from app.modules.record.router import router as record_router
from app.modules.console.router import router as console_router
from app.modules.privacy_shield.router import router as privacy_shield_router
from app.modules.draft.router import router as draft_router
from app.routers import health, meta, ready

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add custom middleware (request ID, timing, security headers)
app.add_middleware(RequestIDMiddleware)

# Include core routers
app.include_router(health.router, tags=["health"])
app.include_router(ready.router, tags=["readiness"])

# Conditional meta router
if settings.enable_meta:
    app.include_router(meta.router, tags=["meta"])

# Include modules
app.include_router(example_router.router, prefix="/api/v1", tags=["modules"])
app.include_router(transcripts_router, prefix="/api/v1/transcripts", tags=["transcripts"])
app.include_router(projects_router, prefix="/api/v1/projects", tags=["projects"])
app.include_router(autonomy_router, prefix="/api/v1/autonomy", tags=["autonomy"])
app.include_router(record_router, prefix="/api/v1/record", tags=["record"])
app.include_router(console_router, prefix="/api/v1", tags=["console"])
app.include_router(privacy_shield_router, prefix="/api/v1/privacy", tags=["privacy"])
app.include_router(draft_router, prefix="/api/v1", tags=["draft"])

# Register global exception handlers
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Lifecycle hooks
@app.on_event("startup")
async def startup_event() -> None:
    """Startup event handler."""
    await startup()


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Shutdown event handler."""
    await shutdown()
