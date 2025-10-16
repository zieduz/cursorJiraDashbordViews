from fastapi import APIRouter
from .tickets import router as tickets_router
from .metrics import router as metrics_router
from .forecast import router as forecast_router
from .jira_sync import router as jira_sync_router

api_router = APIRouter()
api_router.include_router(tickets_router)
api_router.include_router(metrics_router)
api_router.include_router(forecast_router)
api_router.include_router(jira_sync_router)