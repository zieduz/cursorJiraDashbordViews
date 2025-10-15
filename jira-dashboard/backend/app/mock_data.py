import random
import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Dict
import asyncio
from sqlalchemy.orm import Session
from .models import Project, User, Ticket, Commit
from .database import SessionLocal


class MockDataGenerator:
    def __init__(self):
        self.projects = [
            {"key": "PROJ1", "name": "E-commerce Platform", "description": "Main e-commerce application"},
            {"key": "PROJ2", "name": "Mobile App", "description": "iOS and Android mobile application"},
            {"key": "PROJ3", "name": "Analytics Dashboard", "description": "Data analytics and reporting dashboard"}
        ]
        
        self.users = [
            {"jira_id": "user1", "email": "john.doe@company.com", "display_name": "John Doe"},
            {"jira_id": "user2", "email": "jane.smith@company.com", "display_name": "Jane Smith"},
            {"jira_id": "user3", "email": "mike.johnson@company.com", "display_name": "Mike Johnson"},
            {"jira_id": "user4", "email": "sarah.wilson@company.com", "display_name": "Sarah Wilson"},
            {"jira_id": "user5", "email": "david.brown@company.com", "display_name": "David Brown"}
        ]
        
        self.issue_types = ["Story", "Bug", "Task", "Epic", "Sub-task"]
        self.priorities = ["High", "Medium", "Low", "Critical"]
        self.statuses = ["To Do", "In Progress", "Code Review", "Testing", "Done"]
        
        # Track generated Jira IDs within a run to avoid duplicates
        self.generated_jira_ids = set()
        
        self.commit_messages = [
            "Fix login validation bug",
            "Add user authentication",
            "Implement new feature",
            "Update database schema",
            "Refactor code structure",
            "Add unit tests",
            "Fix responsive design",
            "Optimize performance",
            "Update documentation",
            "Fix merge conflict"
        ]
    
    async def generate_data(self, days_back: int = 90):
        """Generate mock data for the specified number of days"""
        db = SessionLocal()
        try:
            # Clear existing data
            db.query(Commit).delete()
            db.query(Ticket).delete()
            db.query(User).delete()
            db.query(Project).delete()
            db.commit()
            
            # Create projects
            projects = []
            for project_data in self.projects:
                project = Project(**project_data)
                db.add(project)
                projects.append(project)
            db.commit()
            
            # Create users
            users = []
            for user_data in self.users:
                user = User(**user_data)
                db.add(user)
                users.append(user)
            db.commit()
            
            # Generate tickets over the specified period
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=days_back)
            
            tickets = []
            current_date = start_date
            
            while current_date <= end_date:
                # Generate 0-5 tickets per day
                tickets_per_day = random.randint(0, 5)
                
                for _ in range(tickets_per_day):
                    ticket = self._create_random_ticket(db, projects, users, current_date)
                    db.add(ticket)
                    tickets.append(ticket)
                
                current_date += timedelta(days=1)
            
            db.commit()
            
            # Generate commits for tickets
            for ticket in tickets:
                # 0-3 commits per ticket
                commits_count = random.randint(0, 3)
                
                for _ in range(commits_count):
                    commit = self._create_random_commit(ticket, users)
                    db.add(commit)
            
            db.commit()
            
            print(f"Generated mock data: {len(projects)} projects, {len(users)} users, {len(tickets)} tickets")
            
        finally:
            db.close()
    
    def _create_random_ticket(self, db: Session, projects: List[Project], users: List[User], created_date: datetime) -> Ticket:
        """Create a random ticket"""
        project = random.choice(projects)
        assignee = random.choice(users) if random.random() > 0.2 else None  # 20% unassigned
        
        # Random resolution time (0-30 days after creation)
        resolution_days = random.randint(0, 30) if random.random() > 0.3 else None  # 30% unresolved
        resolved_at = created_date + timedelta(days=resolution_days) if resolution_days else None
        
        # Random status based on resolution
        if resolved_at and resolved_at <= datetime.now(timezone.utc):
            status = "Done"
        elif created_date + timedelta(days=1) <= datetime.now(timezone.utc):
            status = random.choice(["In Progress", "Code Review", "Testing"])
        else:
            status = "To Do"
        
        return Ticket(
            jira_id=self._generate_unique_jira_id(db, project.key),
            project_id=project.id,
            assignee_id=assignee.id if assignee else None,
            summary=f"Task {random.randint(1, 1000)}: {random.choice(['Implement', 'Fix', 'Add', 'Update', 'Refactor'])} {random.choice(['feature', 'bug', 'component', 'module'])}",
            description=f"Description for task {random.randint(1, 1000)}",
            status=status,
            priority=random.choice(self.priorities),
            issue_type=random.choice(self.issue_types),
            story_points=random.choice([1, 2, 3, 5, 8, 13, 21]) if random.random() > 0.3 else None,
            time_estimate=random.uniform(1, 40),
            time_spent=random.uniform(0, 40) if resolved_at else None,
            created_at=created_date,
            resolved_at=resolved_at
        )
    
    def _generate_unique_jira_id(self, db: Session, project_key: str) -> str:
        """Generate a Jira ID unique across current run and database."""
        # Use a larger numeric space to minimize collisions, plus active checks
        while True:
            candidate = f"{project_key}-{random.randint(1000, 999999)}"
            if candidate in self.generated_jira_ids:
                continue
            # Defensive: also check the database in case it's not empty
            exists = db.query(Ticket).filter(Ticket.jira_id == candidate).first()
            if exists:
                continue
            self.generated_jira_ids.add(candidate)
            return candidate

    def _create_random_commit(self, ticket: Ticket, users: List[User]) -> Commit:
        """Create a random commit for a ticket"""
        author = random.choice(users)
        commit_date = ticket.created_at + timedelta(
            days=random.randint(0, (datetime.now(timezone.utc) - ticket.created_at).days)
        )
        
        return Commit(
            ticket_id=ticket.id,
            project_id=ticket.project_id,
            author_id=author.id,
            commit_hash=uuid.uuid4().hex,
            message=random.choice(self.commit_messages),
            created_at=commit_date
        )


async def generate_mock_data():
    """Generate mock data for development"""
    generator = MockDataGenerator()
    await generator.generate_data(90)