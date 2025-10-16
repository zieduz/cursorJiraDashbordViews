from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Dict, Any, List

from ..database import get_db
from ..models import Project as ProjectModel, User as UserModel, Ticket as TicketModel


router = APIRouter(prefix="/api/filters", tags=["filters"])


@router.get("/options")
async def get_filter_options(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Return dynamic filter options derived from the database.

    - projects: [{ id, name, key }]
    - users: [{ id, display_name }]
    - statuses: [str]
    """
    projects_rows = (
        db.query(ProjectModel.id, ProjectModel.name, ProjectModel.key)
        .order_by(ProjectModel.name.asc())
        .all()
    )
    projects: List[Dict[str, Any]] = [
        {"id": row.id, "name": row.name, "key": row.key} for row in projects_rows
    ]

    users_rows = (
        db.query(UserModel.id, UserModel.display_name)
        .order_by(UserModel.display_name.asc())
        .all()
    )
    users: List[Dict[str, Any]] = [
        {"id": row.id, "display_name": row.display_name} for row in users_rows
    ]

    statuses_rows = (
        db.query(TicketModel.status)
        .filter(TicketModel.status.isnot(None))
        .distinct()
        .order_by(TicketModel.status.asc())
        .all()
    )
    statuses: List[str] = [row[0] for row in statuses_rows if row[0]]

    return {
        "projects": projects,
        "users": users,
        "statuses": statuses,
    }
