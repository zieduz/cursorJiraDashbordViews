from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, not_
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional
from ..models import Ticket, User, Project, Commit
import pandas as pd
import numpy as np


class MetricsService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_metrics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        project_id: Optional[int] = None,
        user_id: Optional[int] = None,
        status: Optional[str] = None,
        project_ids: Optional[List[int]] = None,
        customers: Optional[List[str]] = None,
        labels: Optional[List[str]] = None,
    ) -> Dict:
        """Calculate comprehensive metrics"""
        # Define non-resolved statuses (case-insensitive match)
        non_resolved_statuses = set(
            s.lower()
            for s in [
                "ready for dev",
                "open",
                "in progress",
                "waiting",
                "waiting for factory",
                "created",
                "reopened",
                "to be configured",
                "blocked",
                "confirmed",
                "draft",
                "pending",
                "in coding",
                "waiting for information",
            ]
        )

        def is_resolved_clause():
            return and_(
                Ticket.resolved_at.isnot(None),
                not_(func.lower(Ticket.status).in_(list(non_resolved_statuses))),
            )
        
        # Set default date range if not provided
        if not end_date:
            end_date = datetime.now(timezone.utc)
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        # Base query filters
        filters = [Ticket.created_at >= start_date, Ticket.created_at <= end_date]
        if project_ids:
            filters.append(Ticket.project_id.in_(project_ids))
        elif project_id:
            filters.append(Ticket.project_id == project_id)
        if user_id:
            filters.append(Ticket.assignee_id == user_id)
        if status:
            filters.append(Ticket.status == status)
        if customers:
            filters.append(Ticket.customer.in_(customers))
        if labels:
            # labels stored as comma-delimited string, match any
            label_clauses = [Ticket.labels.like(f"%,{lbl},%") for lbl in labels]
            if label_clauses:
                filters.append(or_(*label_clauses))
        
        # Total tickets
        total_tickets = self.db.query(Ticket).filter(*filters).count()
        
        # Tickets by status
        tickets_created = self.db.query(Ticket).filter(*filters).count()
        tickets_resolved = (
            self.db.query(Ticket)
            .filter(
                *filters,
                is_resolved_clause(),
            )
            .count()
        )
        tickets_in_progress = (
            self.db.query(Ticket)
            .filter(
                *filters,
                func.lower(Ticket.status).in_(list(non_resolved_statuses)),
            )
            .count()
        )
        
        # Productivity per user
        productivity_per_user = self._get_productivity_per_user(filters)
        
        # Productivity per project
        productivity_per_project = self._get_productivity_per_project(filters)
        
        # Ticket throughput over time
        ticket_throughput = self._get_ticket_throughput(
            project_ids=project_ids if project_ids else ([project_id] if project_id else None),
            user_id=user_id,
            status=status,
            customers=customers,
            labels=labels,
            start_date=start_date,
            end_date=end_date,
        )
        
        # Commits per issue
        commits_per_issue = self._get_commits_per_issue(filters)
        
        # SLA compliance (tickets resolved on time)
        sla_compliance = self._get_sla_compliance(filters)
        
        # Average resolution time
        avg_resolution_time = self._get_average_resolution_time(filters)
        
        return {
            "total_tickets": total_tickets,
            "tickets_created": tickets_created,
            "tickets_resolved": tickets_resolved,
            "tickets_in_progress": tickets_in_progress,
            "productivity_per_user": productivity_per_user,
            "productivity_per_project": productivity_per_project,
            "ticket_throughput": ticket_throughput,
            "commits_per_issue": commits_per_issue,
            "sla_compliance": sla_compliance,
            "average_resolution_time": avg_resolution_time
        }
    
    def _get_productivity_per_user(self, filters: List) -> List[Dict]:
        """Calculate productivity metrics per user"""
        query = self.db.query(
            User.display_name,
            func.count(Ticket.id).label('tickets_created'),
            func.count(Ticket.id).filter(
                and_(
                    Ticket.resolved_at.isnot(None),
                    not_(func.lower(Ticket.status).in_(list(non_resolved_statuses))),
                )
            ).label('tickets_resolved'),
            func.avg(Ticket.story_points).label('avg_story_points'),
            func.avg(Ticket.time_spent).label('avg_time_spent')
        ).join(Ticket, User.id == Ticket.assignee_id).filter(*filters).group_by(User.id, User.display_name)
        
        results = []
        for row in query.all():
            results.append({
                "user": row.display_name,
                "tickets_created": row.tickets_created or 0,
                "tickets_resolved": row.tickets_resolved or 0,
                "avg_story_points": float(row.avg_story_points) if row.avg_story_points else 0,
                "avg_time_spent": float(row.avg_time_spent) if row.avg_time_spent else 0
            })
        
        return results
    
    def _get_productivity_per_project(self, filters: List) -> List[Dict]:
        """Calculate productivity metrics per project"""
        query = self.db.query(
            Project.name,
            func.count(Ticket.id).label('tickets_created'),
            func.count(Ticket.id).filter(
                and_(
                    Ticket.resolved_at.isnot(None),
                    not_(func.lower(Ticket.status).in_(list(non_resolved_statuses))),
                )
            ).label('tickets_resolved'),
            func.avg(Ticket.story_points).label('avg_story_points'),
            func.sum(Ticket.story_points).label('total_story_points')
        ).join(Ticket, Project.id == Ticket.project_id).filter(*filters).group_by(Project.id, Project.name)
        
        results = []
        for row in query.all():
            results.append({
                "project": row.name,
                "tickets_created": row.tickets_created or 0,
                "tickets_resolved": row.tickets_resolved or 0,
                "avg_story_points": float(row.avg_story_points) if row.avg_story_points else 0,
                "total_story_points": float(row.total_story_points) if row.total_story_points else 0
            })
        
        return results
    
    def _get_ticket_throughput(
        self,
        project_ids: Optional[List[int]],
        user_id: Optional[int],
        status: Optional[str],
        customers: Optional[List[str]],
        labels: Optional[List[str]],
        start_date: datetime,
        end_date: datetime,
    ) -> List[Dict]:
        """Get ticket throughput over time (daily).

        Note: We intentionally do NOT constrain resolved counts by created_at.
        """
        non_time_filters: List = []
        if project_ids:
            non_time_filters.append(Ticket.project_id.in_(project_ids))
        if user_id:
            non_time_filters.append(Ticket.assignee_id == user_id)
        if status:
            non_time_filters.append(Ticket.status == status)
        if customers:
            non_time_filters.append(Ticket.customer.in_(customers))
        if labels:
            label_clauses = [Ticket.labels.like(f"%,{lbl},%") for lbl in labels]
            if label_clauses:
                non_time_filters.append(or_(*label_clauses))

        daily_data: List[Dict] = []
        current_date = start_date

        while current_date <= end_date:
            next_date = current_date + timedelta(days=1)

            created_count = (
                self.db.query(Ticket)
                .filter(
                    *non_time_filters,
                    Ticket.created_at >= current_date,
                    Ticket.created_at < next_date,
                )
                .count()
            )

            resolved_count = (
                self.db.query(Ticket)
                .filter(
                    *non_time_filters,
                    Ticket.resolved_at.isnot(None),
                    Ticket.resolved_at >= current_date,
                    Ticket.resolved_at < next_date,
                    not_(func.lower(Ticket.status).in_(list(non_resolved_statuses))),
                )
                .count()
            )

            daily_data.append(
                {
                    "date": current_date.strftime("%Y-%m-%d"),
                    "created": created_count,
                    "resolved": resolved_count,
                }
            )

            current_date = next_date

        return daily_data
    
    def _get_commits_per_issue(self, filters: List) -> List[Dict]:
        """Get commits per issue statistics"""
        query = self.db.query(
            Ticket.jira_id,
            func.count(Commit.id).label('commit_count')
        ).join(Commit, Ticket.id == Commit.ticket_id).filter(*filters).group_by(Ticket.id, Ticket.jira_id)
        
        results = []
        for row in query.all():
            results.append({
                "ticket_id": row.jira_id,
                "commit_count": row.commit_count or 0
            })
        
        return results
    
    def _get_sla_compliance(self, filters: List) -> float:
        """Calculate SLA compliance percentage"""
        # Assuming SLA is 7 days for resolution
        sla_days = 7
        sla_cutoff = datetime.now(timezone.utc) - timedelta(days=sla_days)
        
        total_resolved = (
            self.db.query(Ticket)
            .filter(
                *filters,
                Ticket.resolved_at.isnot(None),
                not_(func.lower(Ticket.status).in_(list(non_resolved_statuses))),
            )
            .count()
        )
        
        on_time_resolved = (
            self.db.query(Ticket)
            .filter(
                *filters,
                Ticket.resolved_at.isnot(None),
                not_(func.lower(Ticket.status).in_(list(non_resolved_statuses))),
                Ticket.resolved_at <= Ticket.created_at + timedelta(days=sla_days),
            )
            .count()
        )
        
        if total_resolved == 0:
            return 0.0
        
        return (on_time_resolved / total_resolved) * 100
    
    def _get_average_resolution_time(self, filters: List) -> float:
        """Calculate average resolution time in hours"""
        query = self.db.query(
            func.avg(
                func.extract('epoch', Ticket.resolved_at - Ticket.created_at) / 3600
            )
        ).filter(
            *filters,
            Ticket.resolved_at.isnot(None),
            not_(func.lower(Ticket.status).in_(list(non_resolved_statuses))),
        )
        
        result = query.scalar()
        return float(result) if result else 0.0