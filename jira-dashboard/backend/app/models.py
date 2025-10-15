from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base


class Project(Base):
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(50), unique=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    tickets = relationship("Ticket", back_populates="project")
    commits = relationship("Commit", back_populates="project")


class User(Base):
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
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    resolved_at = Column(DateTime(timezone=True))
    
    story_points = Column(Integer)
    time_estimate = Column(Float)  # in hours
    time_spent = Column(Float)  # in hours
    
    project = relationship("Project", back_populates="tickets")
    assignee = relationship("User", back_populates="assigned_tickets")
    commits = relationship("Commit", back_populates="ticket")


class Commit(Base):
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