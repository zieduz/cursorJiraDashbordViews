from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta, timezone
from ..database import get_db
from ..schemas import MetricsResponse
from ..services.metrics_service import MetricsService

router = APIRouter(prefix="/api/metrics", tags=["metrics"])


@router.get("/", response_model=MetricsResponse)
async def get_metrics(
    start_date: Optional[datetime] = Query(None, description="Start date for metrics calculation"),
    end_date: Optional[datetime] = Query(None, description="End date for metrics calculation"),
    project_id: Optional[int] = Query(None, description="Filter by project ID"),
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    db: Session = Depends(get_db)
):
    """Get comprehensive metrics and KPIs"""
    
    metrics_service = MetricsService(db)
    metrics = metrics_service.get_metrics(
        start_date=start_date,
        end_date=end_date,
        project_id=project_id,
        user_id=user_id
    )
    
    return MetricsResponse(**metrics)


@router.get("/summary")
async def get_metrics_summary(
    days: int = Query(30, description="Number of days to look back"),
    project_id: Optional[int] = Query(None, description="Filter by project ID"),
    db: Session = Depends(get_db)
):
    """Get a quick metrics summary"""
    
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days)
    
    metrics_service = MetricsService(db)
    metrics = metrics_service.get_metrics(
        start_date=start_date,
        end_date=end_date,
        project_id=project_id
    )
    
    return {
        "period": f"Last {days} days",
        "total_tickets": metrics["total_tickets"],
        "resolved_tickets": metrics["tickets_resolved"],
        "resolution_rate": f"{(metrics['tickets_resolved'] / max(metrics['total_tickets'], 1)) * 100:.1f}%",
        "sla_compliance": f"{metrics['sla_compliance']:.1f}%",
        "avg_resolution_time": f"{metrics['average_resolution_time']:.1f} hours"
    }