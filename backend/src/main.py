"""
Copy/Paste Backend - Main Application Entry Point
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from .core.config import settings
from .core.middleware import check_rate_limit, generate_trace_id
from .api import ingest, brief, sources, audit, index

app = FastAPI(
    title="Copy/Paste API",
    description="Nyhetsdesk Copilot - RAG-powered editorial assistant",
    version="0.1.0",
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(ingest.router)
app.include_router(index.router)
app.include_router(brief.router)
app.include_router(sources.router)
app.include_router(audit.router)


@app.middleware("http")
async def add_trace_id(request: Request, call_next):
    """Add trace ID to all requests"""
    trace_id = generate_trace_id()
    request.state.trace_id = trace_id
    
    response = await call_next(request)
    response.headers["X-Trace-ID"] = trace_id
    return response


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Rate limiting middleware (skip for health endpoint)"""
    if request.url.path == "/health":
        return await call_next(request)
    
    # Extract API key
    api_key = request.headers.get(settings.api_key_header)
    if api_key and api_key in settings.api_key_list:
        check_rate_limit(api_key)
    
    return await call_next(request)


@app.get("/health")
async def health_check():
    """Health check endpoint (no auth required)"""
    return {
        "status": "ok",
        "service": "copy-paste-backend",
        "version": "0.1.0"
    }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    trace_id = getattr(request.state, "trace_id", "unknown")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "trace_id": trace_id,
            "detail": str(exc) if settings.debug else "An error occurred"
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

