# Technical Specification

## Overview

This document provides detailed technical specifications for the Parly Parliamentary Data API. It defines the database schema, API endpoints, data models, and technical constraints that must be followed during implementation.

---

## Database Schema

The system uses SQLite as the database engine for simplicity and portability. The schema is defined using SQLAlchemy ORM.

### Tables

#### 1. `members`
Stores information about Members of Parliament.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `member_id` | Integer | PRIMARY KEY | Unique identifier from parliamentary system |
| `name` | String | NOT NULL | Full name in Title Case (e.g., "Ziad Aboultaif") |
| `constituency` | String | NULLABLE | Electoral district name (most recent) |
| `party` | String | NULLABLE | Political party affiliation (most recent) |
| `province_name` | String | NULLABLE | Province or territory name |

**Relationships:**
- One-to-many with `roles`
- One-to-many with `votes`
- One-to-many with `parliamentary_associations`
- One-to-many with `bills` (as sponsor)

---

#### 2. `roles`
Stores all roles held by members (committees, offices, MP status, etc.).

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `role_id` | Integer | PRIMARY KEY, AUTOINCREMENT | Unique role identifier |
| `member_id` | Integer | FOREIGN KEY → members.member_id, NOT NULL | Reference to member |
| `role_type` | Enum(RoleType) | NOT NULL | Type of role (see RoleType enum below) |
| `from_date` | Date | NULLABLE | Start date of role |
| `to_date` | Date | NULLABLE | End date of role (NULL = current) |
| `parliament_number` | String | NULLABLE | Parliament number (e.g., "44") |
| `session_number` | String | NULLABLE | Session number (e.g., "1" or "44-1") |
| `constituency_name` | String | NULLABLE | For MP roles: constituency name |
| `constituency_province` | String | NULLABLE | For MP roles: province/territory |
| `party` | String | NULLABLE | For affiliation roles: party name |
| `committee_name` | String | NULLABLE | For committee roles: committee name |
| `affiliation_role_name` | String | NULLABLE | Role within committee/organization |
| `organization_name` | String | NULLABLE | For associations: organization name |
| `office_role` | String | NULLABLE | For parliamentary offices: role title |
| `election_result` | String | NULLABLE | For election candidates: result status |

**RoleType Enum Values:**
- `MEMBER_OF_PARLIAMENT`
- `POLITICAL_AFFILIATION`
- `COMMITTEE_MEMBER`
- `PARLIAMENTARY_ASSOCIATION`
- `ELECTION_CANDIDATE`
- `PARLIAMENTARIAN_OFFICE`

**Constraints:**
- UNIQUE constraint on: `(member_id, role_type, from_date, parliament_number, session_number, committee_name, organization_name)`
- This prevents duplicate role entries

**Relationships:**
- Many-to-one with `members`

---

#### 3. `votes`
Stores individual member voting records.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `vote_id` | Integer | PRIMARY KEY, AUTOINCREMENT | Unique vote record identifier |
| `member_id` | Integer | FOREIGN KEY → members.member_id, NOT NULL | Reference to member |
| `parliament_number` | Integer | NOT NULL | Parliament number |
| `session_number` | Integer | NOT NULL | Session number |
| `vote_topic` | String | NULLABLE | Topic or bill being voted on |
| `subject` | Text | NULLABLE | Detailed subject description |
| `vote_result` | String | NULLABLE | Overall result (e.g., "Agreed To", "Negatived") |
| `vote_date` | Date | NOT NULL | Date of the vote |
| `member_vote` | String | NOT NULL | Member's vote (e.g., "Yea", "Nay", "Paired") |

**Relationships:**
- Many-to-one with `members`

---

#### 4. `bills`
Stores information about bills sponsored by members.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `bill_id` | Integer | PRIMARY KEY, AUTOINCREMENT | Unique bill identifier |
| `bill_number` | String | NOT NULL | Bill code (e.g., "C-1", "S-203") |
| `parliament_number` | Integer | NOT NULL | Parliament number |
| `session_number` | Integer | NOT NULL | Session number |
| `status` | String | NULLABLE | Current status of the bill |
| `sponsor_id` | Integer | FOREIGN KEY → members.member_id, NULLABLE | Reference to sponsoring member |
| `chamber` | String | NOT NULL | Originating chamber ("House of Commons" or "Senate") |

**Relationships:**
- Many-to-one with `members` (sponsor)
- One-to-many with `bill_progress`

---

#### 5. `bill_progress`
Tracks the legislative progress of bills through various stages.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `progress_id` | Integer | PRIMARY KEY, AUTOINCREMENT | Unique progress record identifier |
| `bill_id` | Integer | FOREIGN KEY → bills.bill_id, NOT NULL | Reference to bill |
| `status` | String | NOT NULL | Stage name (e.g., "First Reading") |
| `progress_date` | Date | NOT NULL | Date of this stage |

**Relationships:**
- Many-to-one with `bills`

---

#### 6. `parliamentary_associations`
Stores member participation in parliamentary associations and groups.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `association_id` | Integer | PRIMARY KEY, AUTOINCREMENT | Unique association record identifier |
| `member_id` | Integer | FOREIGN KEY → members.member_id, NOT NULL | Reference to member |
| `association_name` | String | NOT NULL | Name of the association |
| `role_in_group` | String | NULLABLE | Role (e.g., "Member", "Executive Member") |

**Relationships:**
- Many-to-one with `members`

---

## API Endpoints Specification

All API endpoints follow RESTful conventions and return JSON responses.

### Base URL
```
http://localhost:8000/api
```

### Response Format Standards

**Success Response:**
```json
{
  "status": "success",
  "data": { ... }
}
```

**Error Response:**
```json
{
  "status": "error",
  "message": "Error description",
  "code": "ERROR_CODE"
}
```

**Pagination (for list endpoints):**
```json
{
  "status": "success",
  "data": [...],
  "pagination": {
    "page": 1,
    "per_page": 50,
    "total": 338,
    "total_pages": 7
  }
}
```

---

### Endpoint Definitions

#### 1. **GET /api/members**
Retrieve a list of all Members of Parliament.

**Query Parameters:**
- `page` (integer, optional, default=1): Page number
- `per_page` (integer, optional, default=50, max=100): Items per page
- `party` (string, optional): Filter by party name
- `province` (string, optional): Filter by province/territory

**Response:**
```json
{
  "status": "success",
  "data": [
    {
      "member_id": 89156,
      "name": "Ziad Aboultaif",
      "constituency": "Edmonton Manning",
      "party": "Conservative",
      "province_name": "Alberta"
    }
  ],
  "pagination": { ... }
}
```

---

#### 2. **GET /api/members/{member_id}**
Retrieve detailed information for a specific member.

**Path Parameters:**
- `member_id` (integer, required): Member's unique ID

**Response:**
```json
{
  "status": "success",
  "data": {
    "member_id": 89156,
    "name": "Ziad Aboultaif",
    "constituency": "Edmonton Manning",
    "party": "Conservative",
    "province_name": "Alberta",
    "current_roles": [
      {
        "role_type": "Member of Parliament",
        "from_date": "2021-09-20",
        "to_date": null,
        "constituency_name": "Edmonton Manning"
      }
    ]
  }
}
```

**Error Responses:**
- `404`: Member not found

---

#### 3. **GET /api/members/{member_id}/roles**
Retrieve all roles for a specific member.

**Path Parameters:**
- `member_id` (integer, required): Member's unique ID

**Query Parameters:**
- `role_type` (string, optional): Filter by role type
- `active_only` (boolean, optional, default=false): Only return current roles (to_date is NULL)

**Response:**
```json
{
  "status": "success",
  "data": [
    {
      "role_id": 1,
      "role_type": "MEMBER_OF_PARLIAMENT",
      "from_date": "2021-09-20",
      "to_date": null,
      "constituency_name": "Edmonton Manning",
      "constituency_province": "Alberta"
    },
    {
      "role_id": 2,
      "role_type": "COMMITTEE_MEMBER",
      "from_date": "2023-09-20",
      "to_date": null,
      "committee_name": "Foreign Affairs and International Development",
      "affiliation_role_name": "Member"
    }
  ]
}
```

---

#### 4. **GET /api/members/{member_id}/votes**
Retrieve voting records for a specific member.

**Path Parameters:**
- `member_id` (integer, required): Member's unique ID

**Query Parameters:**
- `page` (integer, optional, default=1): Page number
- `per_page` (integer, optional, default=50): Items per page
- `parliament` (integer, optional): Filter by parliament number
- `from_date` (date, optional, format: YYYY-MM-DD): Start date
- `to_date` (date, optional, format: YYYY-MM-DD): End date

**Response:**
```json
{
  "status": "success",
  "data": [
    {
      "vote_id": 1,
      "parliament_number": 44,
      "session_number": 1,
      "vote_date": "2022-03-15",
      "vote_topic": "Bill C-10",
      "subject": "An Act to amend...",
      "member_vote": "Yea",
      "vote_result": "Agreed To"
    }
  ],
  "pagination": { ... }
}
```

---

#### 5. **GET /api/bills**
Retrieve a list of bills.

**Query Parameters:**
- `page` (integer, optional, default=1): Page number
- `per_page` (integer, optional, default=50): Items per page
- `parliament` (integer, optional): Filter by parliament number
- `session` (integer, optional): Filter by session number
- `sponsor_id` (integer, optional): Filter by sponsor member ID
- `status` (string, optional): Filter by bill status

**Response:**
```json
{
  "status": "success",
  "data": [
    {
      "bill_id": 1,
      "bill_number": "C-1",
      "parliament_number": 44,
      "session_number": 1,
      "status": "First Reading",
      "sponsor_id": 58733,
      "sponsor_name": "Justin Trudeau",
      "chamber": "House of Commons"
    }
  ],
  "pagination": { ... }
}
```

---

#### 6. **GET /api/bills/{bill_id}**
Retrieve detailed information for a specific bill.

**Path Parameters:**
- `bill_id` (integer, required): Bill's unique ID

**Response:**
```json
{
  "status": "success",
  "data": {
    "bill_id": 1,
    "bill_number": "C-1",
    "parliament_number": 44,
    "session_number": 1,
    "status": "First Reading",
    "sponsor": {
      "member_id": 58733,
      "name": "Justin Trudeau"
    },
    "chamber": "House of Commons",
    "progress": [
      {
        "progress_id": 1,
        "status": "Introduction",
        "progress_date": "2021-11-23"
      },
      {
        "progress_id": 2,
        "status": "First Reading",
        "progress_date": "2021-11-23"
      }
    ]
  }
}
```

**Error Responses:**
- `404`: Bill not found

---

#### 7. **GET /api/statistics**
Retrieve aggregate statistics about the parliamentary data.

**Response:**
```json
{
  "status": "success",
  "data": {
    "total_members": 338,
    "total_votes": 15234,
    "total_bills": 450,
    "by_party": {
      "Conservative": 119,
      "Liberal": 159,
      "NDP": 25,
      "Bloc Québécois": 32,
      "Green Party": 2,
      "Independent": 1
    },
    "by_province": {
      "Ontario": 121,
      "Quebec": 78,
      "British Columbia": 42,
      "Alberta": 34,
      ...
    }
  }
}
```

---

## Data Models (Pydantic)

Define Pydantic models for request validation and response serialization.

### Member Model
```python
from pydantic import BaseModel, Field
from typing import Optional
from datetime import date

class MemberBase(BaseModel):
    member_id: int = Field(..., description="Unique member identifier")
    name: str = Field(..., description="Full name in Title Case")
    constituency: Optional[str] = Field(None, description="Electoral district")
    party: Optional[str] = Field(None, description="Political party")
    province_name: Optional[str] = Field(None, description="Province or territory")

class MemberDetail(MemberBase):
    current_roles: list[dict] = Field(default_factory=list)

class Config:
    from_attributes = True
```

### Role Model
```python
class RoleBase(BaseModel):
    role_id: int
    member_id: int
    role_type: str
    from_date: Optional[date]
    to_date: Optional[date]
    parliament_number: Optional[str]
    session_number: Optional[str]
    constituency_name: Optional[str]
    constituency_province: Optional[str]
    party: Optional[str]
    committee_name: Optional[str]
    affiliation_role_name: Optional[str]
    organization_name: Optional[str]
    office_role: Optional[str]
    election_result: Optional[str]

    class Config:
        from_attributes = True
```

### Vote Model
```python
class VoteBase(BaseModel):
    vote_id: int
    member_id: int
    parliament_number: int
    session_number: int
    vote_topic: Optional[str]
    subject: Optional[str]
    vote_result: Optional[str]
    vote_date: date
    member_vote: str

    class Config:
        from_attributes = True
```

### Bill Model
```python
class BillBase(BaseModel):
    bill_id: int
    bill_number: str
    parliament_number: int
    session_number: int
    status: Optional[str]
    sponsor_id: Optional[int]
    chamber: str

    class Config:
        from_attributes = True

class BillDetail(BillBase):
    sponsor: Optional[dict]
    progress: list[dict] = Field(default_factory=list)
```

---

## Technical Constraints

### Performance Requirements
1. **Response Time:** All API endpoints must respond within 500ms under normal load
2. **Pagination:** List endpoints must support pagination with configurable page sizes
3. **Database Queries:** Use batch operations and avoid N+1 query problems
4. **Indexing:** Create indexes on frequently queried columns (member_id, vote_date, parliament_number)

### Data Validation
1. **Date Formats:** All dates must be in ISO 8601 format (YYYY-MM-DD)
2. **Required Fields:** Enforce NOT NULL constraints at both database and API levels
3. **Enum Validation:** Role types must match the defined RoleType enum exactly

### Error Handling
1. **HTTP Status Codes:**
   - 200: Success
   - 400: Bad request (invalid parameters)
   - 404: Resource not found
   - 500: Internal server error
2. **Error Messages:** Must be clear and actionable
3. **Logging:** Log all errors with stack traces for debugging

### Security Considerations
1. **Input Sanitization:** Validate and sanitize all user inputs
2. **SQL Injection Prevention:** Use SQLAlchemy ORM exclusively (no raw SQL)
3. **Rate Limiting:** Implement rate limiting on API endpoints (100 requests/minute per IP)

---

## File Locations

```
parly/
├── db_setup/
│   ├── create_database.py        # Database schema definition
│   └── insert_*.py                # Data insertion scripts
├── api/
│   ├── main.py                    # FastAPI application entry point
│   ├── models.py                  # Pydantic models
│   ├── routes/
│   │   ├── members.py             # Member-related endpoints
│   │   ├── votes.py               # Vote-related endpoints
│   │   └── bills.py               # Bill-related endpoints
│   └── database.py                # Database connection utilities
└── data/
    └── parliament.db              # SQLite database file
```

---

## Version Information

- **Python:** 3.10+
- **FastAPI:** 0.104.0+
- **SQLAlchemy:** 2.0+
- **Pydantic:** 2.0+
- **Uvicorn:** 0.24.0+

