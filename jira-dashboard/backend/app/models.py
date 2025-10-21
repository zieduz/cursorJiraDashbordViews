"""ORM models defining projects, users, tickets, commits, and activity events.

These SQLAlchemy models back the Jira Performance Dashboard. Relationships are
kept simple to facilitate analytical queries for metrics and charts.
"""
from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, ForeignKey, Text, Enum as SQLEnum, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base
from enum import Enum as PyEnum
import uuid
try:
    # Prefer Postgres-native types when available (dev/prod default)
    from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB as PG_JSONB
except Exception:  # pragma: no cover - fallback for non-Postgres envs
    PG_UUID = None  # type: ignore
    PG_JSONB = None  # type: ignore


class Project(Base):
    """Project entity representing a Jira project.

    Contains a stable key, human-readable name, and optional description.
    """
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(50), unique=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    tickets = relationship("Ticket", back_populates="project")
    commits = relationship("Commit", back_populates="project")


class User(Base):
    """User entity representing a Jira user/assignee.

    Stores identifiers and display information used in metrics aggregation.
    """
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    jira_id = Column(String(100), unique=True, index=True)
    email = Column(String(255), unique=True, index=True)
    display_name = Column(String(200), nullable=False)
    avatar_url = Column(String(500))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    assigned_tickets = relationship("Ticket", back_populates="assignee")
    commits = relationship("Commit", back_populates="author")


class Ticket(Base):
    """Ticket/issue entity synchronized from Jira.

    Includes lifecycle timestamps to support cycle/lead-time calculations and
    additional attributes used for filtering and grouping.
    """
    __tablename__ = "tickets"
    
    id = Column(Integer, primary_key=True, index=True)
    jira_id = Column(String(50), unique=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    assignee_id = Column(Integer, ForeignKey("users.id"))
    
    summary = Column(String(500), nullable=False)
    description = Column(Text)
    status = Column(String(50), nullable=False)  # To Do, In Progress, Done, etc.
    priority = Column(String(20))  # High, Medium, Low
    issue_type = Column(String(50))  # Story, Bug, Task, etc.
    # Customer (from Jira custom field, e.g., customfield_12567)
    customer = Column(String(200))
    # Comma-delimited labels string with leading/trailing commas for LIKE matching: ",bug,backend,"
    labels = Column(Text)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    # First time the ticket entered 'In Progress' (start of active work)
    started_at = Column(DateTime(timezone=True))
    resolved_at = Column(DateTime(timezone=True))
    
    story_points = Column(Integer)
    time_estimate = Column(Float)  # in hours
    time_spent = Column(Float)  # in hours
    
    project = relationship("Project", back_populates="tickets")
    assignee = relationship("User", back_populates="assigned_tickets")
    commits = relationship("Commit", back_populates="ticket")


class Commit(Base):
    """Commit entity linked to a ticket and project.

    Enables commits-per-issue and related productivity metrics.
    """
    __tablename__ = "commits"
    
    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"))
    project_id = Column(Integer, ForeignKey("projects.id"))
    author_id = Column(Integer, ForeignKey("users.id"))
    
    commit_hash = Column(String(40), unique=True, index=True)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    ticket = relationship("Ticket", back_populates="commits")
    project = relationship("Project", back_populates="commits")
    author = relationship("User", back_populates="commits")


# --- Activity models for heatmap analytics ---

class ActivitySource(str, PyEnum):
    JIRA = "jira"
    GITLAB = "gitlab"


class ActivityEventType(str, PyEnum):
    # Jira events
    JIRA_COMMENT = "jira_comment"
    JIRA_STATUS_CHANGE = "jira_status_change"
    # GitLab events
    GITLAB_COMMIT_CREATED = "gitlab_commit_created"
    GITLAB_MR_CREATED = "gitlab_mr_created"
    GITLAB_MR_APPROVED = "gitlab_mr_approved"
    GITLAB_MR_MERGED = "gitlab_mr_merged"


class ActivityEvent(Base):
    """Raw activity events across sources for time-based analytics.

    Minimal subset to power heatmap queries; additional fields can be introduced
    later without breaking API shape.
    """

    __tablename__ = "activity_events"

    # Use UUID when Postgres dialect available; otherwise fall back to text id
    if PG_UUID is not None:
        id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    else:  # pragma: no cover
        id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    source = Column(SQLEnum(ActivitySource), nullable=False, index=True)
    event_type = Column(SQLEnum(ActivityEventType), nullable=False, index=True)
    occurred_at_utc = Column(DateTime(timezone=True), nullable=False, index=True)

    # Relations to existing models (nullable to ease ingestion)
    project_id = Column(Integer, ForeignKey("projects.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    ticket_id = Column(Integer, ForeignKey("tickets.id"))

    # Optional JSON metadata when Postgres
    if PG_JSONB is not None:
        extra_data = Column(PG_JSONB, nullable=False, server_default='{}')  # type: ignore
    else:  # pragma: no cover
        extra_data = Column(Text)  # type: ignore

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    project = relationship("Project", backref="activity_events")
    user = relationship("User", foreign_keys=[user_id], backref="activity_events")
    ticket = relationship("Ticket", backref="activity_events")

    __table_args__ = (
        Index("idx_activity_events_composite", "source", "event_type", "occurred_at_utc"),
    )