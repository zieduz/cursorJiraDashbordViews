from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import logging
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .database import engine, Base, ensure_schema
from .api import api_router
from .api.jira_sync import run_startup_sync
import asyncio

# Create database tables and ensure schema consistency
Base.metadata.create_all(bind=engine)
ensure_schema(engine)

app = FastAPI(
    title="Jira Performance Dashboard API",
    description="API for Jira performance metrics and forecasting",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router)


# Global exception handlers to ensure consistent JSON error responses
logger = logging.getLogger("uvicorn.error")


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Keep details concise; do not leak sensitive info
    try:
        details = exc.errors()
    except Exception:
        details = [{"msg": "Validation error"}]
    logger.warning(
        "Validation error on %s %s: %s", request.method, request.url.path, details
    )
    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation error",
            "detail": details,
            "path": request.url.path,
            "method": request.method,
        },
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    # Covers 404 and any HTTPException raised in routes/services
    logger.info(
        "HTTPException %s on %s %s: %s",
        getattr(exc, "status_code", 500),
        request.method,
        request.url.path,
        getattr(exc, "detail", None),
    )
    headers = getattr(exc, "headers", None) or None
    return JSONResponse(
        status_code=getattr(exc, "status_code", 500),
        content={
            "error": exc.detail if isinstance(exc.detail, str) else "HTTP error",
            "detail": exc.detail,
            "path": request.url.path,
            "method": request.method,
        },
        headers=headers,
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    # Final safety net for unexpected errors
    logger.exception("Unhandled error during %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred.",
            "path": request.url.path,
            "method": request.method,
        },
    )


@app.get("/")
async def root():
    return {
        "message": "Jira Performance Dashboard API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

# Kick off a background Jira sync after startup if configured
@app.on_event("startup")
async def startup_event():
    # Run without blocking startup
    asyncio.create_task(run_startup_sync())