from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from datetime import datetime

from ..database import get_db
from ..models import ActivityEvent, ActivitySource
from sqlalchemy import func


router = APIRouter(prefix="/api/analytics", tags=["activity"])


@router.get("/jira/activity/heatmap")
async def get_jira_activity_heatmap(
    projects: Optional[str] = Query(default=None, description="Comma-separated project IDs"),
    event_types: Optional[str] = Query(default="jira_comment,jira_status_change", description="Comma-separated event types"),
    assignees: Optional[str] = Query(default=None, description="Comma-separated user IDs"),
    start_date: datetime = Query(..., description="Start datetime (ISO8601 UTC)"),
    end_date: datetime = Query(..., description="End datetime (ISO8601 UTC)"),
    normalize: bool = Query(default=False),
    db: Session = Depends(get_db),
) -> Dict:
    """Return a 7x24 matrix of Jira activity counts."""

    # Parse comma-separated params into lists
    project_ids_list = [int(p.strip()) for p in projects.split(",")] if projects else []
    assignee_ids_list = [int(u.strip()) for u in assignees.split(",")] if assignees else []
    event_types_list = [et.strip() for et in (event_types or "").split(",") if et.strip()]
    if not event_types_list:
        event_types_list = ["jira_comment", "jira_status_change"]

    if start_date > end_date:
        raise HTTPException(status_code=400, detail="start_date must be before end_date")

    # Build query
    dow = func.extract("dow", ActivityEvent.occurred_at_utc).label("dow")
    hour = func.extract("hour", ActivityEvent.occurred_at_utc).label("hour")
    count_expr = func.count(ActivityEvent.id).label("count")

    query = (
        db.query(dow, hour, count_expr)
        .filter(ActivityEvent.source == ActivitySource.JIRA)
        .filter(ActivityEvent.event_type.in_(event_types_list))
        .filter(ActivityEvent.occurred_at_utc >= start_date)
        .filter(ActivityEvent.occurred_at_utc <= end_date)
    )

    if project_ids_list:
        query = query.filter(ActivityEvent.project_id.in_(project_ids_list))
    if assignee_ids_list:
        query = query.filter(ActivityEvent.user_id.in_(assignee_ids_list))

    results = query.group_by(dow, hour).all()

    # Build 7x24 matrix where index 0=Sunday ... 6=Saturday
    matrix: List[List[float]] = [[0 for _ in range(24)] for _ in range(7)]
    total_count = 0
    for row in results:
        d = int(row.dow)
        h = int(row.hour)
        c = int(row.count)
        if 0 <= d <= 6 and 0 <= h <= 23:
            matrix[d][h] = c
            total_count += c

    if normalize and total_count > 0:
        matrix = [[(cell / total_count) for cell in r] for r in matrix]

    return {
        "matrix": matrix,
        "total_events": total_count,
        "filters": {
            "projects": project_ids_list,
            "event_types": event_types_list,
            "assignees": assignee_ids_list,
            "date_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            },
        },
    }
