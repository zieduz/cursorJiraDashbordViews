from fastapi import APIRouter, HTTPException, Depends, Body, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel

from ..database import get_db, SessionLocal
from ..models import Project as ProjectModel, User as UserModel, Ticket as TicketModel
from ..jira_client import JiraClient
from ..config import settings


router = APIRouter(prefix="/api/jira", tags=["jira"]) 


def _parse_jira_datetime(value: Optional[str]) -> Optional[datetime]:
    """Parse Jira datetime string into aware datetime.

    Supports formats like '2025-01-10T12:34:56.789+0000' and without
    fractional seconds.
    """
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%f%z")
    except ValueError:
        try:
            return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S%z")
        except ValueError:
            return None

def _parse_assignee(assignee: Optional[Dict[str, Any]]) -> Dict[str, Optional[str]]:
    if not assignee:
        return {"jira_id": None, "email": None, "display_name": None, "avatar_url": None}
    return {
        "jira_id": str(assignee.get("accountId") or "").strip() or None,
        "email": (assignee.get("emailAddress") or "").strip() or None,
        "display_name": (assignee.get("displayName") or "").strip() or None,
        "avatar_url": (assignee.get("avatarUrls", {}).get("48x48") or "").strip() or None,
    }


def _ensure_project(db: Session, key: str, name: str, description: Optional[str]) -> ProjectModel:
    project = db.query(ProjectModel).filter(ProjectModel.key == key).first()
    if project:
        changed = False
        if project.name != name:
            project.name = name
            changed = True
        if description is not None and project.description != description:
            project.description = description
            changed = True
        if changed:
            db.add(project)
        return project

    project = ProjectModel(key=key, name=name, description=description)
    db.add(project)
    db.flush()
    return project


def _ensure_user(db: Session, assignee_info: Dict[str, Optional[str]]) -> Optional[UserModel]:
    if not assignee_info.get("jira_id") and not assignee_info.get("email"):
        return None

    user: Optional[UserModel] = None
    if assignee_info.get("jira_id"):
        user = db.query(UserModel).filter(UserModel.jira_id == assignee_info["jira_id"]).first()
    if not user and assignee_info.get("email"):
        user = db.query(UserModel).filter(UserModel.email == assignee_info["email"]).first()

    if user:
        changed = False
        if assignee_info.get("jira_id") and user.jira_id != assignee_info["jira_id"]:
            user.jira_id = assignee_info["jira_id"]
            changed = True
        if assignee_info.get("email") and user.email != assignee_info["email"]:
            user.email = assignee_info["email"]
            changed = True
        if assignee_info.get("display_name") and user.display_name != assignee_info["display_name"]:
            user.display_name = assignee_info["display_name"]
            changed = True
        if assignee_info.get("avatar_url") and user.avatar_url != assignee_info["avatar_url"]:
            user.avatar_url = assignee_info["avatar_url"]
            changed = True
        if changed:
            db.add(user)
        return user

    user = UserModel(
        jira_id=assignee_info.get("jira_id"),
        email=assignee_info.get("email"),
        display_name=assignee_info.get("display_name") or (assignee_info.get("email") or "Unknown"),
        avatar_url=assignee_info.get("avatar_url"),
    )
    db.add(user)
    db.flush()
    return user


def _ensure_ticket(db: Session, project: ProjectModel, assignee: Optional[UserModel], issue_parsed: Dict[str, Any]) -> TicketModel:
    jira_id = issue_parsed["jira_id"]
    ticket = db.query(TicketModel).filter(TicketModel.jira_id == jira_id).first()
    if ticket:
        changed = False
        mapping = {
            "summary": "summary",
            "description": "description",
            "status": "status",
            "priority": "priority",
            "issue_type": "issue_type",
            "story_points": "story_points",
            "time_estimate": "time_estimate",
            "time_spent": "time_spent",
        }
        for src_key, model_attr in mapping.items():
            new_val = issue_parsed.get(src_key)
            if getattr(ticket, model_attr) != new_val:
                setattr(ticket, model_attr, new_val)
                changed = True
        ticket.project_id = project.id
        ticket.assignee_id = assignee.id if assignee else None

        # Sync timestamps from Jira so charts aggregate correctly by date
        created_dt = _parse_jira_datetime(issue_parsed.get("created_at"))
        if created_dt and ticket.created_at != created_dt:
            ticket.created_at = created_dt
            changed = True

        resolved_dt = _parse_jira_datetime(issue_parsed.get("resolved_at"))
        if ticket.resolved_at != resolved_dt:
            ticket.resolved_at = resolved_dt
            changed = True
        if changed:
            db.add(ticket)
        return ticket

    ticket = TicketModel(
        jira_id=jira_id,
        project_id=project.id,
        assignee_id=assignee.id if assignee else None,
        summary=issue_parsed.get("summary") or "",
        description=issue_parsed.get("description"),
        status=issue_parsed.get("status") or "",
        priority=issue_parsed.get("priority"),
        issue_type=issue_parsed.get("issue_type"),
        story_points=issue_parsed.get("story_points"),
        time_estimate=issue_parsed.get("time_estimate"),
        time_spent=issue_parsed.get("time_spent"),
        created_at=_parse_jira_datetime(issue_parsed.get("created_at")),
        resolved_at=_parse_jira_datetime(issue_parsed.get("resolved_at")),
    )
    db.add(ticket)
    db.flush()
    return ticket


async def perform_jira_sync(
    db: Session,
    project_keys: Optional[List[str]] = None,
    created_since: Optional[str] = None,
) -> Dict[str, Any]:
    """Core Jira sync logic reused by API and startup."""
    if project_keys is None or len(project_keys) == 0:
        project_keys = settings.jira_project_keys
    if not project_keys:
        raise ValueError("No project keys provided or configured")

    created_since = created_since or settings.jira_created_since
    try:
        datetime.strptime(created_since, "%Y-%m-%d")
    except ValueError:
        raise ValueError("created_since must be YYYY-MM-DD")

    client = JiraClient()
    total_projects = 0
    total_issues = 0
    upserted_projects = 0
    upserted_users = 0
    upserted_tickets = 0

    jira_projects_index: Dict[str, Dict[str, Any]] = {}
    try:
        all_projects = await client.get_projects()
        for p in all_projects:
            if p and isinstance(p, dict) and p.get("key"):
                jira_projects_index[p["key"]] = p
    except Exception:
        # Swallow project list errors; we can still sync issues via keys
        pass

    for key in project_keys:
        total_projects += 1
        jira_project = jira_projects_index.get(key, {})
        project_name = jira_project.get("name") or key
        project_desc = jira_project.get("description") if isinstance(jira_project.get("description"), str) else None

        project = _ensure_project(db, key=key, name=project_name, description=project_desc)

        start_at = 0
        while True:
            data = await client.get_project_issues(
                project_key=key,
                start_at=start_at,
                max_results=100,
                created_since=created_since,
            )
            issues = data.get("issues", [])
            if not issues:
                break

            for issue in issues:
                parsed = client.parse_issue(issue)
                assignee_info = _parse_assignee(parsed.get("assignee"))
                user = _ensure_user(db, assignee_info)
                _ensure_ticket(db, project, user, parsed)
                total_issues += 1
                if user:
                    upserted_users += 1
                upserted_tickets += 1

            start_at += 100
            if len(issues) < 100:
                break

        upserted_projects += 1

    db.commit()

    return {
        "projects_processed": total_projects,
        "issues_processed": total_issues,
        "projects_upserted": upserted_projects,
        "users_upserted": upserted_users,
        "tickets_upserted": upserted_tickets,
        "created_since": created_since,
        "project_keys": project_keys,
    }


class JiraSyncRequest(BaseModel):
    project_keys: Optional[List[str]] = None
    created_since: Optional[str] = None


@router.post("/sync", summary="Sync Jira issues for configured projects since a date")
async def sync_jira(
    project_keys: Optional[List[str]] = Query(None),
    created_since: Optional[str] = Query(None),
    body: Optional[JiraSyncRequest] = Body(None),
    db: Session = Depends(get_db),
):
    """Sync Jira issues for the provided project keys (or configured keys) created on/after a date.

    - project_keys: List of Jira project keys. If omitted, uses `JIRA_PROJECT_KEYS` env.
    - created_since: YYYY-MM-DD. If omitted, uses `JIRA_CREATED_SINCE` (default 2025-01-01).
    """
    # Allow both JSON body payload and query parameters
    if body is not None:
        if body.project_keys is not None:
            project_keys = body.project_keys
        if body.created_since is not None:
            created_since = body.created_since

    try:
        return await perform_jira_sync(db, project_keys=project_keys, created_since=created_since)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


async def run_startup_sync() -> None:
    """Run Jira sync at app startup if credentials and keys are configured."""
    required = [settings.jira_base_url, settings.jira_username, settings.jira_api_token]
    if not all(required) or not settings.jira_project_keys:
        print("Skipping Jira startup sync: missing Jira credentials or project keys")
        return

    db = SessionLocal()
    try:
        result = await perform_jira_sync(db)
        print(
            f"Jira startup sync completed: projects={result['projects_processed']} issues={result['issues_processed']}"
        )
    except Exception as e:
        print(f"Jira startup sync failed: {e}")
    finally:
        db.close()
