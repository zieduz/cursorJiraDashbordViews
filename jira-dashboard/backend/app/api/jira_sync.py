from fastapi import APIRouter, HTTPException, Depends, Body, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any, Tuple, Set
import asyncio
from datetime import datetime
import re
from pydantic import BaseModel

from ..database import get_db, SessionLocal
from ..models import Project as ProjectModel, User as UserModel, Ticket as TicketModel
from ..jira_client import JiraClient
from ..services.metrics_service import NON_RESOLVED_STATUSES
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


def _normalize_created_since(value: Optional[str]) -> Optional[str]:
    """Return a YYYY-MM-DD string from various user-entered date formats.

    Accepts values like:
    - YYYY-MM-DD (unchanged)
    - YYYY/MM/DD, YYYY MM DD
    - DD/MM/YYYY, DD-MM-YYYY, DD MM YYYY
    - MM/DD/YYYY, MM-DD-YYYY, MM MM YYYY
    Disambiguation: when year is at the end, prefer DMY if day > 12,
    otherwise treat as MDY.
    """
    if not value:
        return None

    v = value.strip()
    # Already ISO-like
    try:
        dt = datetime.strptime(v, "%Y-%m-%d")
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        pass

    # Replace any non-digit with a hyphen to ease splitting
    cleaned = re.sub(r"[^0-9]", "-", v)
    parts = [p for p in cleaned.split("-") if p]
    if len(parts) != 3:
        return None
    a, b, c = parts
    # Year-first
    if len(a) == 4:
        try:
            dt = datetime(int(a), int(b), int(c))
            return dt.strftime("%Y-%m-%d")
        except Exception:
            return None
    # Year-last (DD/MM/YYYY or MM/DD/YYYY)
    if len(c) == 4:
        day = int(a)
        month = int(b)
        # If first number > 12, it must be day, so DMY
        if day > 12:
            d, m, y = day, month, int(c)
        else:
            # Otherwise default to MDY; swap so that a=month, b=day
            d, m, y = int(b), int(a), int(c)
        try:
            dt = datetime(y, m, d)
            return dt.strftime("%Y-%m-%d")
        except Exception:
            return None
    return None


def _compute_first_resolved_datetime(issue: Dict[str, Any]) -> Optional[datetime]:
    """Return the first datetime when the issue transitioned to a status
    not contained in NON_RESOLVED_STATUSES. Falls back to None if not found.

    Expects Jira search result with changelog expanded (expand=changelog).
    """
    try:
        changelog = (issue or {}).get("changelog", {})
        histories = changelog.get("histories", []) if isinstance(changelog, dict) else []
        candidate_times: List[datetime] = []
        for history in histories:
            created_str = history.get("created")
            created_dt = _parse_jira_datetime(created_str)
            if not created_dt:
                continue
            for item in history.get("items", []) or []:
                try:
                    if (item.get("field") or "").lower() != "status":
                        continue
                    to_status = (item.get("toString") or "").strip().lower()
                    if to_status and to_status not in NON_RESOLVED_STATUSES:
                        candidate_times.append(created_dt)
                except Exception:
                    # Skip malformed items; continue scanning
                    continue
        if not candidate_times:
            return None
        # Earliest transition to a resolved/done status
        return min(candidate_times)
    except Exception:
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


def _ensure_ticket(
    db: Session,
    project: ProjectModel,
    assignee: Optional[UserModel],
    issue_parsed: Dict[str, Any],
    first_resolved_at: Optional[datetime] = None,
) -> TicketModel:
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
            "customer": "customer",
        }
        for src_key, model_attr in mapping.items():
            new_val = issue_parsed.get(src_key)
            # Normalize labels: store as comma-delimited string for LIKE queries
            if src_key == "labels":
                new_val = "," + ",".join([str(v) for v in (new_val or [])]) + "," if new_val else None
            # Ensure customer stored as string (parse layer may already handle it)
            if src_key == "customer" and not (new_val is None or isinstance(new_val, str)):
                try:
                    # Prefer common keys if dict provided unexpectedly
                    if isinstance(new_val, dict):
                        new_val = (
                            (new_val.get("value") or new_val.get("name") or new_val.get("id") or "").strip()
                        ) or None
                    else:
                        new_val = str(new_val).strip() or None
                except Exception:
                    new_val = None
            if getattr(ticket, model_attr) != new_val:
                setattr(ticket, model_attr, new_val)
                changed = True
        # labels handled separately since not in mapping dict
        labels_list = issue_parsed.get("labels") or []
        labels_str = "," + ",".join([str(v) for v in labels_list]) + "," if labels_list else None
        if ticket.labels != labels_str:
            ticket.labels = labels_str
            changed = True
        ticket.project_id = project.id
        ticket.assignee_id = assignee.id if assignee else None

        # Sync timestamps from Jira so charts aggregate correctly by date
        created_dt = _parse_jira_datetime(issue_parsed.get("created_at"))
        if created_dt and ticket.created_at != created_dt:
            ticket.created_at = created_dt
            changed = True

        # Prefer earliest transition to a resolved/done status if available
        resolved_dt = first_resolved_at or _parse_jira_datetime(issue_parsed.get("resolved_at"))
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
        # Ensure customer coerced to string for DB storage
        customer=(issue_parsed.get("customer") if isinstance(issue_parsed.get("customer"), str) else (
            (
                (issue_parsed.get("customer") or {}).get("value")
                if isinstance(issue_parsed.get("customer"), dict)
                else (str(issue_parsed.get("customer")).strip() if issue_parsed.get("customer") is not None else None)
            )
        )),
        labels=("," + ",".join([str(v) for v in (issue_parsed.get("labels") or [])]) + ",") if issue_parsed.get("labels") else None,
        story_points=issue_parsed.get("story_points"),
        time_estimate=issue_parsed.get("time_estimate"),
        time_spent=issue_parsed.get("time_spent"),
        created_at=_parse_jira_datetime(issue_parsed.get("created_at")),
        # Prefer earliest transition to a resolved/done status if available
        resolved_at=(first_resolved_at or _parse_jira_datetime(issue_parsed.get("resolved_at"))),
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

    # Trim whitespace/quotes to avoid malformed JQL and 401 from bad caching layers
    created_since = (created_since or settings.jira_created_since or "").strip().strip('"').strip("'")
    normalized = _normalize_created_since(created_since)
    if not normalized:
        raise ValueError("created_since must be a valid date (YYYY-MM-DD or similar)")
    created_since = normalized

    # Concurrency settings for page fetches
    try:
        page_size = int(getattr(settings, "jira_page_size", 100))
    except Exception:
        page_size = 100
    try:
        concurrency = int(getattr(settings, "jira_concurrency", 6))
    except Exception:
        concurrency = 6

    sem = asyncio.Semaphore(concurrency)

    # Caches to avoid repeated DB lookups
    users_by_jira_id: Dict[str, UserModel] = {}
    users_by_email: Dict[str, UserModel] = {}

    async def fetch_page(client: JiraClient, project_key: str, start_at: int) -> Dict[str, Any]:
        async with sem:
            return await client.get_project_issues(
                project_key=project_key,
                start_at=start_at,
                max_results=page_size,
                created_since=created_since,
            )

    async with JiraClient() as client:
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

            # Fetch first page to determine total, then fetch remaining pages concurrently
            first_page = await fetch_page(client, key, 0)
            issues_first = first_page.get("issues", [])
            total_found = int(first_page.get("total", len(issues_first)))

            # Schedule remaining pages
            tasks = []
            for start_at in range(page_size, total_found, page_size):
                tasks.append(asyncio.create_task(fetch_page(client, key, start_at)))

            pages = []
            if tasks:
                pages = await asyncio.gather(*tasks)

            # Aggregate issues
            all_issues: List[Dict[str, Any]] = list(issues_first)
            for page in pages:
                page_issues = page.get("issues", [])
                if page_issues:
                    all_issues.extend(page_issues)

            if not all_issues:
                upserted_projects += 1
                # Commit project upsert early to reduce transaction length
                db.commit()
                continue

            # Preload existing tickets for this project to avoid N lookups
            jira_ids = [str(issue.get("key") or "").strip() for issue in all_issues if issue.get("key")]
            existing_tickets = {}
            if jira_ids:
                for t in db.query(TicketModel).filter(TicketModel.jira_id.in_(jira_ids)).all():
                    existing_tickets[t.jira_id] = t

            # Pre-parse issues and collect assignee identifiers for bulk user preload
            parsed_issues: List[Tuple[Dict[str, Any], Dict[str, Any]]] = []
            assignee_ids: Set[str] = set()
            assignee_emails: Set[str] = set()
            for issue in all_issues:
                parsed = client.parse_issue(issue)
                parsed_issues.append((issue, parsed))
                ai = _parse_assignee(parsed.get("assignee"))
                jid = (ai.get("jira_id") or "").strip()
                eml = (ai.get("email") or "").strip()
                if jid:
                    assignee_ids.add(jid)
                if eml:
                    assignee_emails.add(eml)

            # Bulk preload users by jira_id and email, populate caches
            if assignee_ids:
                for u in db.query(UserModel).filter(UserModel.jira_id.in_(list(assignee_ids))).all():
                    if u.jira_id:
                        users_by_jira_id[u.jira_id] = u
                    if u.email:
                        users_by_email[u.email] = u
            if assignee_emails:
                for u in db.query(UserModel).filter(UserModel.email.in_(list(assignee_emails))).all():
                    if u.email:
                        users_by_email[u.email] = u
                    if u.jira_id:
                        users_by_jira_id[u.jira_id] = u

            # Upsert all issues
            for issue, parsed in parsed_issues:
                assignee_info = _parse_assignee(parsed.get("assignee"))

                # User cache lookup
                user: Optional[UserModel] = None
                cache_key_id = (assignee_info.get("jira_id") or "").strip() or None
                cache_key_email = (assignee_info.get("email") or "").strip() or None
                if cache_key_id and cache_key_id in users_by_jira_id:
                    user = users_by_jira_id[cache_key_id]
                elif cache_key_email and cache_key_email in users_by_email:
                    user = users_by_email[cache_key_email]
                else:
                    user = _ensure_user(db, assignee_info)
                    if user:
                        if user.jira_id:
                            users_by_jira_id[user.jira_id] = user
                        if user.email:
                            users_by_email[user.email] = user

                # Determine earliest resolved/done transition time from changelog (optional)
                first_resolved_at = (
                    _compute_first_resolved_datetime(issue)
                    if bool(getattr(settings, "jira_include_changelog", True))
                    else None
                )

                existing = existing_tickets.get(parsed["jira_id"]) if parsed.get("jira_id") else None
                if existing:
                    # Update existing ticket without issuing a read query
                    ticket = existing
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
                        "customer": "customer",
                    }
                    for src_key, model_attr in mapping.items():
                        new_val = parsed.get(src_key)
                        if src_key == "customer" and not (new_val is None or isinstance(new_val, str)):
                            try:
                                if isinstance(new_val, dict):
                                    new_val = (
                                        (new_val.get("value") or new_val.get("name") or new_val.get("id") or "").strip()
                                    ) or None
                                else:
                                    new_val = str(new_val).strip() or None
                            except Exception:
                                new_val = None
                        if getattr(ticket, model_attr) != new_val:
                            setattr(ticket, model_attr, new_val)
                            changed = True
                    # labels handled separately
                    labels_list = parsed.get("labels") or []
                    labels_str = "," + ",".join([str(v) for v in labels_list]) + "," if labels_list else None
                    if ticket.labels != labels_str:
                        ticket.labels = labels_str
                        changed = True
                    ticket.project_id = project.id
                    ticket.assignee_id = user.id if user else None

                    created_dt = _parse_jira_datetime(parsed.get("created_at"))
                    if created_dt and ticket.created_at != created_dt:
                        ticket.created_at = created_dt
                        changed = True
                    resolved_dt = first_resolved_at or _parse_jira_datetime(parsed.get("resolved_at"))
                    if ticket.resolved_at != resolved_dt:
                        ticket.resolved_at = resolved_dt
                        changed = True
                    if changed:
                        db.add(ticket)
                else:
                    _ensure_ticket(db, project, user, parsed, first_resolved_at=first_resolved_at)
                total_issues += 1
                if user:
                    upserted_users += 1
                upserted_tickets += 1

            upserted_projects += 1
            # Commit changes for this project before moving to the next
            db.commit()

    # Final safety commit (no-op if nothing pending)
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
