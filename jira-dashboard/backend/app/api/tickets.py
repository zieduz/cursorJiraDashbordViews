from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
from datetime import datetime
from ..database import get_db
from ..schemas import Ticket, TicketFilters
from ..models import Ticket as TicketModel

router = APIRouter(prefix="/api/tickets", tags=["tickets"])


@router.get("/", response_model=List[Ticket])
async def get_tickets(
    project_id: Optional[int] = Query(None, description="Filter by project ID"),
    project_ids: Optional[str] = Query(None, description="Comma-separated project IDs"),
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    customers: Optional[str] = Query(None, description="Comma-separated customers"),
    labels: Optional[str] = Query(None, description="Comma-separated labels"),
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    limit: int = Query(100, description="Number of tickets to return"),
    offset: int = Query(0, description="Number of tickets to skip"),
    db: Session = Depends(get_db)
):
    """Get tickets with optional filters"""
    
    query = db.query(TicketModel)
    
    # Parse list params
    project_ids_list = [int(pid.strip()) for pid in project_ids.split(',')] if project_ids else None
    customers_list = [c.strip() for c in customers.split(',')] if customers else None
    labels_list = [l.strip() for l in labels.split(',')] if labels else None

    # Apply filters
    if project_ids_list:
        query = query.filter(TicketModel.project_id.in_(project_ids_list))
    elif project_id:
        query = query.filter(TicketModel.project_id == project_id)
    if user_id:
        query = query.filter(TicketModel.assignee_id == user_id)
    if status:
        query = query.filter(TicketModel.status == status)
    if customers_list:
        query = query.filter(TicketModel.customer.in_(customers_list))
    if labels_list:
        label_clauses = [TicketModel.labels.like(f"%,{lbl},%") for lbl in labels_list]
        if label_clauses:
            query = query.filter(or_(*label_clauses))
    if start_date:
        query = query.filter(TicketModel.created_at >= start_date)
    if end_date:
        query = query.filter(TicketModel.created_at <= end_date)
    
    # Apply pagination
    tickets = query.offset(offset).limit(limit).all()
    
    return tickets


@router.get("/{ticket_id}", response_model=Ticket)
async def get_ticket(ticket_id: int, db: Session = Depends(get_db)):
    """Get a specific ticket by ID"""
    
    ticket = db.query(TicketModel).filter(TicketModel.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    return ticket


@router.get("/jira/{jira_id}", response_model=Ticket)
async def get_ticket_by_jira_id(jira_id: str, db: Session = Depends(get_db)):
    """Get a ticket by Jira ID"""
    
    ticket = db.query(TicketModel).filter(TicketModel.jira_id == jira_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    return ticket