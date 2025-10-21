"""API router aggregation for the Jira Performance Dashboard backend.

This package exposes a single `api_router` that mounts all versionless
endpoint groups (tickets, metrics, forecast, Jira sync, projects, config,
and filters). Import and include `api_router` in the FastAPI application
to register all routes under their respective prefixes.
"""

from fastapi import APIRouter
from .tickets import router as tickets_router
from .metrics import router as metrics_router
from .forecast import router as forecast_router
from .jira_sync import router as jira_sync_router
from .projects import router as projects_router
from .commits import router as commits_router
from .config import router as config_router
from .filters import router as filters_router
from .activity import router as activity_router

api_router = APIRouter()
api_router.include_router(tickets_router)
api_router.include_router(metrics_router)
api_router.include_router(forecast_router)
api_router.include_router(jira_sync_router)
api_router.include_router(projects_router)
api_router.include_router(config_router)
api_router.include_router(filters_router)
api_router.include_router(commits_router)
api_router.include_router(activity_router)
