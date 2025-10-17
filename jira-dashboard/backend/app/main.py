from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
import uuid
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
@app.exception_handler(RequestValidationError)
async def handle_validation_error(request: Request, exc: RequestValidationError):
    return _json_error(
        request,
        status_code=422,
        error_type="validation_error",
        message="Request validation failed",
        details=exc.errors(),
    )


@app.exception_handler(HTTPException)
async def handle_http_exception(request: Request, exc: HTTPException):
    return _json_error(
        request,
        status_code=exc.status_code,
        error_type="http_error",
        message=str(exc.detail) if exc.detail is not None else "HTTP error",
        headers=exc.headers,
    )


@app.exception_handler(SQLAlchemyError)
async def handle_sqlalchemy_error(request: Request, exc: SQLAlchemyError):
    return _json_error(
        request,
        status_code=503,
        error_type="database_error",
        message="Database temporarily unavailable",
    )


@app.exception_handler(Exception)
async def handle_unexpected_error(request: Request, exc: Exception):
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
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

# Kick off a background Jira sync after startup if configured
@app.on_event("startup")
async def startup_event():
    # Run without blocking startup
    asyncio.create_task(run_startup_sync())