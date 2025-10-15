from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from ..database import get_db
from ..schemas import ForecastResponse
from ..services.forecast_service import ForecastService

router = APIRouter(prefix="/api/forecast", tags=["forecast"])


@router.get("/", response_model=ForecastResponse)
async def get_forecast(
    days_ahead: int = Query(30, description="Number of days to forecast ahead"),
    project_id: Optional[int] = Query(None, description="Filter by project ID"),
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    db: Session = Depends(get_db)
):
    """Get velocity forecast using machine learning"""
    
    forecast_service = ForecastService(db)
    forecast = forecast_service.get_forecast(
        days_ahead=days_ahead,
        project_id=project_id,
        user_id=user_id
    )
    
    return ForecastResponse(**forecast)


@router.get("/sprint")
async def get_sprint_forecast(
    sprint_length_days: int = Query(14, description="Sprint length in days"),
    project_id: Optional[int] = Query(None, description="Filter by project ID"),
    db: Session = Depends(get_db)
):
    """Get forecast for next sprint specifically"""
    
    forecast_service = ForecastService(db)
    sprint_forecast = forecast_service.get_sprint_forecast(
        sprint_length_days=sprint_length_days,
        project_id=project_id
    )
    
    return sprint_forecast