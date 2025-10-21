"""
Pydantic models for FastAPI request/response schemas.

These models define the structure of data returned by the API,
separate from the SQLAlchemy database models.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date


# ==================== MEMBER MODELS ====================

class MemberBase(BaseModel):
    """Base member information."""
    member_id: int
    name: str  # Full name (not split into first/last)
    constituency: Optional[str] = None
    province_name: Optional[str] = None  # Actual field name in database
    party: Optional[str] = None

    class Config:
        from_attributes = True


class MemberWithRoles(MemberBase):
    """Member with their roles."""
    roles: List['RoleBase'] = []


class MemberDetail(MemberBase):
    """Detailed member information including votes and bills."""
    roles: List['RoleBase'] = []
    sponsored_bills_count: int = 0
    votes_count: int = 0


# ==================== ROLE MODELS ====================

class RoleBase(BaseModel):
    """Base role information."""
    role_id: int
    member_id: int
    role_type: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None

    class Config:
        from_attributes = True


class RoleWithMember(RoleBase):
    """Role with member information."""
    member: MemberBase


# ==================== VOTE MODELS ====================

class VoteBase(BaseModel):
    """Base vote information."""
    vote_id: int
    vote_number: int
    parliament_number: int
    session_number: int
    sitting_number: Optional[int] = None
    vote_date: Optional[date] = None
    decision: Optional[str] = None
    bill_number: Optional[str] = None
    yea_total: Optional[int] = None
    nay_total: Optional[int] = None
    paired_total: Optional[int] = None

    class Config:
        from_attributes = True


class VoteDetail(VoteBase):
    """Detailed vote information including participants."""
    participants_count: int = 0
    yea_members: List[str] = []
    nay_members: List[str] = []


class VoteParticipantBase(BaseModel):
    """Base vote participant information."""
    participant_id: int
    vote_id: int
    member_id: int
    vote_status: str

    class Config:
        from_attributes = True


class VoteParticipantWithMember(VoteParticipantBase):
    """Vote participant with member information."""
    member: MemberBase


# ==================== BILL MODELS ====================

class BillBase(BaseModel):
    """Base bill information."""
    bill_id: int
    bill_number: str
    parliament_number: int
    session_number: int
    short_title: Optional[str] = None
    long_title: Optional[str] = None
    status: Optional[str] = None
    sponsor_id: Optional[int] = None
    chamber: Optional[str] = None

    class Config:
        from_attributes = True


class BillWithSponsor(BillBase):
    """Bill with sponsor information."""
    sponsor: Optional[MemberBase] = None


class BillDetail(BillWithSponsor):
    """Detailed bill information including progress."""
    progress_stages: List['BillProgressBase'] = []
    votes_count: int = 0


class BillProgressBase(BaseModel):
    """Base bill progress information."""
    progress_id: int
    bill_id: int
    status: str
    progress_date: Optional[date] = None

    class Config:
        from_attributes = True


class BillProgressWithBill(BillProgressBase):
    """Bill progress with bill information."""
    bill: BillBase


# ==================== STATISTICS MODELS ====================

class DatabaseStats(BaseModel):
    """Overall database statistics."""
    total_members: int
    total_roles: int
    total_votes: int
    total_bills: int
    total_bill_progress: int
    total_vote_participants: int


class ParliamentStats(BaseModel):
    """Statistics for a specific parliament."""
    parliament_number: int
    session_number: int
    total_votes: int
    total_bills: int
    date_range: Optional[str] = None


class MemberStats(BaseModel):
    """Statistics for a specific member."""
    member_id: int
    member_name: str
    total_votes: int
    yea_votes: int
    nay_votes: int
    paired_votes: int
    sponsored_bills: int


# ==================== PAGINATION MODELS ====================

class PaginatedResponse(BaseModel):
    """Generic paginated response wrapper."""
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Items per page")
    total_pages: int = Field(..., description="Total number of pages")
    items: List = Field(..., description="List of items for current page")


# ==================== QUERY FILTER MODELS ====================

class MemberFilters(BaseModel):
    """Filters for member queries."""
    party: Optional[str] = None
    province: Optional[str] = None
    constituency: Optional[str] = None
    name: Optional[str] = None


class VoteFilters(BaseModel):
    """Filters for vote queries."""
    parliament_number: Optional[int] = None
    session_number: Optional[int] = None
    bill_number: Optional[str] = None
    decision: Optional[str] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None


class BillFilters(BaseModel):
    """Filters for bill queries."""
    parliament_number: Optional[int] = None
    session_number: Optional[int] = None
    chamber: Optional[str] = None
    status: Optional[str] = None
    sponsor_id: Optional[int] = None
    search: Optional[str] = None  # Search in titles
