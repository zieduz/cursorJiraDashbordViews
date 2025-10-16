from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, not_
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional
from ..models import Ticket, User, Project, Commit
import pandas as pd
import numpy as np


# Statuses considered non-resolved (compared case-insensitively)
NON_RESOLVED_STATUSES = set(
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
        group_by: str = "day",
    ) -> Dict:
        """Calculate comprehensive metrics"""
        def is_resolved_clause():
            return and_(
                Ticket.resolved_at.isnot(None),
                not_(func.lower(Ticket.status).in_(list(NON_RESOLVED_STATUSES))),
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
                func.lower(Ticket.status).in_(list(NON_RESOLVED_STATUSES)),
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
            group_by=group_by or "day",
        )
        
        # Commits per issue (filter by commit date within window, not ticket creation)
        commits_per_issue = self._get_commits_per_issue(
            start_date=start_date,
            end_date=end_date,
            project_ids=project_ids if project_ids else ([project_id] if project_id else None),
            user_id=user_id,
            status=status,
            customers=customers,
            labels=labels,
        )
        
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
                    not_(func.lower(Ticket.status).in_(list(NON_RESOLVED_STATUSES))),
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
                    not_(func.lower(Ticket.status).in_(list(NON_RESOLVED_STATUSES))),
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
        group_by: str = "day",
    ) -> List[Dict]:
        """Get ticket throughput over time aggregated by period.

        group_by: one of 'day', 'month', 'year'.

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

        def normalize_period_start(dt: datetime, gb: str) -> datetime:
            if gb == "year":
                return dt.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            if gb == "month":
                return dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            # day
            return dt.replace(hour=0, minute=0, second=0, microsecond=0)

        def next_period(dt: datetime, gb: str) -> datetime:
            if gb == "year":
                return dt.replace(year=dt.year + 1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            if gb == "month":
                if dt.month == 12:
                    return dt.replace(year=dt.year + 1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
                return dt.replace(month=dt.month + 1, day=1, hour=0, minute=0, second=0, microsecond=0)
            # day
            return dt + timedelta(days=1)

        gb = (group_by or "day").lower()
        if gb not in {"day", "month", "year"}:
            gb = "day"

        data: List[Dict] = []
        current_start = normalize_period_start(start_date, gb)
        # Ensure we start no later than requested window
        if current_start < start_date.replace(hour=0, minute=0, second=0, microsecond=0):
            current_start = start_date

        while current_start <= end_date:
            next_start = next_period(current_start, gb)

            created_count = (
                self.db.query(Ticket)
                .filter(
                    *non_time_filters,
                    Ticket.created_at >= current_start,
                    Ticket.created_at < next_start,
                )
                .count()
            )

            resolved_count = (
                self.db.query(Ticket)
                .filter(
                    *non_time_filters,
                    Ticket.resolved_at.isnot(None),
                    Ticket.resolved_at >= current_start,
                    Ticket.resolved_at < next_start,
                    not_(func.lower(Ticket.status).in_(list(NON_RESOLVED_STATUSES))),
                )
                .count()
            )

            # Use first day of the period for the label to ensure valid date parsing on frontend
            data.append(
                {
                    "date": current_start.strftime("%Y-%m-%d"),
                    "created": created_count,
                    "resolved": resolved_count,
                }
            )

            current_start = next_start

        return data
    
    def get_cumulative_flow(
        self,
        start_date: datetime,
        end_date: datetime,
        project_ids: Optional[List[int]] = None,
        user_id: Optional[int] = None,
        status: Optional[str] = None,
        customers: Optional[List[str]] = None,
        labels: Optional[List[str]] = None,
        group_by: str = "day",
    ) -> List[Dict]:
        """Compute Cumulative Flow data using created/resolved counts.

        Returns a list of points with cumulative 'open' (created - resolved, non-negative)
        and cumulative 'done' (resolved) per period.
        """
        throughput = self._get_ticket_throughput(
            project_ids=project_ids,
            user_id=user_id,
            status=status,
            customers=customers,
            labels=labels,
            start_date=start_date,
            end_date=end_date,
            group_by=group_by or "day",
        )

        cumulative_data: List[Dict] = []
        cum_created = 0
        cum_resolved = 0
        for point in throughput:
            cum_created += int(point.get("created", 0) or 0)
            cum_resolved += int(point.get("resolved", 0) or 0)
            open_count = max(cum_created - cum_resolved, 0)
            cumulative_data.append(
                {
                    "date": point["date"],
                    "open": open_count,
                    "done": cum_resolved,
                }
            )

        return cumulative_data

    def get_cycle_time_metrics(
        self,
        start_date: datetime,
        end_date: datetime,
        project_ids: Optional[List[int]] = None,
        user_id: Optional[int] = None,
        customers: Optional[List[str]] = None,
        labels: Optional[List[str]] = None,
    ) -> Dict:
        """Compute Control Chart (cycle time) data for resolved issues.

        Cycle time is approximated as hours spent if available, otherwise
        the elapsed time between created_at and resolved_at. Returned in days.
        """
        non_time_filters: List = [
            Ticket.resolved_at.isnot(None),
        ]
        if project_ids:
            non_time_filters.append(Ticket.project_id.in_(project_ids))
        if user_id:
            non_time_filters.append(Ticket.assignee_id == user_id)
        if customers:
            non_time_filters.append(Ticket.customer.in_(customers))
        if labels:
            label_clauses = [Ticket.labels.like(f"%,{lbl},%") for lbl in labels]
            if label_clauses:
                non_time_filters.append(or_(*label_clauses))

        tickets = (
            self.db.query(Ticket)
            .filter(
                *non_time_filters,
                Ticket.resolved_at >= start_date,
                Ticket.resolved_at <= end_date,
                not_(func.lower(Ticket.status).in_(list(NON_RESOLVED_STATUSES))),
            )
            .all()
        )

        points: List[Dict] = []
        values: List[float] = []
        for t in tickets:
            if t.time_spent is not None:
                hours = float(t.time_spent)
            else:
                # Compute hours between created and resolved
                hours = float((t.resolved_at - t.created_at).total_seconds() / 3600.0)
            days = max(hours / 24.0, 0.0)
            values.append(days)
            points.append(
                {
                    "jira_id": t.jira_id,
                    "cycle_time_days": days,
                    "resolved_at": t.resolved_at.isoformat(),
                }
            )

        def percentile(vals: List[float], p: float) -> float:
            if not vals:
                return 0.0
            sv = sorted(vals)
            k = (len(sv) - 1) * p
            f = int(k)
            c = min(f + 1, len(sv) - 1)
            if f == c:
                return sv[int(k)]
            d0 = sv[f] * (c - k)
            d1 = sv[c] * (k - f)
            return d0 + d1

        average_days = float(np.mean(values)) if values else 0.0
        p85_days = float(percentile(values, 0.85)) if values else 0.0
        p95_days = float(percentile(values, 0.95)) if values else 0.0

        return {
            "points": points,
            "average_days": average_days,
            "p85_days": p85_days,
            "p95_days": p95_days,
        }

    def _get_commits_per_issue(
        self,
        start_date: datetime,
        end_date: datetime,
        project_ids: Optional[List[int]] = None,
        user_id: Optional[int] = None,
        status: Optional[str] = None,
        customers: Optional[List[str]] = None,
        labels: Optional[List[str]] = None,
    ) -> List[Dict]:
        """Get commits per issue statistics.

        Important: Filter by Commit.created_at within the requested window.
        Apply non-time filters (project, user, status, customers, labels) on the Ticket side.
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

        query = (
            self.db.query(
                Ticket.jira_id,
                func.count(Commit.id).label('commit_count')
            )
            .join(Commit, Ticket.id == Commit.ticket_id)
            .filter(
                *non_time_filters,
                Commit.created_at >= start_date,
                Commit.created_at <= end_date,
            )
            .group_by(Ticket.id, Ticket.jira_id)
        )

        results: List[Dict] = []
        for row in query.all():
            results.append({
                "ticket_id": row.jira_id,
                "commit_count": row.commit_count or 0,
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
                not_(func.lower(Ticket.status).in_(list(NON_RESOLVED_STATUSES))),
            )
            .count()
        )
        
        on_time_resolved = (
            self.db.query(Ticket)
            .filter(
                *filters,
                Ticket.resolved_at.isnot(None),
                not_(func.lower(Ticket.status).in_(list(NON_RESOLVED_STATUSES))),
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
            not_(func.lower(Ticket.status).in_(list(NON_RESOLVED_STATUSES))),
        )
        
        result = query.scalar()
        return float(result) if result else 0.0