from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .database import engine, Base
from .api import api_router
from .api.jira_sync import run_startup_sync
import asyncio

# Create database tables
Base.metadata.create_all(bind=engine)

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