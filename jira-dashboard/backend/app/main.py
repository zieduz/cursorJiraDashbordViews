from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from .config import settings
from .database import engine, Base, ensure_schema
from .api import api_router
from .api.jira_sync import run_startup_sync
from .exceptions import (
    JiraDashboardException,
    jira_dashboard_exception_handler,
    http_exception_handler,
    validation_exception_handler,
    generic_exception_handler,
)
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

# Register exception handlers
app.add_exception_handler(JiraDashboardException, jira_dashboard_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

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
