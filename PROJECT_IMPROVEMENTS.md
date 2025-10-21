# Parly Project Analysis and Improvement Recommendations

## Executive Summary

This document analyzes the current state of the Parly project, identifies discrepancies, and provides actionable recommendations for improving the project setup to make it professional, maintainable, and easy to work with.

---

## Current Issues Discovered

### 1. **Schema Mismatch Between Database and API** (HIGH PRIORITY)

**Problem:**
The API models (Pydantic schemas) don't match the actual database schema:

**Database Schema (Actual):**
```python
# Member table
- member_id
- name  # Single field, not split
- constituency
- province_name  # Not "province"
- party

# Vote table (from ParliamentaryAssociation)
- vote_id
- member_id
- parliament_number
- session_number
- vote_date
- subject
- vote_topic
- vote_result
- member_vote  # Individual member's vote
```

**API Models (Incorrect):**
```python
# MemberBase
- member_id
- first_name  # DOESN'T EXIST
- last_name   # DOESN'T EXIST
- province    # Should be province_name
```

**Impact:** API endpoints return 500 errors when trying to serialize database objects.

**Solution:** Update Pydantic models to match actual database schema OR update database schema to match desired API format.

---

### 2. **Data Model Confusion** (HIGH PRIORITY)

**Problem:**
The database has TWO different vote-related tables with overlapping purposes:

1. **`Vote` table**: Stores individual member votes (vote_id, member_id, member_vote, vote_result)
2. **`ParliamentaryAssociation` table**: Supposed to store member-vote associations

**Current State:**
- The `Vote` table is actually storing what should be in `ParliamentaryAssociation` (member-level vote records)
- The `ParliamentaryAssociation` table has NO DATA (0 records)
- This makes the schema confusing and the API endpoints fail

**Recommendation:** Choose one approach:

**Option A (Recommended):** Two-table design
- `Vote` table: Aggregate vote information (vote number, date, topic, totals, outcome)
- `VoteParticipant` table: Individual member votes

**Option B:** Single-table design
- Keep current `Vote` table as-is (member-level records)
- Remove `ParliamentaryAssociation` table entirely

---

### 3. **Naming Inconsistencies** (MEDIUM PRIORITY)

**Issues:**
- `province` vs `province_name`
- `name` (single field) vs `first_name` + `last_name` (split fields)
- `member_vote` vs `vote_status`
- `vote_result` vs `decision`

**Recommendation:** Standardize naming across the project. Suggested conventions:
```python
# Members
- full_name or name (keep as single field)
- province (remove _name suffix)

# Votes
- vote_status (for member's vote: Yea/Nay/Paired)
- vote_outcome (for overall result: Agreed/Negatived)
```

---

## What's Currently Needed vs Excess

### ✅ **What's Needed and Well-Built**

1. **Modern Dependency Management (pyproject.toml)**
   - Excellent! This replaces the old requirements.txt
   - Includes proper metadata, optional dependencies, tool configurations
   - **Keep this**

2. **Production-Grade Scrapers**
   - fetch_votes.py, fetch_bills.py, fetch_bill_progress.py
   - Include retry logic, checkpointing, logging, error handling
   - **Keep all of these**

3. **API Layer Structure**
   - FastAPI with proper routing
   - Pydantic models for validation
   - Database session management
   - **Keep, but needs schema fixes**

4. **.gitignore and Settings**
   - Comprehensive .gitignore
   - Proper Claude Code settings (no telemetry, blocked destructive commands)
   - **Keep as-is**

### ❌ **What's Excess or Problematic**

1. **Old requirements.txt**
   - Now that we have pyproject.toml, this is redundant
   - **Action:** Delete it

2. **Duplicate Vote Tables**
   - Having both `Vote` and `ParliamentaryAssociation` with unclear purposes
   - **Action:** Redesign schema (see recommendations below)

3. **Incomplete API Models**
   - Models reference fields that don't exist in the database
   - **Action:** Rebuild models to match actual schema

---

## Recommended Project Improvements

### 1. **Database Schema Refactoring** (Critical)

**Current Problems:**
- Vote table structure is confusing
- ParliamentaryAssociation table is empty and unused
- Member name not split into first/last

**Recommended New Schema:**

```python
# Option A: Clean two-table vote design
class Vote(Base):
    """Aggregate vote information"""
    __tablename__ = 'votes'
    vote_id = Column(Integer, primary_key=True)
    vote_number = Column(Integer)
    parliament_number = Column(Integer)
    session_number = Column(Integer)
    sitting_number = Column(Integer)
    vote_date = Column(Date)
    subject = Column(Text)
    topic = Column(Text)
    outcome = Column(String)  # Agreed/Negatived
    yea_total = Column(Integer)
    nay_total = Column(Integer)
    paired_total = Column(Integer)

class VoteParticipant(Base):
    """Individual member's vote in a specific vote"""
    __tablename__ = 'vote_participants'
    participant_id = Column(Integer, primary_key=True)
    vote_id = Column(Integer, ForeignKey('votes.vote_id'))
    member_id = Column(Integer, ForeignKey('members.member_id'))
    vote_status = Column(String)  # Yea/Nay/Paired

class Member(Base):
    """Member of Parliament"""
    __tablename__ = 'members'
    member_id = Column(Integer, primary_key=True)
    full_name = Column(String)  # Or split into first_name/last_name
    constituency = Column(String)
    province = Column(String)  # Rename from province_name
    party = Column(String)
```

**Migration Path:**
1. Create migration script to restructure data
2. Extract aggregate vote info from current Vote table
3. Keep individual vote records as VoteParticipant
4. Update all scrapers to use new schema

### 2. **Add Missing Development Tools**

**Tools to Add:**

```bash
# Install development dependencies
pip install -e ".[dev]"
```

**What this adds:**
- `ruff` - Modern linter and formatter (replaces flake8, black, isort)
- `mypy` - Type checking
- `pytest` - Testing framework
- `httpx` - For testing API endpoints

**Usage:**
```bash
# Format code
ruff format .

# Lint code
ruff check .

# Type check
mypy api/ scripts/

# Run tests
pytest
```

### 3. **Create Missing Project Files**

#### A. **Setup Guide** (SETUP.md)

```markdown
# Parly Project Setup

## Installation

\```bash
# Clone repository
git clone <repo-url>
cd Parly

# Install project in editable mode with dev dependencies
pip install -e ".[dev]"

# Verify installation
python -c "import parly; print('Success!')"
\```

## Running Scrapers

\```bash
# Scrape members
python scripts/extraction/members/fetch_members.py

# Scrape votes
python scripts/extraction/votes/fetch_votes.py

# Scrape bills
python scripts/extraction/bills/fetch_bills.py
python scripts/extraction/bills/fetch_bill_progress.py
\```

## Running API

\```bash
# Start API server
uvicorn api.main:app --reload --port 8000

# Access API docs
open http://localhost:8000/docs
\```
```

#### B. **API Documentation** (API.md)

Document all endpoints with examples

#### C. **Contributing Guide** (CONTRIBUTING.md)

Code style, PR process, testing requirements

### 4. **Add Testing Infrastructure**

**Create test suite:**
```
tests/
├── __init__.py
├── conftest.py          # Pytest fixtures
├── test_api/
│   ├── test_members.py
│   ├── test_votes.py
│   └── test_bills.py
└── test_scrapers/
    ├── test_fetch_members.py
    ├── test_fetch_votes.py
    └── test_fetch_bills.py
```

**Example test:**
```python
# tests/test_api/test_members.py
import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

def test_list_members():
    response = client.get("/members/?page=1&page_size=10")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
```

### 5. **Add Configuration Management**

**Create config.py:**
```python
# config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "sqlite:///data/parliament.db"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    log_level: str = "INFO"

    # Scraper settings
    rate_limit_seconds: float = 1.0
    max_retries: int = 3

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
```

**Usage:**
```python
from config import settings

DATABASE_URL = settings.database_url
```

### 6. **Add Logging Configuration**

**Create logging_config.py:**
```python
import logging
import sys
from pathlib import Path

def setup_logging(name: str, log_dir: Path = Path("logs")):
    """Set up structured logging"""
    log_dir.mkdir(exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)

    # File handler
    file_handler = logging.FileHandler(log_dir / f"{name}.log")
    file_handler.setLevel(logging.DEBUG)

    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger
```

### 7. **Add Database Migrations**

**Use Alembic for schema migrations:**
```bash
# Install alembic
pip install alembic

# Initialize alembic
alembic init migrations

# Create migration
alembic revision --autogenerate -m "Refactor vote schema"

# Apply migration
alembic upgrade head
```

---

## Priority Action Items

### Immediate (Do Now)

1. ✅ **Delete old requirements.txt** - Use pyproject.toml instead
2. ✅ **Fix API models to match database schema** - Update Pydantic models
3. ✅ **Document actual database schema** - Create clear schema documentation
4. ✅ **Test API endpoints** - Ensure they work with current schema

### Short Term (This Week)

5. **Refactor database schema** - Implement clean vote table design
6. **Add configuration management** - Create config.py with settings
7. **Add basic tests** - Test critical API endpoints
8. **Create SETUP.md** - Document installation and usage

### Medium Term (This Month)

9. **Add Alembic migrations** - Proper database versioning
10. **Improve error handling** - Better API error responses
11. **Add API authentication** - Secure the API if needed
12. **Performance optimization** - Add caching, optimize queries

---

## Conclusion

The project has a solid foundation with modern tooling (pyproject.toml), production-grade scrapers, and a well-structured API. The main issues are:

1. **Schema mismatch** between database and API models
2. **Unclear vote table design** (two tables with overlapping purposes)
3. **Missing documentation** and setup guides

By addressing these issues and implementing the recommended improvements, the project will be:
- **Easy to set up** - Clear installation instructions
- **Easy to maintain** - Proper testing, migrations, configuration
- **Easy to understand** - Clear schema, good documentation
- **Professional** - Modern tooling, best practices

All tools and configurations are already in place in pyproject.toml - just need to run `pip install -e ".[dev]"` to get started!
