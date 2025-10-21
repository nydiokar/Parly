"""
Bills API endpoints.

Provides endpoints for querying bills, bill progress, and bill-related votes.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
import math

from api.database import get_db
from api.models import BillBase, BillDetail, PaginatedResponse
from db_setup.create_database import Bill, BillProgress, Member, Vote

router = APIRouter(prefix="/bills", tags=["bills"])


@router.get("/", response_model=PaginatedResponse)
def list_bills(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=200, description="Items per page"),
    parliament_number: Optional[int] = Query(None, description="Filter by parliament"),
    session_number: Optional[int] = Query(None, description="Filter by session"),
    chamber: Optional[str] = Query(None, description="Filter by chamber (House, Senate)"),
    status: Optional[str] = Query(None, description="Filter by status"),
    sponsor_id: Optional[int] = Query(None, description="Filter by sponsor member ID"),
    search: Optional[str] = Query(None, description="Search in bill titles"),
    db: Session = Depends(get_db)
):
    """
    List all bills with optional filtering and pagination.

    Returns paginated list of bills with basic information.
    """
    query = db.query(Bill)

    # Apply filters
    if parliament_number:
        query = query.filter(Bill.parliament_number == parliament_number)
    if session_number:
        query = query.filter(Bill.session_number == session_number)
    if chamber:
        query = query.filter(Bill.chamber == chamber)
    if status:
        query = query.filter(Bill.status == status)
    if sponsor_id:
        query = query.filter(Bill.sponsor_id == sponsor_id)
    if search:
        query = query.filter(
            (Bill.short_title.like(f"%{search}%")) |
            (Bill.long_title.like(f"%{search}%")) |
            (Bill.bill_number.like(f"%{search}%"))
        )

    # Order by parliament/session/bill number
    query = query.order_by(
        Bill.parliament_number.desc(),
        Bill.session_number.desc(),
        Bill.bill_number
    )

    # Get total count
    total = query.count()

    # Calculate pagination
    total_pages = math.ceil(total / page_size)
    offset = (page - 1) * page_size

    # Get paginated results
    bills = query.offset(offset).limit(page_size).all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "items": [BillBase.from_orm(b) for b in bills]
    }


@router.get("/chambers", response_model=List[str])
def list_chambers(db: Session = Depends(get_db)):
    """
    Get list of all unique chambers.
    """
    chambers = db.query(Bill.chamber).distinct().filter(Bill.chamber.isnot(None)).all()
    return sorted([c[0] for c in chambers])


@router.get("/statuses", response_model=List[str])
def list_statuses(db: Session = Depends(get_db)):
    """
    Get list of all unique bill statuses.
    """
    statuses = db.query(Bill.status).distinct().filter(Bill.status.isnot(None)).all()
    return sorted([s[0] for s in statuses])


@router.get("/{bill_id}", response_model=BillDetail)
def get_bill(bill_id: int, db: Session = Depends(get_db)):
    """
    Get detailed information about a specific bill.

    Includes sponsor information, progress stages, and vote count.
    """
    bill = db.query(Bill).options(
        joinedload(Bill.sponsor),
        joinedload(Bill.progress)
    ).filter(Bill.bill_id == bill_id).first()

    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")

    # Get vote count for this bill
    votes_count = db.query(Vote).filter(Vote.bill_number == bill.bill_number).count()

    # Build response
    sponsor_data = None
    if bill.sponsor:
        sponsor_data = {
            "member_id": bill.sponsor.member_id,
            "first_name": bill.sponsor.first_name,
            "last_name": bill.sponsor.last_name,
            "constituency": bill.sponsor.constituency,
            "province": bill.sponsor.province,
            "party": bill.sponsor.party
        }

    progress_stages = [
        {
            "progress_id": p.progress_id,
            "bill_id": p.bill_id,
            "status": p.status,
            "progress_date": p.progress_date
        }
        for p in bill.progress
    ]

    return {
        "bill_id": bill.bill_id,
        "bill_number": bill.bill_number,
        "parliament_number": bill.parliament_number,
        "session_number": bill.session_number,
        "short_title": bill.short_title,
        "long_title": bill.long_title,
        "status": bill.status,
        "sponsor_id": bill.sponsor_id,
        "chamber": bill.chamber,
        "sponsor": sponsor_data,
        "progress_stages": progress_stages,
        "votes_count": votes_count
    }


@router.get("/{bill_id}/progress", response_model=List[dict])
def get_bill_progress(bill_id: int, db: Session = Depends(get_db)):
    """
    Get all progress stages for a specific bill.
    """
    bill = db.query(Bill).filter(Bill.bill_id == bill_id).first()

    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")

    progress = db.query(BillProgress).filter(
        BillProgress.bill_id == bill_id
    ).order_by(BillProgress.progress_date).all()

    return [
        {
            "progress_id": p.progress_id,
            "bill_id": p.bill_id,
            "status": p.status,
            "progress_date": p.progress_date
        }
        for p in progress
    ]


@router.get("/{bill_id}/votes", response_model=List[dict])
def get_bill_votes(bill_id: int, db: Session = Depends(get_db)):
    """
    Get all votes related to a specific bill.
    """
    bill = db.query(Bill).filter(Bill.bill_id == bill_id).first()

    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")

    votes = db.query(Vote).filter(
        Vote.bill_number == bill.bill_number
    ).order_by(Vote.vote_date.desc()).all()

    return [
        {
            "vote_id": v.vote_id,
            "vote_number": v.vote_number,
            "parliament_number": v.parliament_number,
            "session_number": v.session_number,
            "vote_date": v.vote_date,
            "decision": v.decision,
            "yea_total": v.yea_total,
            "nay_total": v.nay_total,
            "paired_total": v.paired_total
        }
        for v in votes
    ]


@router.get("/by-number/{bill_number}", response_model=List[BillBase])
def get_bills_by_number(bill_number: str, db: Session = Depends(get_db)):
    """
    Get all bills with a specific bill number (across parliaments/sessions).
    """
    bills = db.query(Bill).filter(
        Bill.bill_number == bill_number
    ).order_by(
        Bill.parliament_number.desc(),
        Bill.session_number.desc()
    ).all()

    if not bills:
        raise HTTPException(status_code=404, detail="No bills found with this number")

    return [BillBase.from_orm(b) for b in bills]


@router.get("/stats/summary", response_model=dict)
def get_bills_summary(
    parliament_number: Optional[int] = Query(None),
    session_number: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Get summary statistics about bills.
    """
    query = db.query(Bill)

    if parliament_number:
        query = query.filter(Bill.parliament_number == parliament_number)
    if session_number:
        query = query.filter(Bill.session_number == session_number)

    bills = query.all()

    # Count by chamber
    house_bills = sum(1 for b in bills if b.chamber == 'House')
    senate_bills = sum(1 for b in bills if b.chamber == 'Senate')

    # Count by status (if available)
    status_counts = {}
    for bill in bills:
        if bill.status:
            status_counts[bill.status] = status_counts.get(bill.status, 0) + 1

    return {
        "total_bills": len(bills),
        "house_bills": house_bills,
        "senate_bills": senate_bills,
        "status_breakdown": status_counts,
        "parliament_number": parliament_number,
        "session_number": session_number
    }
