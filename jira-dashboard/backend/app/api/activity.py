from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from datetime import datetime

from ..database import get_db
from ..models import ActivityEvent, ActivitySource, Ticket
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

    # Fallback: if no events found, approximate from tickets' status timestamps
    # Only applies when requesting Jira status change events
    if total_count == 0 and ("jira_status_change" in set(event_types_list)):
        # Aggregate started_at and resolved_at as proxies for status changes
        t_dow_started = func.extract("dow", Ticket.started_at).label("dow")
        t_hour_started = func.extract("hour", Ticket.started_at).label("hour")
        started_q = (
            db.query(t_dow_started, t_hour_started, func.count(Ticket.id).label("count"))
            .filter(Ticket.started_at.isnot(None))
            .filter(Ticket.started_at >= start_date)
            .filter(Ticket.started_at <= end_date)
        )
        if project_ids_list:
            started_q = started_q.filter(Ticket.project_id.in_(project_ids_list))
        if assignee_ids_list:
            started_q = started_q.filter(Ticket.assignee_id.in_(assignee_ids_list))

        t_dow_resolved = func.extract("dow", Ticket.resolved_at).label("dow")
        t_hour_resolved = func.extract("hour", Ticket.resolved_at).label("hour")
        resolved_q = (
            db.query(t_dow_resolved, t_hour_resolved, func.count(Ticket.id).label("count"))
            .filter(Ticket.resolved_at.isnot(None))
            .filter(Ticket.resolved_at >= start_date)
            .filter(Ticket.resolved_at <= end_date)
        )
        if project_ids_list:
            resolved_q = resolved_q.filter(Ticket.project_id.in_(project_ids_list))
        if assignee_ids_list:
            resolved_q = resolved_q.filter(Ticket.assignee_id.in_(assignee_ids_list))

        started_rows = started_q.group_by(t_dow_started, t_hour_started).all()
        resolved_rows = resolved_q.group_by(t_dow_resolved, t_hour_resolved).all()

        fallback_total = 0
        for row in started_rows:
            d = int(row.dow)
            h = int(row.hour)
            c = int(row.count)
            if 0 <= d <= 6 and 0 <= h <= 23:
                matrix[d][h] += c
                fallback_total += c
        for row in resolved_rows:
            d = int(row.dow)
            h = int(row.hour)
            c = int(row.count)
            if 0 <= d <= 6 and 0 <= h <= 23:
                matrix[d][h] += c
                fallback_total += c

        total_count = fallback_total

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
