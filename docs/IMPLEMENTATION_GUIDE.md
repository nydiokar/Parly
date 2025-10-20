# Implementation Guide

## Overview

This guide provides step-by-step instructions for implementing the Parly Parliamentary Data API from the current state to a fully functional system. It is designed to be followed by an LLM or a developer with minimal oversight.

---

## Prerequisites

Before starting implementation, ensure you have:

1. **Python 3.10 or higher** installed
2. **Git** for version control
3. **A text editor or IDE** (VS Code, PyCharm, etc.)
4. **Internet connection** for scraping parliamentary data
5. **Windows PowerShell** (based on project environment)

---

## Implementation Phases

The implementation is divided into three phases, each building on the previous one.

### **Phase 1: Solidify the Data Foundation**
- Complete and fix existing scraping scripts
- Populate the database with all required data types

### **Phase 2: Build the API Layer**
- Set up FastAPI framework
- Implement API endpoints
- Add documentation

### **Phase 3: Refine and Automate**
- Create orchestration scripts
- Modernize project structure
- Add testing

---

## Phase 1: Solidify the Data Foundation

### Step 1.1: Set Up Development Environment

**Objective:** Prepare the project for development with proper dependency management.

**Actions:**

1. **Navigate to project directory:**
   ```powershell
   pwd
   cd C:\Users\solastic\prj\Parly
   ```

2. **Create a Python virtual environment:**
   ```powershell
   python -m venv venv
   ```

3. **Activate the virtual environment:**
   ```powershell
   .\venv\Scripts\Activate.ps1
   ```

4. **Verify existing dependencies:**
   - Current file: `requirements.txt`
   - Contains: beautifulsoup4, requests, pandas, SQLAlchemy, etc.

5. **Install dependencies:**
   ```powershell
   pip install -r requirements.txt
   ```

**Verification:**
```powershell
python -c "import sqlalchemy, requests, bs4, pandas; print('All dependencies installed')"
```

**Expected Output:** "All dependencies installed"

---

### Step 1.2: Initialize the Database

**Objective:** Create the SQLite database with the correct schema.

**Actions:**

1. **Ensure the data directory exists:**
   ```powershell
   if (!(Test-Path -Path "data")) { New-Item -ItemType Directory -Path "data" }
   ```

2. **Run the database creation script:**
   ```powershell
   python db_setup/create_database.py
   ```

**Expected Output:**
```
Database setup completed successfully.
```

**Verification:**
```powershell
Test-Path data/parliament.db
```
Should return `True`

**Files Created:**
- `data/parliament.db` (SQLite database with empty tables)

---

### Step 1.3: Fix and Run Member Role Insertion

**Objective:** Populate the `members` and `roles` tables from existing scraped data.

**Current Issue:** The `insert_roles_db.py` script has inefficiencies and uses incorrect member names.

**Actions:**

1. **Fix the member name issue:**
   
   **Problem:** Line 37 uses `search_pattern` instead of proper name.
   
   **Solution:** Read the proper name from `member_ids.csv` and create a lookup dictionary.

   **Modification Required in `db_setup/insert_roles_db.py`:**
   
   Add at the beginning of `insert_roles_from_json`:
   ```python
   # Load member names from CSV
   import csv
   member_names = {}
   with open('data/member_ids.csv', 'r', encoding='utf-8') as csv_file:
       reader = csv.DictReader(csv_file)
       for row in reader:
           member_names[row['id']] = row['name']
   ```
   
   Replace line 37:
   ```python
   # OLD: member = Member(member_id=member_id, name=search_pattern)
   # NEW:
   member = Member(member_id=member_id, name=member_names.get(str(member_id), search_pattern))
   ```

2. **Fix the inefficient commit issue:**
   
   **Problem:** Line 75 commits inside the loop (338 times).
   
   **Solution:** Remove line 75 and rely on the commit at line 106.
   
   **Modification Required in `db_setup/insert_roles_db.py`:**
   
   Delete or comment out line 75:
   ```python
   # session.commit()  # REMOVED: Commit once at the end instead
   ```

3. **Add duplicate prevention:**
   
   **Problem:** Running the script multiple times could attempt to insert duplicates.
   
   **Solution:** Check if a role already exists before adding it.
   
   **Modification Required in `db_setup/insert_roles_db.py`:**
   
   Add before `session.add(role)` at line 104:
   ```python
   # Check if role already exists
   existing_role = session.query(Role).filter_by(
       member_id=member.member_id,
       role_type=RoleType[role_type_str],
       from_date=from_date,
       parliament_number=role_data.get('parliament_number'),
       session_number=role_data.get('parliament_session')
   ).first()
   
   if existing_role:
       continue  # Skip if already exists
   ```

4. **Run the fixed script:**
   ```powershell
   python db_setup/insert_roles_db.py
   ```

**Expected Output:**
```
Data from data/member_roles.json has been inserted into the database successfully.
```

**Verification:**
```powershell
python scripts/db_check.py
```

**Expected Output:** Should show counts of members and roles matching the JSON file.

**Files Modified:**
- `db_setup/insert_roles_db.py`

**Database Tables Populated:**
- `members` (~338 rows)
- `roles` (~15,000+ rows depending on data)

---

### Step 1.4: Complete the Votes Scraper

**Objective:** Finish implementing the vote scraping and insertion functionality.

**Current State:** `scripts/extraction/fetch_votes.py` exists but is incomplete.

**Actions:**

1. **Create a new, complete votes scraper:**
   
   **File:** `scripts/extraction/fetch_votes.py`
   
   **Implementation Requirements:**
   - Read member IDs from `data/member_ids.csv`
   - For each member, fetch votes XML from: `https://www.ourcommons.ca/Members/en/{search_pattern}/votes/xml`
   - Parse XML structure (see DATA_SOURCES.md for format)
   - Insert directly into database `votes` table
   - Implement rate limiting (2 seconds between requests)
   - Handle errors gracefully (log and continue)
   
   **Key Code Structure:**
   ```python
   import csv
   import requests
   import xml.etree.ElementTree as ET
   from datetime import datetime
   import time
   from db_setup.create_database import Member, Vote, Session
   
   def fetch_votes_for_member(member_id, search_pattern):
       url = f"https://www.ourcommons.ca/Members/en/{search_pattern}/votes/xml"
       response = requests.get(url, timeout=10)
       if response.status_code == 200:
           return response.content
       return None
   
   def parse_votes_xml(xml_content, member_id):
       root = ET.fromstring(xml_content)
       votes = []
       for member_vote in root.findall('MemberVote'):
           # Parse each field according to DATA_SOURCES.md
           vote_date_str = member_vote.find('DecisionEventDateTime').text
           vote_date = datetime.fromisoformat(vote_date_str.split('T')[0])
           
           vote = Vote(
               member_id=member_id,
               parliament_number=int(member_vote.find('ParliamentNumber').text),
               session_number=int(member_vote.find('SessionNumber').text),
               vote_date=vote_date,
               vote_topic=member_vote.find('DecisionDivisionSubject').text[:255],
               subject=member_vote.find('DecisionDivisionSubject').text,
               vote_result=member_vote.find('DecisionResultName').text,
               member_vote=member_vote.find('VoteValueName').text
           )
           votes.append(vote)
       return votes
   
   def main():
       session = Session()
       with open('data/member_ids.csv', 'r') as f:
           reader = csv.DictReader(f)
           for row in reader:
               member_id = row['id']
               search_pattern = row['search_pattern']
               
               print(f"Fetching votes for {row['name']}...")
               xml_content = fetch_votes_for_member(member_id, search_pattern)
               
               if xml_content:
                   votes = parse_votes_xml(xml_content, int(member_id))
                   for vote in votes:
                       session.add(vote)
                   session.commit()
                   print(f"  Added {len(votes)} votes")
               
               time.sleep(2)  # Rate limiting
       
       session.close()
   
   if __name__ == "__main__":
       main()
   ```

2. **Run the votes scraper:**
   ```powershell
   python scripts/extraction/fetch_votes.py
   ```

**Expected Duration:** ~11 minutes (338 members × 2 seconds)

**Expected Output:**
```
Fetching votes for Ziad Aboultaif...
  Added 156 votes
Fetching votes for Scott Aitchison...
  Added 203 votes
...
```

**Verification:**
```powershell
python -c "from db_setup.create_database import Session, Vote; print(f'Total votes: {Session().query(Vote).count()}')"
```

**Files Created:**
- `scripts/extraction/fetch_votes.py` (completed version)

**Database Tables Populated:**
- `votes` (~50,000+ rows depending on parliamentary activity)

---

### Step 1.5: Create the Bills Scraper

**Objective:** Implement scraping for bills sponsored by each member.

**Current State:** Script does not exist.

**Actions:**

1. **Create the bills scraper:**
   
   **File:** `scripts/extraction/fetch_bills.py`
   
   **Implementation Requirements:**
   - Read member IDs from `data/member_ids.csv`
   - For each member, fetch bills XML from: `https://www.parl.ca/legisinfo/en/bills/xml?parlsession=all&sponsor={member_id}&advancedview=true`
   - Parse XML structure
   - Insert into database `bills` table
   - Implement rate limiting (2 seconds between requests)
   
   **Key Code Structure:**
   ```python
   import csv
   import requests
   import xml.etree.ElementTree as ET
   import time
   from db_setup.create_database import Bill, Session
   
   def fetch_bills_for_member(member_id):
       url = f"https://www.parl.ca/legisinfo/en/bills/xml?parlsession=all&sponsor={member_id}&advancedview=true"
       response = requests.get(url, timeout=10)
       if response.status_code == 200:
           return response.content
       return None
   
   def parse_bills_xml(xml_content):
       root = ET.fromstring(xml_content)
       bills = []
       for bill_elem in root.findall('Bill'):
           bill = Bill(
               bill_number=bill_elem.find('NumberCode').text,
               parliament_number=int(bill_elem.find('ParliamentNumber').text),
               session_number=int(bill_elem.find('SessionNumber').text),
               status=bill_elem.find('StatusName').text,
               sponsor_id=int(bill_elem.find('SponsorPersonId').text),
               chamber=bill_elem.find('OriginatingChamberName').text
           )
           bills.append(bill)
       return bills
   
   def main():
       session = Session()
       with open('data/member_ids.csv', 'r') as f:
           reader = csv.DictReader(f)
           for row in reader:
               member_id = row['id']
               
               print(f"Fetching bills for {row['name']}...")
               xml_content = fetch_bills_for_member(member_id)
               
               if xml_content:
                   bills = parse_bills_xml(xml_content)
                   for bill in bills:
                       # Check if bill already exists
                       existing = session.query(Bill).filter_by(
                           bill_number=bill.bill_number,
                           parliament_number=bill.parliament_number,
                           session_number=bill.session_number
                       ).first()
                       if not existing:
                           session.add(bill)
                   session.commit()
                   print(f"  Added {len(bills)} bills")
               
               time.sleep(2)  # Rate limiting
       
       session.close()
   
   if __name__ == "__main__":
       main()
   ```

2. **Run the bills scraper:**
   ```powershell
   python scripts/extraction/fetch_bills.py
   ```

**Expected Duration:** ~11 minutes

**Expected Output:**
```
Fetching bills for Ziad Aboultaif...
  Added 3 bills
Fetching bills for Scott Aitchison...
  Added 5 bills
...
```

**Verification:**
```powershell
python -c "from db_setup.create_database import Session, Bill; print(f'Total bills: {Session().query(Bill).count()}')"
```

**Files Created:**
- `scripts/extraction/fetch_bills.py`

**Database Tables Populated:**
- `bills` (~1,000+ rows)

---

### Step 1.6: Create the Bill Progress Scraper

**Objective:** Implement scraping for legislative progress of bills.

**Current State:** Script does not exist.

**Actions:**

1. **Create the bill progress scraper:**
   
   **File:** `scripts/extraction/fetch_bill_progress.py`
   
   **Implementation Requirements:**
   - Read bills from database
   - For each bill, fetch progress JSON from: `https://www.parl.ca/LegisInfo/en/bill/{parliament}-{session}/{bill_type}-{bill_number}/json?view=progress`
   - Parse JSON structure
   - Insert into database `bill_progress` table
   - Implement rate limiting (1 second between requests)
   
   **Key Code Structure:**
   ```python
   import requests
   import time
   from datetime import datetime
   from db_setup.create_database import Bill, BillProgress, Session
   
   def fetch_bill_progress(parliament, session_num, bill_number):
       # Extract bill type from number (C or S)
       bill_type = bill_number.split('-')[0]
       bill_num = bill_number.split('-')[1]
       
       url = f"https://www.parl.ca/LegisInfo/en/bill/{parliament}-{session_num}/{bill_type}-{bill_num}/json?view=progress"
       response = requests.get(url, timeout=10)
       if response.status_code == 200:
           return response.json()
       return None
   
   def parse_progress_json(json_data, bill_id):
       progress_records = []
       
       bill_stages = json_data.get('BillStages', {})
       
       # Process House stages
       for stage in bill_stages.get('HouseBillStages', []):
           if stage.get('State') == 4:  # Completed
               date_str = stage.get('StateAsOfDate')
               if date_str:
                   progress_date = datetime.fromisoformat(date_str.split('T')[0])
                   progress = BillProgress(
                       bill_id=bill_id,
                       status=stage.get('BillStageName'),
                       progress_date=progress_date
                   )
                   progress_records.append(progress)
       
       # Process Senate stages
       for stage in bill_stages.get('SenateBillStages', []):
           if stage.get('State') == 4:  # Completed
               date_str = stage.get('StateAsOfDate')
               if date_str:
                   progress_date = datetime.fromisoformat(date_str.split('T')[0])
                   progress = BillProgress(
                       bill_id=bill_id,
                       status=f"Senate: {stage.get('BillStageName')}",
                       progress_date=progress_date
                   )
                   progress_records.append(progress)
       
       return progress_records
   
   def main():
       session = Session()
       bills = session.query(Bill).all()
       
       for bill in bills:
           print(f"Fetching progress for {bill.bill_number}...")
           json_data = fetch_bill_progress(
               bill.parliament_number,
               bill.session_number,
               bill.bill_number
           )
           
           if json_data:
               progress_records = parse_progress_json(json_data, bill.bill_id)
               for progress in progress_records:
                   # Check if already exists
                   existing = session.query(BillProgress).filter_by(
                       bill_id=progress.bill_id,
                       status=progress.status,
                       progress_date=progress.progress_date
                   ).first()
                   if not existing:
                       session.add(progress)
               session.commit()
               print(f"  Added {len(progress_records)} progress records")
           
           time.sleep(1)  # Rate limiting
       
       session.close()
   
   if __name__ == "__main__":
       main()
   ```

2. **Run the bill progress scraper:**
   ```powershell
   python scripts/extraction/fetch_bill_progress.py
   ```

**Expected Duration:** Varies based on number of bills (~15-30 minutes)

**Expected Output:**
```
Fetching progress for C-1...
  Added 2 progress records
Fetching progress for C-10...
  Added 5 progress records
...
```

**Verification:**
```powershell
python -c "from db_setup.create_database import Session, BillProgress; print(f'Total progress records: {Session().query(BillProgress).count()}')"
```

**Files Created:**
- `scripts/extraction/fetch_bill_progress.py`

**Database Tables Populated:**
- `bill_progress` (~5,000+ rows)

---

## Phase 2: Build the API Layer

### Step 2.1: Add FastAPI Dependencies

**Objective:** Install and configure FastAPI and related packages.

**Actions:**

1. **Update dependencies:**
   
   Add to `requirements.txt`:
   ```
   fastapi==0.104.1
   uvicorn[standard]==0.24.0
   pydantic==2.5.0
   ```

2. **Install new dependencies:**
   ```powershell
   pip install fastapi uvicorn[standard] pydantic
   ```

**Verification:**
```powershell
python -c "import fastapi, uvicorn, pydantic; print('FastAPI dependencies installed')"
```

---

### Step 2.2: Create API Directory Structure

**Objective:** Set up the file structure for the API.

**Actions:**

1. **Create directories:**
   ```powershell
   New-Item -ItemType Directory -Path "api"
   New-Item -ItemType Directory -Path "api\routes"
   ```

2. **Create empty `__init__.py` files:**
   ```powershell
   New-Item -ItemType File -Path "api\__init__.py"
   New-Item -ItemType File -Path "api\routes\__init__.py"
   ```

**Expected Structure:**
```
parly/
├── api/
│   ├── __init__.py
│   ├── main.py              (to be created)
│   ├── database.py          (to be created)
│   ├── models.py            (to be created)
│   ├── dependencies.py      (to be created)
│   └── routes/
│       ├── __init__.py
│       ├── members.py       (to be created)
│       ├── votes.py         (to be created)
│       ├── bills.py         (to be created)
│       └── statistics.py    (to be created)
```

---

### Step 2.3: Create Database Connection Module

**Objective:** Set up database connection utilities for the API.

**Actions:**

1. **Create `api/database.py`:**
   ```python
   from sqlalchemy import create_engine
   from sqlalchemy.orm import sessionmaker
   from db_setup.create_database import Base
   
   DATABASE_URL = "sqlite:///data/parliament.db"
   
   engine = create_engine(
       DATABASE_URL,
       connect_args={"check_same_thread": False}  # Needed for SQLite
   )
   
   SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
   
   def get_db():
       """Dependency for getting database sessions."""
       db = SessionLocal()
       try:
           yield db
       finally:
           db.close()
   ```

**Files Created:**
- `api/database.py`

---

### Step 2.4: Create Pydantic Models

**Objective:** Define response models for API endpoints.

**Actions:**

1. **Create `api/models.py`:**
   ```python
   from pydantic import BaseModel, Field
   from typing import Optional, List
   from datetime import date
   
   # Member Models
   class MemberBase(BaseModel):
       member_id: int
       name: str
       constituency: Optional[str] = None
       party: Optional[str] = None
       province_name: Optional[str] = None
       
       class Config:
           from_attributes = True
   
   class MemberDetail(MemberBase):
       current_roles: List[dict] = []
   
   # Role Models
   class RoleBase(BaseModel):
       role_id: int
       role_type: str
       from_date: Optional[date] = None
       to_date: Optional[date] = None
       parliament_number: Optional[str] = None
       session_number: Optional[str] = None
       constituency_name: Optional[str] = None
       committee_name: Optional[str] = None
       organization_name: Optional[str] = None
       
       class Config:
           from_attributes = True
   
   # Vote Models
   class VoteBase(BaseModel):
       vote_id: int
       parliament_number: int
       session_number: int
       vote_date: date
       vote_topic: Optional[str] = None
       member_vote: str
       vote_result: Optional[str] = None
       
       class Config:
           from_attributes = True
   
   # Bill Models
   class BillBase(BaseModel):
       bill_id: int
       bill_number: str
       parliament_number: int
       session_number: int
       status: Optional[str] = None
       sponsor_id: Optional[int] = None
       chamber: str
       
       class Config:
           from_attributes = True
   
   class BillDetail(BillBase):
       sponsor_name: Optional[str] = None
       progress: List[dict] = []
   
   # Response wrapper
   class SuccessResponse(BaseModel):
       status: str = "success"
       data: any
   
   class PaginatedResponse(BaseModel):
       status: str = "success"
       data: List[any]
       pagination: dict
   ```

**Files Created:**
- `api/models.py`

---

### Step 2.5: Implement Member Endpoints

**Objective:** Create API routes for member-related queries.

**Actions:**

1. **Create `api/routes/members.py`:**
   ```python
   from fastapi import APIRouter, Depends, HTTPException, Query
   from sqlalchemy.orm import Session
   from typing import Optional
   from api.database import get_db
   from api.models import MemberBase, MemberDetail
   from db_setup.create_database import Member, Role
   
   router = APIRouter(prefix="/api/members", tags=["members"])
   
   @router.get("/", response_model=dict)
   def get_members(
       page: int = Query(1, ge=1),
       per_page: int = Query(50, ge=1, le=100),
       party: Optional[str] = None,
       province: Optional[str] = None,
       db: Session = Depends(get_db)
   ):
       """Get list of all members with optional filtering."""
       query = db.query(Member)
       
       if party:
           query = query.filter(Member.party == party)
       if province:
           query = query.filter(Member.province_name == province)
       
       total = query.count()
       members = query.offset((page - 1) * per_page).limit(per_page).all()
       
       return {
           "status": "success",
           "data": [MemberBase.model_validate(m) for m in members],
           "pagination": {
               "page": page,
               "per_page": per_page,
               "total": total,
               "total_pages": (total + per_page - 1) // per_page
           }
       }
   
   @router.get("/{member_id}", response_model=dict)
   def get_member(member_id: int, db: Session = Depends(get_db)):
       """Get detailed information for a specific member."""
       member = db.query(Member).filter(Member.member_id == member_id).first()
       
       if not member:
           raise HTTPException(status_code=404, detail="Member not found")
       
       # Get current roles (where to_date is None)
       current_roles = db.query(Role).filter(
           Role.member_id == member_id,
           Role.to_date.is_(None)
       ).all()
       
       member_data = MemberBase.model_validate(member)
       member_dict = member_data.model_dump()
       member_dict["current_roles"] = [
           {
               "role_type": role.role_type.value,
               "from_date": role.from_date,
               "constituency_name": role.constituency_name,
               "committee_name": role.committee_name
           }
           for role in current_roles
       ]
       
       return {"status": "success", "data": member_dict}
   
   @router.get("/{member_id}/roles", response_model=dict)
   def get_member_roles(
       member_id: int,
       active_only: bool = Query(False),
       db: Session = Depends(get_db)
   ):
       """Get all roles for a specific member."""
       member = db.query(Member).filter(Member.member_id == member_id).first()
       if not member:
           raise HTTPException(status_code=404, detail="Member not found")
       
       query = db.query(Role).filter(Role.member_id == member_id)
       
       if active_only:
           query = query.filter(Role.to_date.is_(None))
       
       roles = query.all()
       
       roles_data = [
           {
               "role_id": role.role_id,
               "role_type": role.role_type.value,
               "from_date": role.from_date,
               "to_date": role.to_date,
               "parliament_number": role.parliament_number,
               "session_number": role.session_number,
               "constituency_name": role.constituency_name,
               "committee_name": role.committee_name,
               "organization_name": role.organization_name
           }
           for role in roles
       ]
       
       return {"status": "success", "data": roles_data}
   ```

**Files Created:**
- `api/routes/members.py`

---

### Step 2.6: Implement Vote Endpoints

**Objective:** Create API routes for vote-related queries.

**Actions:**

1. **Create `api/routes/votes.py`:**
   ```python
   from fastapi import APIRouter, Depends, HTTPException, Query
   from sqlalchemy.orm import Session
   from typing import Optional
   from datetime import date
   from api.database import get_db
   from api.models import VoteBase
   from db_setup.create_database import Vote
   
   router = APIRouter(prefix="/api/members/{member_id}/votes", tags=["votes"])
   
   @router.get("/", response_model=dict)
   def get_member_votes(
       member_id: int,
       page: int = Query(1, ge=1),
       per_page: int = Query(50, ge=1, le=100),
       parliament: Optional[int] = None,
       from_date: Optional[date] = None,
       to_date: Optional[date] = None,
       db: Session = Depends(get_db)
   ):
       """Get voting records for a specific member."""
       query = db.query(Vote).filter(Vote.member_id == member_id)
       
       if parliament:
           query = query.filter(Vote.parliament_number == parliament)
       if from_date:
           query = query.filter(Vote.vote_date >= from_date)
       if to_date:
           query = query.filter(Vote.vote_date <= to_date)
       
       total = query.count()
       votes = query.order_by(Vote.vote_date.desc()).offset((page - 1) * per_page).limit(per_page).all()
       
       return {
           "status": "success",
           "data": [VoteBase.model_validate(v) for v in votes],
           "pagination": {
               "page": page,
               "per_page": per_page,
               "total": total,
               "total_pages": (total + per_page - 1) // per_page
           }
       }
   ```

**Files Created:**
- `api/routes/votes.py`

---

### Step 2.7: Implement Bill Endpoints

**Objective:** Create API routes for bill-related queries.

**Actions:**

1. **Create `api/routes/bills.py`:**
   ```python
   from fastapi import APIRouter, Depends, HTTPException, Query
   from sqlalchemy.orm import Session
   from typing import Optional
   from api.database import get_db
   from api.models import BillBase
   from db_setup.create_database import Bill, BillProgress, Member
   
   router = APIRouter(prefix="/api/bills", tags=["bills"])
   
   @router.get("/", response_model=dict)
   def get_bills(
       page: int = Query(1, ge=1),
       per_page: int = Query(50, ge=1, le=100),
       parliament: Optional[int] = None,
       session: Optional[int] = None,
       sponsor_id: Optional[int] = None,
       db: Session = Depends(get_db)
   ):
       """Get list of bills with optional filtering."""
       query = db.query(Bill)
       
       if parliament:
           query = query.filter(Bill.parliament_number == parliament)
       if session:
           query = query.filter(Bill.session_number == session)
       if sponsor_id:
           query = query.filter(Bill.sponsor_id == sponsor_id)
       
       total = query.count()
       bills = query.offset((page - 1) * per_page).limit(per_page).all()
       
       # Enrich with sponsor names
       bills_data = []
       for bill in bills:
           bill_dict = BillBase.model_validate(bill).model_dump()
           if bill.sponsor_id:
               sponsor = db.query(Member).filter(Member.member_id == bill.sponsor_id).first()
               bill_dict["sponsor_name"] = sponsor.name if sponsor else None
           bills_data.append(bill_dict)
       
       return {
           "status": "success",
           "data": bills_data,
           "pagination": {
               "page": page,
               "per_page": per_page,
               "total": total,
               "total_pages": (total + per_page - 1) // per_page
           }
       }
   
   @router.get("/{bill_id}", response_model=dict)
   def get_bill(bill_id: int, db: Session = Depends(get_db)):
       """Get detailed information for a specific bill."""
       bill = db.query(Bill).filter(Bill.bill_id == bill_id).first()
       
       if not bill:
           raise HTTPException(status_code=404, detail="Bill not found")
       
       # Get sponsor
       sponsor = None
       if bill.sponsor_id:
           sponsor_obj = db.query(Member).filter(Member.member_id == bill.sponsor_id).first()
           if sponsor_obj:
               sponsor = {"member_id": sponsor_obj.member_id, "name": sponsor_obj.name}
       
       # Get progress
       progress_records = db.query(BillProgress).filter(
           BillProgress.bill_id == bill_id
       ).order_by(BillProgress.progress_date).all()
       
       progress = [
           {
               "progress_id": p.progress_id,
               "status": p.status,
               "progress_date": p.progress_date
           }
           for p in progress_records
       ]
       
       bill_data = BillBase.model_validate(bill).model_dump()
       bill_data["sponsor"] = sponsor
       bill_data["progress"] = progress
       
       return {"status": "success", "data": bill_data}
   ```

**Files Created:**
- `api/routes/bills.py`

---

### Step 2.8: Implement Statistics Endpoint

**Objective:** Create an endpoint for aggregate statistics.

**Actions:**

1. **Create `api/routes/statistics.py`:**
   ```python
   from fastapi import APIRouter, Depends
   from sqlalchemy.orm import Session
   from sqlalchemy import func
   from api.database import get_db
   from db_setup.create_database import Member, Vote, Bill
   
   router = APIRouter(prefix="/api/statistics", tags=["statistics"])
   
   @router.get("/", response_model=dict)
   def get_statistics(db: Session = Depends(get_db)):
       """Get aggregate statistics about parliamentary data."""
       
       total_members = db.query(Member).count()
       total_votes = db.query(Vote).count()
       total_bills = db.query(Bill).count()
       
       # Count by party
       by_party = db.query(
           Member.party,
           func.count(Member.member_id)
       ).filter(Member.party.isnot(None)).group_by(Member.party).all()
       
       # Count by province
       by_province = db.query(
           Member.province_name,
           func.count(Member.member_id)
       ).filter(Member.province_name.isnot(None)).group_by(Member.province_name).all()
       
       return {
           "status": "success",
           "data": {
               "total_members": total_members,
               "total_votes": total_votes,
               "total_bills": total_bills,
               "by_party": {party: count for party, count in by_party},
               "by_province": {province: count for province, count in by_province}
           }
       }
   ```

**Files Created:**
- `api/routes/statistics.py`

---

### Step 2.9: Create Main API Application

**Objective:** Set up the FastAPI application and register all routes.

**Actions:**

1. **Create `api/main.py`:**
   ```python
   from fastapi import FastAPI
   from fastapi.middleware.cors import CORSMiddleware
   from api.routes import members, votes, bills, statistics
   
   app = FastAPI(
       title="Parly - Parliamentary Data API",
       description="A comprehensive API for Canadian parliamentary data",
       version="1.0.0",
       docs_url="/docs",
       redoc_url="/redoc"
   )
   
   # Configure CORS
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["*"],  # In production, specify actual origins
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )
   
   # Include routers
   app.include_router(members.router)
   app.include_router(votes.router)
   app.include_router(bills.router)
   app.include_router(statistics.router)
   
   @app.get("/")
   def root():
       return {
           "message": "Welcome to Parly API",
           "documentation": "/docs",
           "version": "1.0.0"
       }
   
   @app.get("/health")
   def health_check():
       return {"status": "healthy"}
   ```

**Files Created:**
- `api/main.py`

---

### Step 2.10: Run and Test the API

**Objective:** Start the API server and verify all endpoints work.

**Actions:**

1. **Start the API server:**
   ```powershell
   uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
   ```

**Expected Output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

2. **Access the API documentation:**
   - Open browser: `http://localhost:8000/docs`
   - You should see the Swagger UI with all endpoints

3. **Test endpoints manually:**
   - **GET** `http://localhost:8000/api/members` - Should return list of members
   - **GET** `http://localhost:8000/api/members/89156` - Should return Ziad Aboultaif's details
   - **GET** `http://localhost:8000/api/statistics` - Should return aggregate statistics

**Verification:**
All endpoints should return JSON responses with `status: "success"`.

---

## Phase 3: Refine and Automate

### Step 3.1: Create Pipeline Orchestrator

**Objective:** Create a master script to run the entire data pipeline.

**Actions:**

1. **Create `run_pipeline.py` in the project root:**
   ```python
   """
   Master orchestrator for the Parly data pipeline.
   Runs all scraping and insertion scripts in the correct order.
   """
   import subprocess
   import sys
   from datetime import datetime
   
   def run_script(script_path: str, description: str):
       """Run a Python script and handle errors."""
       print(f"\n{'='*60}")
       print(f"[{datetime.now().strftime('%H:%M:%S')}] {description}")
       print(f"{'='*60}")
       
       try:
           result = subprocess.run(
               [sys.executable, script_path],
               check=True,
               capture_output=True,
               text=True
           )
           print(result.stdout)
           print(f"✓ {description} completed successfully")
           return True
       except subprocess.CalledProcessError as e:
           print(f"✗ {description} failed")
           print(f"Error: {e.stderr}")
           return False
   
   def main():
       print("Starting Parly Data Pipeline")
       print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
       
       steps = [
           ("db_setup/create_database.py", "Initialize Database"),
           ("scripts/extraction/member_id_scraper.py", "Scrape Member IDs"),
           ("scripts/extraction/scrape_roles.py", "Scrape Member Roles"),
           ("db_setup/insert_roles_db.py", "Insert Members and Roles"),
           ("scripts/extraction/fetch_votes.py", "Scrape and Insert Votes"),
           ("scripts/extraction/fetch_bills.py", "Scrape and Insert Bills"),
           ("scripts/extraction/fetch_bill_progress.py", "Scrape and Insert Bill Progress"),
       ]
       
       results = []
       for script, description in steps:
           success = run_script(script, description)
           results.append((description, success))
       
       print(f"\n{'='*60}")
       print("Pipeline Summary")
       print(f"{'='*60}")
       for description, success in results:
           status = "✓ PASS" if success else "✗ FAIL"
           print(f"{status}: {description}")
       
       print(f"\nEnd time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
       
       all_success = all(success for _, success in results)
       sys.exit(0 if all_success else 1)
   
   if __name__ == "__main__":
       main()
   ```

2. **Run the pipeline:**
   ```powershell
   python run_pipeline.py
   ```

**Expected Duration:** ~40-60 minutes (full data refresh)

**Files Created:**
- `run_pipeline.py`

---

### Step 3.2: Convert to pyproject.toml

**Objective:** Modernize dependency management using `pyproject.toml`.

**Actions:**

1. **Create `pyproject.toml`:**
   ```toml
   [project]
   name = "parly"
   version = "1.0.0"
   description = "Parliamentary Data API for Canadian Parliament"
   readme = "README.md"
   requires-python = ">=3.10"
   license = {text = "MIT"}
   
   dependencies = [
       "beautifulsoup4==4.12.3",
       "requests==2.32.3",
       "pandas==2.2.3",
       "SQLAlchemy==2.0.36",
       "fastapi==0.104.1",
       "uvicorn[standard]==0.24.0",
       "pydantic==2.5.0",
   ]
   
   [project.optional-dependencies]
   dev = [
       "pytest==7.4.3",
       "pytest-cov==4.1.0",
       "black==23.12.0",
       "ruff==0.1.8",
   ]
   
   [build-system]
   requires = ["setuptools>=61.0"]
   build-backend = "setuptools.build_meta"
   
   [tool.black]
   line-length = 100
   target-version = ['py310']
   
   [tool.ruff]
   line-length = 100
   select = ["E", "F", "W"]
   ```

2. **Install from pyproject.toml:**
   ```powershell
   pip install -e .
   ```

3. **Install dev dependencies:**
   ```powershell
   pip install -e ".[dev]"
   ```

**Files Created:**
- `pyproject.toml`

**Files to Deprecate (but keep for now):**
- `requirements.txt` (can be removed after confirming pyproject.toml works)

---

### Step 3.3: Add Basic Testing

**Objective:** Implement unit and integration tests.

**Actions:**

1. **Create test directory:**
   ```powershell
   New-Item -ItemType Directory -Path "tests"
   New-Item -ItemType File -Path "tests\__init__.py"
   ```

2. **Create `tests/test_api.py`:**
   ```python
   import pytest
   from fastapi.testclient import TestClient
   from api.main import app
   
   client = TestClient(app)
   
   def test_root():
       response = client.get("/")
       assert response.status_code == 200
       assert response.json()["message"] == "Welcome to Parly API"
   
   def test_health():
       response = client.get("/health")
       assert response.status_code == 200
       assert response.json()["status"] == "healthy"
   
   def test_get_members():
       response = client.get("/api/members")
       assert response.status_code == 200
       assert response.json()["status"] == "success"
       assert "data" in response.json()
       assert "pagination" in response.json()
   
   def test_get_statistics():
       response = client.get("/api/statistics")
       assert response.status_code == 200
       assert response.json()["status"] == "success"
       assert "total_members" in response.json()["data"]
   ```

3. **Run tests:**
   ```powershell
   pytest tests/ -v
   ```

**Expected Output:**
```
tests/test_api.py::test_root PASSED
tests/test_api.py::test_health PASSED
tests/test_api.py::test_get_members PASSED
tests/test_api.py::test_get_statistics PASSED
```

**Files Created:**
- `tests/__init__.py`
- `tests/test_api.py`

---

## Verification Checklist

After completing all phases, verify the following:

- [ ] Database exists and is populated: `data/parliament.db`
- [ ] Members table has ~338 rows
- [ ] Roles table has ~15,000+ rows
- [ ] Votes table has ~50,000+ rows
- [ ] Bills table has ~1,000+ rows
- [ ] Bill progress table has ~5,000+ rows
- [ ] API server starts without errors
- [ ] API documentation accessible at `http://localhost:8000/docs`
- [ ] All API endpoints return successful responses
- [ ] Tests pass with `pytest`
- [ ] `run_pipeline.py` executes successfully

---

## Troubleshooting

### Database is Locked
**Symptom:** "database is locked" error when running scripts.

**Solution:**
1. Close any open database connections
2. Restart PowerShell
3. Ensure only one script accesses the database at a time

### Module Import Errors
**Symptom:** `ModuleNotFoundError` when running scripts.

**Solution:**
1. Ensure virtual environment is activated
2. Install all dependencies: `pip install -e ".[dev]"`
3. Run scripts from the project root directory

### API Slow Response Times
**Symptom:** API responses take >1 second.

**Solution:**
1. Add database indexes (see TECHNICAL_SPECIFICATION.md)
2. Reduce `per_page` parameter
3. Consider adding response caching

---

## Next Steps After Implementation

Once all three phases are complete, consider:

1. **Deployment:** Deploy the API to a production server
2. **Monitoring:** Add logging and monitoring tools
3. **Documentation:** Create user guides and API usage examples
4. **Analysis Layer:** Begin work on the LLM-powered analysis system
5. **Data Updates:** Set up scheduled scraping (daily/weekly)

---

## Estimated Time to Complete

- **Phase 1:** 4-6 hours (including scraping time)
- **Phase 2:** 3-4 hours
- **Phase 3:** 2-3 hours

**Total:** 9-13 hours of active development (plus scraping wait time)

---

## Success Criteria

The implementation is considered complete when:

1. All database tables are populated with current data
2. The API server runs without errors
3. All documented endpoints return valid responses
4. API documentation is accessible and accurate
5. Basic tests pass
6. The orchestrator script runs the full pipeline successfully

