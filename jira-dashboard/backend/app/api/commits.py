from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator
from typing import List, Optional
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Commit as CommitModel, Ticket as TicketModel, Project as ProjectModel, User as UserModel


router = APIRouter(prefix="/api/commits", tags=["commits"])


def _parse_iso_datetime(value: str) -> Optional[datetime]:
    if not value:
        return None
    v = value.strip()
    try:
        # Accept 'Z' suffix
        if v.endswith("Z"):
            v = v[:-1] + "+00:00"
        dt = datetime.fromisoformat(v)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


def _find_or_create_user(db: Session, email: Optional[str], display_name: Optional[str]) -> Optional[UserModel]:
    if not email and not display_name:
        return None
    user: Optional[UserModel] = None
    if email:
        user = db.query(UserModel).filter(UserModel.email == email).first()
    if not user and display_name:
        # As a fallback, try to find by display name (not unique, so best-effort)
        user = db.query(UserModel).filter(UserModel.display_name == display_name).first()
    if user:
        # Update display name if we have a better one
        name = display_name or user.display_name
        if name and user.display_name != name:
            user.display_name = name
            db.add(user)
        return user
    # Create new user record with provided info
    user = UserModel(
        jira_id=None,
        email=email,
        display_name=display_name or (email or "Unknown"),
        avatar_url=None,
    )
    db.add(user)
    db.flush()
    return user


def _extract_jira_keys(message: str) -> List[str]:
    # Match standard JIRA keys like ABC-123, OPS-9, TEAM1-456
    import re

    if not message:
        return []
    pattern = re.compile(r"\b([A-Z][A-Z0-9]+-\d+)\b")
    keys = pattern.findall(message.upper())
    # Preserve order but remove duplicates
    seen = set()
    ordered: List[str] = []
    for k in keys:
        if k not in seen:
            seen.add(k)
            ordered.append(k)
    return ordered


class CommitIngestItem(BaseModel):
    commit_hash: str
    message: str
    created_at: Optional[str] = None
    author_email: Optional[str] = None
    author_name: Optional[str] = None
    project_key: Optional[str] = None

    @field_validator("commit_hash")
    @classmethod
    def _validate_hash(cls, v: str) -> str:
        v = (v or "").strip()
        if not v:
            raise ValueError("commit_hash is required")
        return v


class CommitIngestRequest(BaseModel):
    commits: List[CommitIngestItem]


@router.post("/ingest", summary="Ingest commits and link to Jira tickets")
def ingest_commits(payload: CommitIngestRequest, db: Session = Depends(get_db)):
    """Ingest commit metadata and associate with Jira tickets by parsing keys from messages.

    Notes:
    - A commit is uniquely identified by commit_hash. If it already exists, it will be skipped.
    - If a commit message contains multiple Jira keys, only the first is used for linkage.
    - When project_key is omitted, the project is derived from the linked ticket.
    """
    if not payload or not payload.commits:
        raise HTTPException(status_code=400, detail="No commits provided")

    created = 0
    updated = 0
    skipped = 0
    unmatched = 0

    for item in payload.commits:
        # De-duplicate by commit_hash
        existing = db.query(CommitModel).filter(CommitModel.commit_hash == item.commit_hash).first()
        if existing:
            skipped += 1
            continue

        jira_keys = _extract_jira_keys(item.message)
        if not jira_keys:
            unmatched += 1
            continue

        ticket: Optional[TicketModel] = (
            db.query(TicketModel).filter(TicketModel.jira_id == jira_keys[0]).first()
        )
        if not ticket:
            unmatched += 1
            continue

        # Determine project
        project: Optional[ProjectModel] = None
        if item.project_key:
            project = db.query(ProjectModel).filter(ProjectModel.key == item.project_key).first()
        if not project:
            project = db.query(ProjectModel).filter(ProjectModel.id == ticket.project_id).first()

        # Determine author
        author = _find_or_create_user(db, email=item.author_email, display_name=item.author_name)

        created_dt = _parse_iso_datetime(item.created_at) if item.created_at else datetime.now(timezone.utc)

        commit = CommitModel(
            ticket_id=ticket.id,
            project_id=project.id if project else ticket.project_id,
            author_id=author.id if author else None,
            commit_hash=item.commit_hash,
            message=item.message,
            created_at=created_dt,
        )
        db.add(commit)
        created += 1

    db.commit()

    return {
        "created": created,
        "updated": updated,
        "skipped": skipped,
        "unmatched": unmatched,
        "total": len(payload.commits),
    }
