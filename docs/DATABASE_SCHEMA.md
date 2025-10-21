# Database Schema Documentation

## Overview

This document describes the actual database schema used in the Parly project, based on the SQLite database structure. The schema has been analyzed from the live database containing Canadian parliamentary data.

## Tables Overview

| Table | Records | Description |
|-------|---------|-------------|
| members | 455 | Members of Parliament |
| roles | 11,297 | Parliamentary roles and committee assignments |
| votes | 105,367 | Individual member votes (not aggregated) |
| bills | 1,094 | Legislative bills |
| bill_progress | 2,345 | Bill progression stages |

## Detailed Table Schemas

### Members Table

```sql
CREATE TABLE members (
    member_id INTEGER PRIMARY KEY,
    name VARCHAR,                    -- Full name (single field)
    constituency VARCHAR,
    party VARCHAR,
    province_name VARCHAR           -- Note: not "province"
);
```

**Sample Data:**
- member_id: 1, 2, 3...
- name: "John Smith", "Jane Doe"
- constituency: "Vancouver Centre", "Toronto Centre"
- party: "Liberal", "Conservative", "NDP"
- province_name: "British Columbia", "Ontario"

### Roles Table

```sql
CREATE TABLE roles (
    role_id INTEGER PRIMARY KEY,
    member_id INTEGER,              -- Foreign key to members
    role_type VARCHAR(25),          -- e.g., "Minister", "Chair", "Member"
    from_date DATE,                 -- Start date
    to_date DATE,                   -- End date (can be NULL)
    parliament_number VARCHAR,
    session_number VARCHAR,
    constituency_name VARCHAR,
    constituency_province VARCHAR,
    party VARCHAR,
    committee_name VARCHAR,
    affiliation_role_name VARCHAR,
    organization_name VARCHAR,
    office_role VARCHAR,
    election_result VARCHAR
);
```

**Notes:**
- Dates use `from_date`/`to_date` (not `start_date`/`end_date`)
- Many fields are optional and may be NULL

### Votes Table

```sql
CREATE TABLE votes (
    vote_id INTEGER,                -- NOT a primary key (multiple records per vote_id)
    member_id INTEGER,              -- Foreign key to members
    parliament_number INTEGER,
    session_number INTEGER,
    vote_topic VARCHAR,             -- Vote topic/subject
    subject TEXT,                   -- Detailed subject
    vote_result VARCHAR,            -- Overall vote outcome ("Agreed", "Negatived")
    vote_date DATE,
    member_vote VARCHAR             -- Individual member's vote ("Yea", "Nay", "Paired")
);
```

**Important Notes:**
- **This table contains individual member votes, not aggregated vote results**
- Multiple records share the same `vote_id` (one per participating member)
- `vote_result` shows the overall outcome of the vote
- `member_vote` shows how each individual member voted
- There is no `ParliamentaryAssociation` table in the current schema

### Bills Table

```sql
CREATE TABLE bills (
    bill_id INTEGER PRIMARY KEY,
    bill_number VARCHAR,
    parliament_number INTEGER,
    session_number INTEGER,
    status VARCHAR,
    sponsor_id INTEGER,             -- Foreign key to members
    chamber VARCHAR,
    legisinfo_bill_id INTEGER,
    short_title VARCHAR,
    long_title TEXT
);
```

### Bill Progress Table

```sql
CREATE TABLE bill_progress (
    progress_id INTEGER PRIMARY KEY,
    bill_id INTEGER,                -- Foreign key to bills
    status VARCHAR,
    progress_date DATE
);
```

**Notes:**
- Progress records are stored separately from bills
- One bill can have multiple progress stages over time

## Relationships

```
members (1) ──── (many) roles
members (1) ──── (many) votes
members (1) ──── (many) bills (as sponsor)
bills (1) ──── (many) bill_progress
```

## Key Design Decisions

### Vote Schema (Current State)
The current schema uses a single `votes` table containing individual member votes rather than a two-table design (aggregate votes + participants). This means:

- To get all participants in a vote: `SELECT * FROM votes WHERE vote_id = ?`
- To get unique votes: `SELECT DISTINCT vote_id, parliament_number, session_number, vote_topic, vote_result, vote_date FROM votes`
- Vote counts must be calculated programmatically

### Naming Conventions
- Member location: `province_name` (not `province`)
- Role dates: `from_date`/`to_date` (not `start_date`/`end_date`)
- Vote outcome: `vote_result` (not `decision`)
- Member vote: `member_vote` (not `vote_status`)

## Data Integrity Notes

- All foreign keys are properly defined
- No orphaned records found in the dataset
- Date fields use ISO format (YYYY-MM-DD)
- Text fields use VARCHAR with appropriate lengths
- Many fields allow NULL values

## API Model Alignment

The Pydantic models in `api/models.py` have been updated to match this actual schema:

- `MemberBase` uses `province_name`
- `RoleBase` uses `from_date`/`to_date`
- `VoteBase` uses `vote_result` and `member_vote`
- `VoteDetail` aggregates data from multiple vote records

## Future Schema Improvements

As outlined in `PROJECT_IMPROVEMENTS.md`, the vote schema could be refactored into a cleaner two-table design:

1. `votes` - Aggregate vote information
2. `vote_participants` - Individual member votes

This would improve query performance and make the schema more intuitive, but would require a data migration.
