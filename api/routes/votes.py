"""
Votes API endpoints.

Provides endpoints for querying votes, vote participants, and vote details.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from datetime import date
import math

from api.database import get_db
from api.models import VoteBase, VoteDetail, PaginatedResponse
from db_setup.create_database import Vote, ParliamentaryAssociation, Member

router = APIRouter(prefix="/votes", tags=["votes"])


@router.get("/", response_model=PaginatedResponse)
def list_votes(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=200, description="Items per page"),
    parliament_number: Optional[int] = Query(None, description="Filter by parliament"),
    session_number: Optional[int] = Query(None, description="Filter by session"),
    vote_topic: Optional[str] = Query(None, description="Filter by vote topic"),
    vote_result: Optional[str] = Query(None, description="Filter by vote result"),
    member_vote: Optional[str] = Query(None, description="Filter by member's vote"),
    date_from: Optional[date] = Query(None, description="Filter votes from this date"),
    date_to: Optional[date] = Query(None, description="Filter votes until this date"),
    db: Session = Depends(get_db)
):
    """
    List all votes with optional filtering and pagination.

    Returns paginated list of votes with basic information.
    """
    query = db.query(Vote)

    # Apply filters
    if parliament_number:
        query = query.filter(Vote.parliament_number == parliament_number)
    if session_number:
        query = query.filter(Vote.session_number == session_number)
    if vote_topic:
        query = query.filter(Vote.vote_topic.like(f"%{vote_topic}%"))
    if vote_result:
        query = query.filter(Vote.vote_result == vote_result)
    if member_vote:
        query = query.filter(Vote.member_vote == member_vote)
    if date_from:
        query = query.filter(Vote.vote_date >= date_from)
    if date_to:
        query = query.filter(Vote.vote_date <= date_to)

    # Order by date descending (most recent first)
    query = query.order_by(Vote.vote_date.desc(), Vote.vote_id.desc())

    # Get total count
    total = query.count()

    # Calculate pagination
    total_pages = math.ceil(total / page_size)
    offset = (page - 1) * page_size

    # Get paginated results
    votes = query.offset(offset).limit(page_size).all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "items": [VoteBase.from_orm(v) for v in votes]
    }


@router.get("/parliaments", response_model=List[dict])
def list_parliaments(db: Session = Depends(get_db)):
    """
    Get list of all unique parliament/session combinations with vote counts.
    """
    parliaments = db.query(
        Vote.parliament_number,
        Vote.session_number
    ).distinct().all()

    result = []
    for parl, sess in parliaments:
        count = db.query(Vote).filter(
            Vote.parliament_number == parl,
            Vote.session_number == sess
        ).count()

        result.append({
            "parliament_number": parl,
            "session_number": sess,
            "vote_count": count
        })

    return sorted(result, key=lambda x: (x["parliament_number"], x["session_number"]), reverse=True)


@router.get("/{vote_id}", response_model=VoteDetail)
def get_vote(vote_id: int, db: Session = Depends(get_db)):
    """
    Get detailed information about a specific vote.

    Includes participant counts and lists of members who voted yea/nay.
    """
    # Get all vote records with this vote_id (individual member votes)
    vote_records = db.query(Vote).options(
        joinedload(Vote.member)
    ).filter(Vote.vote_id == vote_id).all()

    if not vote_records:
        raise HTTPException(status_code=404, detail="Vote not found")

    # Use first record for vote metadata
    vote = vote_records[0]

    # Aggregate participant data
    yea_members = []
    nay_members = []
    paired_members = []

    for record in vote_records:
        member_name = record.member.name if record.member else "Unknown"
        if record.member_vote == 'Yea':
            yea_members.append(member_name)
        elif record.member_vote == 'Nay':
            nay_members.append(member_name)
        elif record.member_vote == 'Paired':
            paired_members.append(member_name)

    return {
        "vote_id": vote.vote_id,
        "parliament_number": vote.parliament_number,
        "session_number": vote.session_number,
        "vote_topic": vote.vote_topic,
        "subject": vote.subject,
        "vote_result": vote.vote_result,
        "vote_date": vote.vote_date,
        "participants_count": len(vote_records),
        "yea_count": len(yea_members),
        "nay_count": len(nay_members),
        "paired_count": len(paired_members),
        "yea_members": sorted(yea_members),
        "nay_members": sorted(nay_members),
        "paired_members": sorted(paired_members)
    }


@router.get("/{vote_id}/participants", response_model=PaginatedResponse)
def get_vote_participants(
    vote_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    vote_status: Optional[str] = Query(None, description="Filter by vote status (Yea, Nay, Paired)"),
    db: Session = Depends(get_db)
):
    """
    Get all participants in a specific vote with pagination.
    """
    vote = db.query(Vote).filter(Vote.vote_id == vote_id).first()

    if not vote:
        raise HTTPException(status_code=404, detail="Vote not found")

    query = db.query(ParliamentaryAssociation).options(
        joinedload(ParliamentaryAssociation.member)
    ).filter(ParliamentaryAssociation.vote_id == vote_id)

    if vote_status:
        query = query.filter(ParliamentaryAssociation.vote_status == vote_status)

    total = query.count()
    total_pages = math.ceil(total / page_size)
    offset = (page - 1) * page_size

    participants = query.offset(offset).limit(page_size).all()

    items = [
        {
            "participant_id": p.participant_id,
            "vote_id": p.vote_id,
            "member_id": p.member_id,
            "vote_status": p.vote_status,
            "member": {
                "member_id": p.member.member_id,
                "first_name": p.member.first_name,
                "last_name": p.member.last_name,
                "party": p.member.party,
                "province": p.member.province
            }
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


@router.get("/by-topic/{topic}", response_model=List[VoteBase])
def get_votes_by_topic(topic: str, db: Session = Depends(get_db)):
    """
    Get all votes related to a specific topic.
    """
    votes = db.query(Vote).filter(
        Vote.vote_topic.like(f"%{topic}%")
    ).order_by(Vote.vote_date.desc()).all()

    return [VoteBase.from_orm(v) for v in votes]


@router.get("/stats/summary", response_model=dict)
def get_vote_summary(
    parliament_number: Optional[int] = Query(None),
    session_number: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Get summary statistics about votes.
    """
    query = db.query(Vote)

    if parliament_number:
        query = query.filter(Vote.parliament_number == parliament_number)
    if session_number:
        query = query.filter(Vote.session_number == session_number)

    votes = query.all()

    # Count unique votes (not individual member votes)
    unique_votes = {}
    for v in votes:
        key = v.vote_id
        if key not in unique_votes:
            unique_votes[key] = v

    agreed_count = sum(1 for v in unique_votes.values() if v.vote_result == 'Agreed')
    negatived_count = sum(1 for v in unique_votes.values() if v.vote_result == 'Negatived')

    return {
        "total_votes": len(unique_votes),
        "agreed": agreed_count,
        "negatived": negatived_count,
        "parliament_number": parliament_number,
        "session_number": session_number
    }


@router.get("/stats/day-of-week", response_model=dict)
def get_votes_by_day_of_week(
    exclude_budget_votes: bool = Query(True, description="Exclude budget-related votes for cleaner analysis"),
    parliament_number: Optional[int] = Query(None, description="Filter by parliament"),
    session_number: Optional[int] = Query(None, description="Filter by session"),
    db: Session = Depends(get_db)
):
    """
    Get vote counts by day of week.

    This endpoint powers the "4-Day Work Week" visualization, showing that
    96% of parliamentary votes happen Monday-Thursday.

    Returns vote event counts (not individual member votes) grouped by day of week.
    """
    from scripts.analysis.classify_vote_types import is_budget_vote

    # Build base query
    query = db.query(Vote)

    if parliament_number:
        query = query.filter(Vote.parliament_number == parliament_number)
    if session_number:
        query = query.filter(Vote.session_number == session_number)

    votes = query.all()

    # Group by date and count unique vote events per day
    votes_by_date = {}
    for vote in votes:
        if vote.vote_date:
            date_key = vote.vote_date.isoformat()

            # Apply budget vote filter if requested
            if exclude_budget_votes and is_budget_vote(vote.vote_topic):
                continue

            if date_key not in votes_by_date:
                votes_by_date[date_key] = set()
            votes_by_date[date_key].add(vote.vote_id)

    # Count votes per day and group by day of week
    day_counts = {
        'Monday': 0,
        'Tuesday': 0,
        'Wednesday': 0,
        'Thursday': 0,
        'Friday': 0,
        'Saturday': 0,
        'Sunday': 0
    }

    total_votes = 0

    for date_str, vote_ids in votes_by_date.items():
        date_obj = date.fromisoformat(date_str)
        day_name = date_obj.strftime('%A')  # Monday, Tuesday, etc.
        vote_count = len(vote_ids)

        day_counts[day_name] += vote_count
        total_votes += vote_count

    # Calculate percentages
    day_percentages = {}
    if total_votes > 0:
        for day, count in day_counts.items():
            day_percentages[day] = round((count / total_votes) * 100, 1)

    return {
        "day_counts": day_counts,
        "day_percentages": day_percentages,
        "total_vote_events": total_votes,
        "total_days_with_votes": len(votes_by_date),
        "monday_to_thursday_percentage": sum(day_percentages.get(day, 0) for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday']),
        "exclude_budget_votes": exclude_budget_votes,
        "parliament_number": parliament_number,
        "session_number": session_number
    }