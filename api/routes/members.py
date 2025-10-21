"""
Members API endpoints.

Provides endpoints for querying members, their roles, votes, and sponsored bills.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
import math

from api.database import get_db
from api.models import (
    MemberBase,
    MemberWithRoles,
    MemberDetail,
    MemberStats,
    PaginatedResponse
)
from db_setup.create_database import Member, Role, Vote, ParliamentaryAssociation, Bill

router = APIRouter(prefix="/members", tags=["members"])


@router.get("/", response_model=PaginatedResponse)
def list_members(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=200, description="Items per page"),
    party: Optional[str] = Query(None, description="Filter by party"),
    province: Optional[str] = Query(None, description="Filter by province"),
    constituency: Optional[str] = Query(None, description="Filter by constituency"),
    name: Optional[str] = Query(None, description="Search by name (first or last)"),
    db: Session = Depends(get_db)
):
    """
    List all members with optional filtering and pagination.

    Returns paginated list of members with basic information.
    """
    query = db.query(Member)

    # Apply filters
    if party:
        query = query.filter(Member.party == party)
    if province:
        query = query.filter(Member.province == province)
    if constituency:
        query = query.filter(Member.constituency.like(f"%{constituency}%"))
    if name:
        query = query.filter(
            (Member.first_name.like(f"%{name}%")) |
            (Member.last_name.like(f"%{name}%"))
        )

    # Get total count
    total = query.count()

    # Calculate pagination
    total_pages = math.ceil(total / page_size)
    offset = (page - 1) * page_size

    # Get paginated results
    members = query.offset(offset).limit(page_size).all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "items": [MemberBase.from_orm(m) for m in members]
    }


@router.get("/parties", response_model=List[str])
def list_parties(db: Session = Depends(get_db)):
    """
    Get list of all unique parties.
    """
    parties = db.query(Member.party).distinct().filter(Member.party.isnot(None)).all()
    return sorted([p[0] for p in parties])


@router.get("/provinces", response_model=List[str])
def list_provinces(db: Session = Depends(get_db)):
    """
    Get list of all unique provinces.
    """
    provinces = db.query(Member.province).distinct().filter(Member.province.isnot(None)).all()
    return sorted([p[0] for p in provinces])


@router.get("/{member_id}", response_model=MemberDetail)
def get_member(member_id: int, db: Session = Depends(get_db)):
    """
    Get detailed information about a specific member.

    Includes roles, vote count, and sponsored bills count.
    """
    member = db.query(Member).options(
        joinedload(Member.roles)
    ).filter(Member.member_id == member_id).first()

    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    # Get vote count
    votes_count = db.query(ParliamentaryAssociation).filter(
        ParliamentaryAssociation.member_id == member_id
    ).count()

    # Get sponsored bills count
    sponsored_bills_count = db.query(Bill).filter(
        Bill.sponsor_id == member_id
    ).count()

    # Convert to response model
    member_dict = {
        "member_id": member.member_id,
        "first_name": member.first_name,
        "last_name": member.last_name,
        "constituency": member.constituency,
        "province": member.province,
        "party": member.party,
        "roles": member.roles,
        "votes_count": votes_count,
        "sponsored_bills_count": sponsored_bills_count
    }

    return member_dict


@router.get("/{member_id}/roles", response_model=List[dict])
def get_member_roles(member_id: int, db: Session = Depends(get_db)):
    """
    Get all roles for a specific member.
    """
    member = db.query(Member).filter(Member.member_id == member_id).first()

    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    roles = db.query(Role).filter(Role.member_id == member_id).all()

    return [
        {
            "role_id": r.role_id,
            "member_id": r.member_id,
            "role_type": r.role_type,
            "start_date": r.start_date,
            "end_date": r.end_date
        }
        for r in roles
    ]


@router.get("/{member_id}/votes", response_model=PaginatedResponse)
def get_member_votes(
    member_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """
    Get all votes by a specific member with pagination.
    """
    member = db.query(Member).filter(Member.member_id == member_id).first()

    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    # Query vote participants with vote information
    query = db.query(ParliamentaryAssociation).options(
        joinedload(ParliamentaryAssociation.vote)
    ).filter(ParliamentaryAssociation.member_id == member_id)

    total = query.count()
    total_pages = math.ceil(total / page_size)
    offset = (page - 1) * page_size

    participants = query.offset(offset).limit(page_size).all()

    items = [
        {
            "vote_id": p.vote.vote_id,
            "vote_number": p.vote.vote_number,
            "parliament_number": p.vote.parliament_number,
            "session_number": p.vote.session_number,
            "vote_date": p.vote.vote_date,
            "bill_number": p.vote.bill_number,
            "decision": p.vote.decision,
            "member_vote": p.vote_status
        }
        for p in participants
    ]

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "items": items
    }


@router.get("/{member_id}/bills", response_model=PaginatedResponse)
def get_member_bills(
    member_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """
    Get all bills sponsored by a specific member with pagination.
    """
    member = db.query(Member).filter(Member.member_id == member_id).first()

    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    query = db.query(Bill).filter(Bill.sponsor_id == member_id)

    total = query.count()
    total_pages = math.ceil(total / page_size)
    offset = (page - 1) * page_size

    bills = query.offset(offset).limit(page_size).all()

    items = [
        {
            "bill_id": b.bill_id,
            "bill_number": b.bill_number,
            "parliament_number": b.parliament_number,
            "session_number": b.session_number,
            "short_title": b.short_title,
            "long_title": b.long_title,
            "status": b.status,
            "chamber": b.chamber
        }
        for b in bills
    ]

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "items": items
    }


@router.get("/{member_id}/stats", response_model=MemberStats)
def get_member_stats(member_id: int, db: Session = Depends(get_db)):
    """
    Get voting statistics for a specific member.
    """
    member = db.query(Member).filter(Member.member_id == member_id).first()

    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    # Get vote counts by status
    votes = db.query(ParliamentaryAssociation).filter(
        ParliamentaryAssociation.member_id == member_id
    ).all()

    yea_votes = sum(1 for v in votes if v.vote_status == 'Yea')
    nay_votes = sum(1 for v in votes if v.vote_status == 'Nay')
    paired_votes = sum(1 for v in votes if v.vote_status == 'Paired')

    # Get sponsored bills count
    sponsored_bills = db.query(Bill).filter(Bill.sponsor_id == member_id).count()

    return {
        "member_id": member.member_id,
        "member_name": f"{member.first_name} {member.last_name}",
        "total_votes": len(votes),
        "yea_votes": yea_votes,
        "nay_votes": nay_votes,
        "paired_votes": paired_votes,
        "sponsored_bills": sponsored_bills
    }
