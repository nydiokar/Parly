"""
FastAPI main application for Parly - Canadian Parliament Data API.

This API provides access to Canadian parliamentary data including:
- Members of Parliament
- Votes and voting records
- Bills and legislative progress
- Member roles and statistics

Data is sourced from parl.ca and ourcommons.ca through automated scrapers.
"""

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import math

from api.database import get_db
from api.routes import members, votes, bills
from db_setup.create_database import Member, Role, Vote, ParliamentaryAssociation, Bill, BillProgress

# Create FastAPI app
app = FastAPI(
    title="Parly API",
    description="Canadian Parliament Data API - Access parliamentary data including members, votes, and bills",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware for web clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(members.router)
app.include_router(votes.router)
app.include_router(bills.router)


@app.get("/", tags=["root"])
def root():
    """
    API root endpoint with welcome message and available endpoints.
    """
    return {
        "message": "Welcome to Parly API - Canadian Parliament Data",
        "version": "1.0.0",
        "documentation": "/docs",
        "endpoints": {
            "members": "/members",
            "votes": "/votes",
            "bills": "/bills",
            "statistics": "/stats"
        }
    }


@app.get("/health", tags=["root"])
def health_check():
    """
    Health check endpoint.
    """
    return {"status": "healthy"}


@app.get("/stats", tags=["statistics"])
def get_overall_stats(db: Session = Depends(get_db)):
    """
    Get overall database statistics.

    Returns counts for all major entities in the database.
    """
    total_members = db.query(Member).count()
    total_roles = db.query(Role).count()
    total_votes = db.query(Vote).count()
    total_vote_participants = db.query(ParliamentaryAssociation).count()
    total_bills = db.query(Bill).count()
    total_bill_progress = db.query(BillProgress).count()

    # Get parliament/session info
    parliaments = db.query(
        Vote.parliament_number,
        Vote.session_number
    ).distinct().all()

    return {
        "database_stats": {
            "total_members": total_members,
            "total_roles": total_roles,
            "total_votes": total_votes,
            "total_vote_participants": total_vote_participants,
            "total_bills": total_bills,
            "total_bill_progress_stages": total_bill_progress
        },
        "parliaments": [
            {
                "parliament_number": p[0],
                "session_number": p[1]
            }
            for p in sorted(parliaments, reverse=True)
        ]
    }


@app.get("/stats/parties", tags=["statistics"])
def get_party_stats(db: Session = Depends(get_db)):
    """
    Get statistics broken down by party.
    """
    members = db.query(Member).all()

    party_counts = {}
    for member in members:
        if member.party:
            party_counts[member.party] = party_counts.get(member.party, 0) + 1

    return {
        "total_parties": len(party_counts),
        "party_breakdown": dict(sorted(party_counts.items(), key=lambda x: x[1], reverse=True))
    }


@app.get("/stats/provinces", tags=["statistics"])
def get_province_stats(db: Session = Depends(get_db)):
    """
    Get statistics broken down by province.
    """
    members = db.query(Member).all()

    province_counts = {}
    for member in members:
        if member.province:
            province_counts[member.province] = province_counts.get(member.province, 0) + 1

    return {
        "total_provinces": len(province_counts),
        "province_breakdown": dict(sorted(province_counts.items(), key=lambda x: x[1], reverse=True))
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
