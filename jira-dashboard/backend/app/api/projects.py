from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..schemas import Project as ProjectSchema
from ..models import Project as ProjectModel


router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.get("/", response_model=List[ProjectSchema])
async def list_projects(db: Session = Depends(get_db)) -> List[ProjectSchema]:
    """Return all projects stored in the database.

    Used by the frontend filter to populate the Project dropdown.
    """
    return db.query(ProjectModel).order_by(ProjectModel.name.asc()).all()
