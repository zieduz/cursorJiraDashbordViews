from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta, timezone, date, time as dtime
from ..database import get_db
from ..schemas import MetricsResponse
from ..services.metrics_service import MetricsService

router = APIRouter(prefix="/api/metrics", tags=["metrics"])


@router.get("/", response_model=MetricsResponse)
async def get_metrics(
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD) for metrics calculation"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD) for metrics calculation"),
    project_id: Optional[int] = Query(None, description="Filter by project ID"),
    project_ids: Optional[str] = Query(None, description="Comma-separated list of project IDs"),
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    status: Optional[str] = Query(None, description="Filter by issue status"),
    customers: Optional[str] = Query(None, description="Comma-separated list of customers"),
    labels: Optional[str] = Query(None, description="Comma-separated list of labels"),
    group_by: Optional[str] = Query("day", description="Aggregation granularity: day | month | year"),
    db: Session = Depends(get_db)
):
    """Get comprehensive metrics and KPIs"""
    # Convert date inputs to timezone-aware datetimes spanning full days
    start_dt: Optional[datetime] = None
    end_dt: Optional[datetime] = None

    if start_date is not None:
        start_dt = datetime.combine(start_date, dtime.min).replace(tzinfo=timezone.utc)
    if end_date is not None:
        end_dt = datetime.combine(end_date, dtime.max).replace(tzinfo=timezone.utc)

    metrics_service = MetricsService(db)
    project_ids_list = [int(pid.strip()) for pid in project_ids.split(',')] if project_ids else None
    customers_list = [c.strip() for c in customers.split(',')] if customers else None
    labels_list = [l.strip() for l in labels.split(',')] if labels else None

    metrics = metrics_service.get_metrics(
        start_date=start_dt,
        end_date=end_dt,
        project_id=project_id,
        project_ids=project_ids_list,
        user_id=user_id,
        status=status,
        customers=customers_list,
        labels=labels_list,
        group_by=(group_by or "day").lower(),
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


@router.get("/cfd")
async def get_cumulative_flow(
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    project_id: Optional[int] = Query(None, description="Filter by project ID"),
    project_ids: Optional[str] = Query(None, description="Comma-separated list of project IDs"),
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    status: Optional[str] = Query(None, description="Filter by issue status"),
    customers: Optional[str] = Query(None, description="Comma-separated list of customers"),
    labels: Optional[str] = Query(None, description="Comma-separated list of labels"),
    group_by: Optional[str] = Query("day", description="Aggregation granularity: day | month | year"),
    db: Session = Depends(get_db),
):
    # Default window
    end_dt = datetime.combine(end_date, dtime.max).replace(tzinfo=timezone.utc) if end_date else datetime.now(timezone.utc)
    start_dt = datetime.combine(start_date, dtime.min).replace(tzinfo=timezone.utc) if start_date else end_dt - timedelta(days=30)

    metrics_service = MetricsService(db)
    project_ids_list = [int(pid.strip()) for pid in project_ids.split(',')] if project_ids else ([project_id] if project_id else None)
    customers_list = [c.strip() for c in customers.split(',')] if customers else None
    labels_list = [l.strip() for l in labels.split(',')] if labels else None

    data = metrics_service.get_cumulative_flow(
        start_date=start_dt,
        end_date=end_dt,
        project_ids=project_ids_list,
        user_id=user_id,
        status=status,
        customers=customers_list,
        labels=labels_list,
        group_by=(group_by or "day").lower(),
    )
    return {"cfd": data}


@router.get("/control-chart")
async def get_control_chart(
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    project_id: Optional[int] = Query(None, description="Filter by project ID"),
    project_ids: Optional[str] = Query(None, description="Comma-separated list of project IDs"),
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    customers: Optional[str] = Query(None, description="Comma-separated list of customers"),
    labels: Optional[str] = Query(None, description="Comma-separated list of labels"),
    db: Session = Depends(get_db),
):
    # Default window
    end_dt = datetime.combine(end_date, dtime.max).replace(tzinfo=timezone.utc) if end_date else datetime.now(timezone.utc)
    start_dt = datetime.combine(start_date, dtime.min).replace(tzinfo=timezone.utc) if start_date else end_dt - timedelta(days=30)

    metrics_service = MetricsService(db)
    project_ids_list = [int(pid.strip()) for pid in project_ids.split(',')] if project_ids else ([project_id] if project_id else None)
    customers_list = [c.strip() for c in customers.split(',')] if customers else None
    labels_list = [l.strip() for l in labels.split(',')] if labels else None

    result = metrics_service.get_cycle_time_metrics(
        start_date=start_dt,
        end_date=end_dt,
        project_ids=project_ids_list,
        user_id=user_id,
        customers=customers_list,
        labels=labels_list,
    )
    return result