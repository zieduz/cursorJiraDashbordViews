from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional, Dict
from datetime import datetime

from ..models import ActivityEvent, ActivityEventType, User, Project
from ..schemas import PAPUserProjectMetric, PAPAuthorMetric
from ..config import settings

class PAPService:
    def __init__(self, db: Session):
        self.db = db
        self.tracked_emails = settings.pap_tracked_user_emails

    def get_comments_metrics(self, start_date: datetime, end_date: datetime) -> List[PAPUserProjectMetric]:
        """Aggregate Jira comments by user and project."""
        query = (
            self.db.query(
                User.display_name.label("user"),
                Project.name.label("project"),
                func.count(ActivityEvent.id).label("count")
            )
            .join(User, ActivityEvent.user_id == User.id)
            .join(Project, ActivityEvent.project_id == Project.id)
            .filter(ActivityEvent.event_type == ActivityEventType.JIRA_COMMENT)
            .filter(ActivityEvent.occurred_at_utc >= start_date)
            .filter(ActivityEvent.occurred_at_utc <= end_date)
        )
        
        if self.tracked_emails:
            query = query.filter(User.email.in_(self.tracked_emails))
            
        results = query.group_by(User.display_name, Project.name).all()
        return [
            PAPUserProjectMetric(user=r.user, project=r.project, count=r.count)
            for r in results
        ]

    def get_status_changes_metrics(self, start_date: datetime, end_date: datetime) -> List[PAPUserProjectMetric]:
        """Aggregate Jira status changes by user and project."""
        query = (
            self.db.query(
                User.display_name.label("user"),
                Project.name.label("project"),
                func.count(ActivityEvent.id).label("count")
            )
            .join(User, ActivityEvent.user_id == User.id)
            .join(Project, ActivityEvent.project_id == Project.id)
            .filter(ActivityEvent.event_type == ActivityEventType.JIRA_STATUS_CHANGE)
            .filter(ActivityEvent.occurred_at_utc >= start_date)
            .filter(ActivityEvent.occurred_at_utc <= end_date)
        )
        
        if self.tracked_emails:
            query = query.filter(User.email.in_(self.tracked_emails))
            
        results = query.group_by(User.display_name, Project.name).all()
        return [
            PAPUserProjectMetric(user=r.user, project=r.project, count=r.count)
            for r in results
        ]

    def get_mr_metrics(self, start_date: datetime, end_date: datetime) -> List[PAPAuthorMetric]:
        """Aggregate GitLab MRs created by author."""
        query = (
            self.db.query(
                User.display_name.label("author"),
                func.count(ActivityEvent.id).label("count")
            )
            .join(User, ActivityEvent.user_id == User.id)
            .filter(ActivityEvent.event_type == ActivityEventType.GITLAB_MR_CREATED)
            .filter(ActivityEvent.occurred_at_utc >= start_date)
            .filter(ActivityEvent.occurred_at_utc <= end_date)
        )
        
        if self.tracked_emails:
            query = query.filter(User.email.in_(self.tracked_emails))
            
        results = query.group_by(User.display_name).all()
        return [
            PAPAuthorMetric(author=r.author, count=r.count)
            for r in results
        ]


