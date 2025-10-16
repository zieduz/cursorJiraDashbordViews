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
    - customers: [str]
    - labels: [str]
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

    # Distinct customers
    customers_rows = (
        db.query(TicketModel.customer)
        .filter(TicketModel.customer.isnot(None))
        .distinct()
        .order_by(TicketModel.customer.asc())
        .all()
    )
    customers: List[str] = [row[0] for row in customers_rows if row[0]]

    # Distinct labels (flatten from comma-delimited storage)
    labels_set: set[str] = set()
    labels_rows = (
        db.query(TicketModel.labels)
        .filter(TicketModel.labels.isnot(None))
        .all()
    )
    for (labels_str,) in labels_rows:
        for lbl in (labels_str or "").strip(',').split(','):
            if lbl:
                labels_set.add(lbl)
    labels: List[str] = sorted(labels_set)

    return {
        "projects": projects,
        "users": users,
        "statuses": statuses,
        "customers": customers,
        "labels": labels,
    }
