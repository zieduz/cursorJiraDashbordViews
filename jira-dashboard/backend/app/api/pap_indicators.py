from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta, timezone

from ..database import get_db
from ..services.pap_service import PAPService
from ..schemas import PAPIndicatorsResponse, PAPFilters

router = APIRouter(prefix="/api/pap-indicators", tags=["PAPIndicators"])

@router.get("/summary", response_model=PAPIndicatorsResponse)
async def get_pap_indicators_summary(
    start_date: Optional[datetime] = Query(None, description="Start date (ISO8601 UTC)"),
    end_date: Optional[datetime] = Query(None, description="End date (ISO8601 UTC)"),
    db: Session = Depends(get_db),
):
    """Return aggregated performance indicators for tracked users and projects."""
    
    # 1. Resolve date range
    if not end_date:
        end_date = datetime.now(timezone.utc)
    if not start_date:
        start_date = end_date - timedelta(days=30)
        
    if start_date > end_date:
        raise HTTPException(status_code=400, detail="start_date must be before end_date")

    # 2. Initialize Service
    service = PAPService(db)

    # 3. Fetch Metrics via Service
    comments_metrics = service.get_comments_metrics(start_date, end_date)
    status_metrics = service.get_status_changes_metrics(start_date, end_date)
    mr_metrics = service.get_mr_metrics(start_date, end_date)

    # 4. Construct Response
    return PAPIndicatorsResponse(
        comments_by_user_project=comments_metrics,
        status_changes_by_user_project=status_metrics,
        mrs_by_author=mr_metrics,
        filters=PAPFilters(
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
            tracked_emails=service.tracked_emails
        )
    )
