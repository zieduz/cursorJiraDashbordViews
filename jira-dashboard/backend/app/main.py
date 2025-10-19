"""FastAPI application entrypoint for the Jira Performance Dashboard.

This module initializes the FastAPI app, configures CORS, registers API
routers, defines consistent error handling, and exposes health and root
endpoints. It also schedules an optional Jira sync task on startup.
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
import uuid
from .config import settings
from .database import engine, Base, ensure_schema
from .api import api_router
from .api.jira_sync import run_startup_sync
from .exceptions import JiraDashboardException
import asyncio
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create database tables and ensure schema consistency
try:
    Base.metadata.create_all(bind=engine)
    ensure_schema(engine)
except Exception as e:
    logger.error(f"Failed to initialize database: {e}")
    raise

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
    expose_headers=["X-Request-ID"],
)

# Include API routes
app.include_router(api_router)


# Request ID middleware to tag all responses and errors
@app.middleware("http")
async def add_request_id_header(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    # Store on request.state for handlers to access
    request.state.request_id = request_id
    try:
        response = await call_next(request)
    except Exception:
        # Let exception handlers format the response; they will set header
        raise
    response.headers["X-Request-ID"] = request_id
    return response


def _json_error(
    request: Request,
    status_code: int,
    error_type: str,
    message: str,
    details: dict | list | None = None,
    headers: dict | None = None,
):
    """Return a standardized JSON error response with a request ID header.

    Ensures all errors share a consistent shape for the frontend and logs,
    and always includes the current request's correlation identifier.
    """
    request_id = getattr(request.state, "request_id", None) or request.headers.get("X-Request-ID") or str(uuid.uuid4())
    payload = {
        "error": {
            "type": error_type,
            "message": message,
            "status_code": status_code,
            **({"details": details} if details is not None else {}),
        },
        "request_id": request_id,
    }
    response = JSONResponse(status_code=status_code, content=payload, headers=headers or {})
    response.headers["X-Request-ID"] = request_id
    return response


# Global exception handlers for consistent error responses
@app.exception_handler(JiraDashboardException)
async def handle_jira_dashboard_exception(request: Request, exc: JiraDashboardException):
    """Handle custom Jira Dashboard exceptions."""
    logger.error(
        f"JiraDashboardException: {exc.message}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "status_code": exc.status_code,
            "detail": exc.detail,
        },
    )
    return _json_error(
        request,
        status_code=exc.status_code,
        error_type=type(exc).__name__,
        message=exc.message,
        details=exc.detail if exc.detail else None,
    )


@app.exception_handler(RequestValidationError)
async def handle_validation_error(request: Request, exc: RequestValidationError):
    logger.warning(
        f"ValidationError: {exc.errors()}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "errors": exc.errors(),
        },
    )
    return _json_error(
        request,
        status_code=422,
        error_type="validation_error",
        message="Request validation failed",
        details=exc.errors(),
    )


@app.exception_handler(HTTPException)
async def handle_http_exception(request: Request, exc: HTTPException):
    logger.warning(
        f"HTTPException: {exc.detail}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "status_code": exc.status_code,
        },
    )
    return _json_error(
        request,
        status_code=exc.status_code,
        error_type="http_error",
        message=str(exc.detail) if exc.detail is not None else "HTTP error",
        headers=exc.headers,
    )


@app.exception_handler(SQLAlchemyError)
async def handle_sqlalchemy_error(request: Request, exc: SQLAlchemyError):
    logger.error(
        f"SQLAlchemyError: {str(exc)}",
        extra={
            "path": request.url.path,
            "method": request.method,
        },
    )
    return _json_error(
        request,
        status_code=503,
        error_type="database_error",
        message="Database temporarily unavailable",
    )


@app.exception_handler(Exception)
async def handle_unexpected_error(request: Request, exc: Exception):
    logger.exception(
        f"Unhandled exception: {str(exc)}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "exception_type": type(exc).__name__,
        },
    )
    return _json_error(
        request,
        status_code=500,
        error_type="internal_error",
        message="Internal server error",
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
    """Health check endpoint that verifies database connectivity."""
    try:
        from .database import SessionLocal
        db = SessionLocal()
        try:
            # Test database connection
            db.execute("SELECT 1")
            db_status = "healthy"
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            db_status = "unhealthy"
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Health check error: {e}")
        db_status = "unknown"
    
    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "database": db_status,
    }


# Kick off a background Jira sync after startup if configured
@app.on_event("startup")
async def startup_event():
    """Run startup tasks including optional Jira sync."""
    logger.info("Application startup initiated")
    try:
        # Run without blocking startup
        asyncio.create_task(run_startup_sync())
        logger.info("Jira sync task scheduled")
    except Exception as e:
        logger.error(f"Failed to schedule Jira sync task: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
