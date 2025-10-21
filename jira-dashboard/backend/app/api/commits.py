from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import re

from ..database import get_db
from ..models import Commit as CommitModel, Ticket as TicketModel, Project as ProjectModel, User as UserModel

router = APIRouter(prefix="/api/commits", tags=["commits"])

ISSUE_KEY_RE = re.compile(r"\b([A-Z][A-Z0-9]+-\d+)\b")


class CommitIngestItem(BaseModel):
    commit_hash: str
    message: str
    author_email: Optional[str] = None
    author_name: Optional[str] = None
    committed_at: Optional[datetime] = None
    project_key: Optional[str] = None
    ticket_key: Optional[str] = None


class CommitIngestRequest(BaseModel):
    commits: List[CommitIngestItem]


@router.post("/ingest")
async def ingest_commits(
    payload: CommitIngestRequest = Body(..., description="List of commits to ingest"),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Ingest commits and link them to Jira tickets by parsing ticket keys.

    - Links commits to `tickets` by matching Jira issue keys (e.g., PROJ-123) in the commit message
      or by an explicit `ticket_key`.
    - If `project_key` is provided, sets project accordingly; otherwise derived from ticket key when possible.
    - Creates the author `users` record if an `author_email` is provided and does not exist.
    - Idempotent on `commit_hash`.
    """
    if payload is None or not payload.commits:
        raise HTTPException(status_code=400, detail="No commits provided")

    stats = {"created": 0, "updated": 0, "skipped": 0, "linked": 0, "unlinked": 0}

    # Preload project map by key for faster lookups
    project_keys = {c.project_key for c in payload.commits if c.project_key}
    projects_by_key: Dict[str, ProjectModel] = {}
    if project_keys:
        for p in db.query(ProjectModel).filter(ProjectModel.key.in_(list(project_keys))).all():
            projects_by_key[p.key] = p

    users_by_email: Dict[str, UserModel] = {}

    for item in payload.commits:
        try:
            commit_hash = (item.commit_hash or "").strip()
            message = (item.message or "").strip()
            if not commit_hash or not message:
                stats["skipped"] += 1
                continue

            # Normalize committed_at to aware UTC datetime
            committed_at = item.committed_at
            if committed_at and committed_at.tzinfo is None:
                committed_at = committed_at.replace(tzinfo=timezone.utc)

            # Resolve author if email provided
            author_id: Optional[int] = None
            if item.author_email:
                email = item.author_email.strip().lower()
                user = users_by_email.get(email)
                if not user:
                    user = db.query(UserModel).filter(UserModel.email == email).first()
                    if not user:
                        # Create a minimal user record
                        display_name = item.author_name or item.author_email
                        user = UserModel(email=email, display_name=display_name, jira_id=None, avatar_url=None)
                        db.add(user)
                        db.flush()
                    users_by_email[email] = user
                author_id = user.id

            # Determine ticket (jira) key
            jira_key = None
            if item.ticket_key and ISSUE_KEY_RE.search(item.ticket_key):
                jira_key = ISSUE_KEY_RE.search(item.ticket_key).group(1)
            else:
                m = ISSUE_KEY_RE.search(message)
                if m:
                    jira_key = m.group(1)

            # Resolve ticket if possible
            ticket: Optional[TicketModel] = None
            if jira_key:
                ticket = db.query(TicketModel).filter(TicketModel.jira_id == jira_key).first()

            # Resolve project
            project: Optional[ProjectModel] = None
            if item.project_key:
                project = projects_by_key.get(item.project_key)
                if not project:
                    project = db.query(ProjectModel).filter(ProjectModel.key == item.project_key).first()
                    if project:
                        projects_by_key[item.project_key] = project
            elif ticket:
                project = db.query(ProjectModel).filter(ProjectModel.id == ticket.project_id).first()
            elif jira_key:
                # Derive from ticket key prefix
                derived_key = jira_key.split("-", 1)[0]
                project = projects_by_key.get(derived_key)
                if not project:
                    project = db.query(ProjectModel).filter(ProjectModel.key == derived_key).first()
                    if project:
                        projects_by_key[derived_key] = project

            # Upsert commit by hash
            existing: Optional[CommitModel] = db.query(CommitModel).filter(CommitModel.commit_hash == commit_hash).first()

            if existing:
                changed = False
                if existing.message != message:
                    existing.message = message
                    changed = True
                if author_id is not None and existing.author_id != author_id:
                    existing.author_id = author_id
                    changed = True
                if project and existing.project_id != project.id:
                    existing.project_id = project.id
                    changed = True
                if ticket and existing.ticket_id != ticket.id:
                    existing.ticket_id = ticket.id
                    changed = True
                if committed_at and existing.created_at != committed_at:
                    existing.created_at = committed_at
                    changed = True
                if changed:
                    db.add(existing)
                    stats["updated"] += 1
                else:
                    stats["skipped"] += 1
            else:
                new_commit = CommitModel(
                    commit_hash=commit_hash,
                    message=message,
                    author_id=author_id,
                    project_id=project.id if project else None,
                    ticket_id=ticket.id if ticket else None,
                    created_at=committed_at or datetime.now(timezone.utc),
                )
                db.add(new_commit)
                stats["created"] += 1

            if ticket:
                stats["linked"] += 1
            else:
                stats["unlinked"] += 1
        except Exception:
            # Skip malformed entries without failing entire batch
            stats["skipped"] += 1
            continue

    db.commit()
    return stats
