"""Pydantic schemas for API requests and responses.

These models define the shape of data exchanged between the frontend and the
FastAPI backend, separate from the database ORM models.
"""
from pydantic import BaseModel, field_validator
from typing import Optional, List
from datetime import datetime


class ProjectBase(BaseModel):
    key: str
    name: str
    description: Optional[str] = None


class ProjectCreate(ProjectBase):
    pass


class Project(ProjectBase):
    """Project response model returned by the API."""
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserBase(BaseModel):
    jira_id: str
    email: str
    display_name: str
    avatar_url: Optional[str] = None


class UserCreate(UserBase):
    pass


class User(UserBase):
    """User response model returned by the API."""
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class TicketBase(BaseModel):
    jira_id: str
    summary: str
    description: Optional[str] = None
    status: str
    priority: Optional[str] = None
    issue_type: Optional[str] = None
    customer: Optional[str] = None
    labels: Optional[List[str]] = None
    story_points: Optional[int] = None
    time_estimate: Optional[float] = None
    time_spent: Optional[float] = None


class TicketCreate(TicketBase):
    project_id: int
    assignee_id: Optional[int] = None


class Ticket(TicketBase):
    """Ticket/issue response model returned by the API."""
    id: int
    project_id: int
    assignee_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

    # Normalize labels from comma-delimited string in DB to list for API
    @field_validator("labels", mode="before")
    @classmethod
    def _normalize_labels(cls, v):
        """Normalize labels field from DB string to list for API output."""
        if v is None:
            return None
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            stripped = v.strip(',')
            if not stripped:
                return []
            return [s for s in stripped.split(',') if s]
        return None


class CommitBase(BaseModel):
    commit_hash: str
    message: str


class CommitCreate(CommitBase):
    ticket_id: int
    project_id: int
    author_id: int


class Commit(CommitBase):
    """Commit response model linked to a ticket and project."""
    id: int
    ticket_id: int
    project_id: int
    author_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# Metrics and Forecast Schemas
class MetricsResponse(BaseModel):
    """Aggregate metrics used by dashboard KPIs and charts."""
    total_tickets: int
    tickets_created: int
    tickets_resolved: int
    tickets_in_progress: int
    productivity_per_user: List[dict]
    productivity_per_project: List[dict]
    ticket_throughput: List[dict]
    commits_per_issue: List[dict]
    sla_compliance: float
    average_resolution_time: float


class ForecastResponse(BaseModel):
    """Forecast output including daily velocity and confidence intervals."""
    predicted_velocity: List[dict]
    confidence_interval: List[dict]
    trend: str
    next_sprint_prediction: dict


class TicketFilters(BaseModel):
    """Common filter parameters for ticket list endpoints."""
    project_id: Optional[int] = None
    user_id: Optional[int] = None
    status: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = 100
    offset: int = 0