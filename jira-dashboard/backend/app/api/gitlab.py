from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, Dict, List
from datetime import datetime, timedelta, timezone
import asyncio

from ..database import get_db
from ..models import ActivityEvent, ActivitySource, ActivityEventType, Project as ProjectModel, User as UserModel
from ..config import settings
from ..gitlab_client import GitLabClient, parse_iso_datetime
from ..exceptions import GitLabAPIError, GitLabAuthenticationError, GitLabConnectionError


router = APIRouter(prefix="/api/gitlab", tags=["gitlab"])


def _normalize_since_until(since: Optional[str], until: Optional[str]) -> tuple[datetime, datetime]:
    now = datetime.now(timezone.utc)
    end = parse_iso_datetime(until) or now
    if since:
        start = parse_iso_datetime(since) or (end - timedelta(days=int(getattr(settings, "gitlab_default_since_days", 90) or 90)))
    else:
        start = end - timedelta(days=int(getattr(settings, "gitlab_default_since_days", 90) or 90))
    if start > end:
        start, end = end, start
    return start, end


def _ensure_project(db: Session, key: str, name: Optional[str] = None) -> ProjectModel:
    project = db.query(ProjectModel).filter(ProjectModel.key == key).first()
    if project:
        if name and project.name != name:
            project.name = name
            db.add(project)
        return project
    project = ProjectModel(key=key, name=name or key)
    db.add(project)
    db.flush()
    return project


def _find_or_create_user_by_email(db: Session, email: Optional[str], display_name: Optional[str]) -> Optional[UserModel]:
    if not email and not display_name:
        return None
    user: Optional[UserModel] = None
    if email:
        user = db.query(UserModel).filter(UserModel.email == email).first()
    if not user and display_name:
        user = db.query(UserModel).filter(UserModel.display_name == display_name).first()
    if user:
        new_name = display_name or user.display_name
        if new_name and user.display_name != new_name:
            user.display_name = new_name
            db.add(user)
        return user
    user = UserModel(jira_id=None, email=email, display_name=display_name or (email or "Unknown"), avatar_url=None)
    db.add(user)
    db.flush()
    return user


@router.post("/sync", summary="Sync GitLab activity events from branches mapped to customers")
async def sync_gitlab_activity(
    project_ids: Optional[List[int]] = Query(None, description="GitLab project IDs; defaults to GITLAB_PROJECT_IDS env"),
    since: Optional[str] = Query(None, description="ISO8601 start datetime"),
    until: Optional[str] = Query(None, description="ISO8601 end datetime"),
    db: Session = Depends(get_db),
):
    effective_project_ids: List[int] = project_ids or list(getattr(settings, "gitlab_project_ids", []) or [])
    if not effective_project_ids:
        raise HTTPException(status_code=400, detail="No GitLab project IDs provided or configured")

    branch_customer = dict(getattr(settings, "gitlab_branch_customer_map", {}) or {})
    if not branch_customer:
        raise HTTPException(status_code=400, detail="GITLAB_BRANCH_CUSTOMER_MAP is not configured")

    start_dt, end_dt = _normalize_since_until(since, until)

    created_events = 0

    try:
        concurrency = int(getattr(settings, "gitlab_concurrency", 6) or 6)
    except Exception:
        concurrency = 6
    sem = asyncio.Semaphore(concurrency)

    async def process_project(proj_id: int):
        nonlocal created_events
        async with sem:
            async with GitLabClient() as gl:
                # Project metadata
                try:
                    proj = await gl.get_project(proj_id)
                    proj_name = (proj.get("name_with_namespace") or proj.get("name") or str(proj_id)).strip()
                except Exception:
                    proj_name = str(proj_id)
                project = _ensure_project(db, key=f"GL-{proj_id}", name=proj_name)

                # Branches
                branches = await gl.list_branches(proj_id, per_page=int(getattr(settings, "gitlab_page_size", 100) or 100))
                matched: List[tuple[str, str]] = []
                for b in branches or []:
                    name = (b.get("name") or "").strip()
                    if not name:
                        continue
                    for pattern, customer in branch_customer.items():
                        # Treat mapping patterns as prefixes (e.g., "S9.1.X" matches "S9.1.X-some")
                        if name == pattern or name.startswith(pattern.rstrip("*")):
                            matched.append((name, customer))
                            break

                # Commits as activity events
                for branch_name, customer in matched:
                    commits = await gl.list_commits(
                        proj_id,
                        ref_name=branch_name,
                        since=start_dt.isoformat(),
                        until=end_dt.isoformat(),
                        per_page=int(getattr(settings, "gitlab_page_size", 100) or 100),
                    )
                    for c in commits or []:
                        timestamp = c.get("created_at") or c.get("committed_date") or c.get("authored_date")
                        occurred = parse_iso_datetime(timestamp)
                        if not occurred:
                            continue
                        if not (start_dt <= occurred <= end_dt):
                            continue
                        author_name = (c.get("author_name") or "").strip() or None
                        author_email = (c.get("author_email") or "").strip() or None
                        user = _find_or_create_user_by_email(db, email=author_email, display_name=author_name)
                        evt = ActivityEvent(
                            source=ActivitySource.GITLAB,
                            event_type=ActivityEventType.GITLAB_COMMIT_CREATED,
                            occurred_at_utc=occurred,
                            project_id=project.id,
                            user_id=user.id if user else None,
                            extra_data={"branch": branch_name, "customer": customer, "gitlab_project_id": proj_id},
                        )
                        db.add(evt)
                        created_events += 1

                # Merge Requests events (created, merged)
                mrs = await gl.list_merge_requests(proj_id, updated_after=start_dt.isoformat())
                for mr in mrs or []:
                    # created
                    created_at = parse_iso_datetime(mr.get("created_at"))
                    if created_at and (start_dt <= created_at <= end_dt):
                        author = (mr.get("author") or {})
                        user = _find_or_create_user_by_email(
                            db,
                            email=(author.get("public_email") or author.get("email") or None),
                            display_name=(author.get("name") or author.get("username") or None),
                        )
                        evt = ActivityEvent(
                            source=ActivitySource.GITLAB,
                            event_type=ActivityEventType.GITLAB_MR_CREATED,
                            occurred_at_utc=created_at,
                            project_id=project.id,
                            user_id=user.id if user else None,
                            extra_data={"iid": mr.get("iid"), "gitlab_project_id": proj_id, "state": mr.get("state")},
                        )
                        db.add(evt)
                        created_events += 1
                    # merged
                    merged_at = parse_iso_datetime(mr.get("merged_at"))
                    if merged_at and (start_dt <= merged_at <= end_dt):
                        merged_by = (mr.get("merged_by") or {})
                        user = _find_or_create_user_by_email(
                            db,
                            email=(merged_by.get("public_email") or merged_by.get("email") or None),
                            display_name=(merged_by.get("name") or merged_by.get("username") or None),
                        )
                        evt = ActivityEvent(
                            source=ActivitySource.GITLAB,
                            event_type=ActivityEventType.GITLAB_MR_MERGED,
                            occurred_at_utc=merged_at,
                            project_id=project.id,
                            user_id=user.id if user else None,
                            extra_data={"iid": mr.get("iid"), "gitlab_project_id": proj_id},
                        )
                        db.add(evt)
                        created_events += 1

    tasks = [asyncio.create_task(process_project(pid)) for pid in effective_project_ids]
    try:
        if tasks:
            await asyncio.gather(*tasks)
        db.commit()
    except (GitLabAPIError, GitLabAuthenticationError, GitLabConnectionError) as e:
        db.rollback()
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Unexpected error during GitLab sync: {e}")

    return {"events_created": created_events, "project_ids": effective_project_ids, "since": start_dt.isoformat(), "until": end_dt.isoformat()}


@router.get("/activity/heatmap", summary="Activity heatmap from GitLab events")
async def get_gitlab_activity_heatmap(
    projects: Optional[str] = Query(default=None, description="Comma-separated project IDs (DB IDs, not GitLab)"),
    assignees: Optional[str] = Query(default=None, description="Comma-separated user IDs"),
    start_date: datetime = Query(..., description="Start datetime (ISO8601 UTC)"),
    end_date: datetime = Query(..., description="End datetime (ISO8601 UTC)"),
    event_types: Optional[str] = Query(default="gitlab_commit_created,gitlab_mr_created,gitlab_mr_merged"),
    normalize: bool = Query(default=False),
    db: Session = Depends(get_db),
) -> Dict:
    from sqlalchemy import func

    if start_date > end_date:
        raise HTTPException(status_code=400, detail="start_date must be before end_date")

    project_ids_list = [int(p.strip()) for p in projects.split(",")] if projects else []
    assignee_ids_list = [int(u.strip()) for u in assignees.split(",")] if assignees else []
    event_types_list = [et.strip() for et in (event_types or "").split(",") if et.strip()] or [
        "gitlab_commit_created",
        "gitlab_mr_created",
        "gitlab_mr_merged",
    ]

    dow = func.extract("dow", ActivityEvent.occurred_at_utc).label("dow")
    hour = func.extract("hour", ActivityEvent.occurred_at_utc).label("hour")
    count_expr = func.count(ActivityEvent.id).label("count")

    query = (
        db.query(dow, hour, count_expr)
        .filter(ActivityEvent.source == ActivitySource.GITLAB)
        .filter(ActivityEvent.event_type.in_(event_types_list))
        .filter(ActivityEvent.occurred_at_utc >= start_date)
        .filter(ActivityEvent.occurred_at_utc <= end_date)
    )
    if project_ids_list:
        query = query.filter(ActivityEvent.project_id.in_(project_ids_list))
    if assignee_ids_list:
        query = query.filter(ActivityEvent.user_id.in_(assignee_ids_list))

    results = query.group_by(dow, hour).all()

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
