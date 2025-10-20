# Development Workflow

## Overview

This document provides guidance on the day-to-day development workflow, testing strategies, deployment procedures, and maintenance tasks for the Parly Parliamentary Data API.

---

## Development Environment Setup

### Initial Setup

1. **Clone the Repository:**
   ```powershell
   git clone <repository-url>
   cd Parly
   ```

2. **Create Virtual Environment:**
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

3. **Install Dependencies:**
   ```powershell
   pip install -e ".[dev]"
   ```

4. **Verify Installation:**
   ```powershell
   python -c "import fastapi, sqlalchemy, requests; print('Setup complete')"
   ```

### Daily Workflow

1. **Activate Environment:**
   ```powershell
   cd C:\Users\solastic\prj\Parly
   .\venv\Scripts\Activate.ps1
   ```

2. **Check Current Location:**
   ```powershell
   pwd
   ```
   Should output: `C:\Users\solastic\prj\Parly`

3. **Pull Latest Changes:**
   ```powershell
   git pull origin main
   ```

4. **Run Tests (before making changes):**
   ```powershell
   pytest tests/ -v
   ```

---

## Testing Strategy

### Test Structure

```
tests/
├── __init__.py
├── test_api.py           # API endpoint tests
├── test_scrapers.py      # Scraping logic tests
├── test_database.py      # Database operations tests
└── fixtures/             # Test data samples
    ├── sample_member.json
    ├── sample_votes.xml
    └── sample_bills.xml
```

### Running Tests

**Run All Tests:**
```powershell
pytest tests/ -v
```

**Run Specific Test File:**
```powershell
pytest tests/test_api.py -v
```

**Run with Coverage:**
```powershell
pytest tests/ --cov=api --cov=scripts --cov-report=html
```

**View Coverage Report:**
```powershell
start htmlcov/index.html
```

### Writing Tests

**API Test Example:**
```python
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

def test_get_member_not_found():
    response = client.get("/api/members/999999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()
```

**Scraper Test Example:**
```python
import pytest
from scripts.extraction.member_id_scraper import MemberIdScraper

def test_parse_member_link():
    scraper = MemberIdScraper()
    # Test with known URL pattern
    link = "/Members/en/ziad-aboultaif-89156"
    # Assert parsing logic works correctly
```

### Test Database

For tests that require database access:

1. **Use a Separate Test Database:**
   ```python
   # In tests/conftest.py
   import pytest
   from sqlalchemy import create_engine
   from db_setup.create_database import Base, Session
   
   @pytest.fixture(scope="function")
   def test_db():
       engine = create_engine("sqlite:///:memory:")
       Base.metadata.create_all(engine)
       session = Session(bind=engine)
       yield session
       session.close()
   ```

2. **Use Test Fixtures:**
   ```python
   def test_insert_member(test_db):
       member = Member(
           member_id=12345,
           name="Test Member",
           party="Test Party"
       )
       test_db.add(member)
       test_db.commit()
       
       assert test_db.query(Member).count() == 1
   ```

---

## Code Quality

### Linting and Formatting

**Format Code with Black:**
```powershell
black api/ scripts/ db_setup/ --line-length 100
```

**Lint with Ruff:**
```powershell
ruff check api/ scripts/ db_setup/
```

**Type Checking (Optional):**
```powershell
pip install mypy
mypy api/ scripts/ db_setup/ --ignore-missing-imports
```

### Code Style Guidelines

Follow these principles (as per user preferences):

1. **Functional Programming First:** Prefer pure functions over classes when possible
2. **Type Annotations:** Always include type hints for function parameters and returns
3. **Minimal Changes:** Only modify what's necessary for the task
4. **KISS Principle:** Keep solutions simple
5. **DRY Principle:** Extract reusable components
6. **No Excessive Logging:** Only log errors and critical information

**Example:**
```python
# Good: Typed, functional, clear
def parse_date(date_string: str) -> date | None:
    """Parse date string to date object."""
    if not date_string:
        return None
    try:
        return datetime.strptime(date_string, '%Y-%m-%d').date()
    except ValueError:
        return None

# Avoid: Class for simple function, no types
class DateParser:
    @staticmethod
    def parse(s):
        # implementation
        pass
```

---

## Data Pipeline Management

### Running Individual Scrapers

**Scrape Member IDs:**
```powershell
python scripts/extraction/member_id_scraper.py
```

**Scrape Roles:**
```powershell
python scripts/extraction/scrape_roles.py
```

**Scrape Votes:**
```powershell
python scripts/extraction/fetch_votes.py
```

**Scrape Bills:**
```powershell
python scripts/extraction/fetch_bills.py
```

**Scrape Bill Progress:**
```powershell
python scripts/extraction/fetch_bill_progress.py
```

### Running the Full Pipeline

**Execute Complete Data Refresh:**
```powershell
python run_pipeline.py
```

**Expected Duration:** ~40-60 minutes

**Monitoring Progress:**
The pipeline script outputs progress for each step. Watch for:
- ✓ markers for successful steps
- ✗ markers for failed steps
- Error messages with details

### Scheduled Updates

**Recommended Schedule:**

| Data Type | Frequency | Rationale |
|-----------|-----------|-----------|
| Members | Monthly | List changes infrequently |
| Roles | Weekly | Committee assignments change |
| Votes | Daily | During parliamentary sessions |
| Bills | Weekly | Bill progress updates |

**Windows Task Scheduler Setup:**

1. **Create a batch script `scripts/scheduled_update.bat`:**
   ```batch
   @echo off
   cd C:\Users\solastic\prj\Parly
   call venv\Scripts\activate.bat
   python scripts/extraction/fetch_votes.py
   python scripts/extraction/fetch_bills.py
   python scripts/extraction/fetch_bill_progress.py
   ```

2. **Schedule with Task Scheduler:**
   - Open Task Scheduler
   - Create Basic Task
   - Name: "Parly Daily Update"
   - Trigger: Daily at 2:00 AM
   - Action: Start a program
   - Program: `C:\Users\solastic\prj\Parly\scripts\scheduled_update.bat`

---

## API Development Workflow

### Running the Development Server

**Start with Auto-Reload:**
```powershell
uvicorn api.main:app --reload --host 127.0.0.1 --port 8000
```

**Access API Documentation:**
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Adding a New Endpoint

1. **Define the endpoint in the appropriate route file:**
   ```python
   # In api/routes/members.py
   
   @router.get("/{member_id}/committees")
   def get_member_committees(member_id: int, db: Session = Depends(get_db)):
       """Get all committee memberships for a member."""
       # Implementation
       pass
   ```

2. **Create Pydantic model if needed:**
   ```python
   # In api/models.py
   
   class CommitteeBase(BaseModel):
       committee_name: str
       role: str
       from_date: date
       to_date: Optional[date] = None
   ```

3. **Test the endpoint:**
   ```python
   # In tests/test_api.py
   
   def test_get_member_committees():
       response = client.get("/api/members/89156/committees")
       assert response.status_code == 200
   ```

4. **Verify in Swagger UI:**
   - Navigate to `http://localhost:8000/docs`
   - Find the new endpoint
   - Click "Try it out"
   - Test with sample data

### Making Database Schema Changes

**Important:** Schema changes require migration strategy.

1. **Modify schema in `db_setup/create_database.py`**

2. **For development (destructive):**
   ```powershell
   # Backup existing data
   copy data\parliament.db data\parliament_backup.db
   
   # Recreate database
   python db_setup/create_database.py
   
   # Re-run pipeline
   python run_pipeline.py
   ```

3. **For production (use Alembic - future enhancement):**
   - Install Alembic: `pip install alembic`
   - Initialize: `alembic init alembic`
   - Create migration: `alembic revision --autogenerate -m "description"`
   - Apply migration: `alembic upgrade head`

---

## Git Workflow

### Branch Strategy

**Main Branch:** `main`
- Always deployable
- Protected branch
- Requires pull request for changes

**Feature Branches:** `feature/description`
- For new features
- Branch from `main`
- Merge back via pull request

**Bugfix Branches:** `bugfix/description`
- For bug fixes
- Branch from `main`
- Merge back via pull request

### Commit Message Format

```
<type>: <short description>

<detailed description if needed>

<reference to issue if applicable>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Maintenance tasks

**Examples:**
```
feat: Add endpoint for committee memberships

Implements GET /api/members/{id}/committees endpoint
with filtering by parliament number.

Closes #42
```

```
fix: Correct date parsing for election candidate roles

The election candidate role uses 'date' field instead of
'start_date', causing parsing errors.
```

### Working with Git

**Create Feature Branch:**
```powershell
git checkout -b feature/new-endpoint
```

**Stage and Commit Changes:**
```powershell
git add api/routes/members.py
git commit -m "feat: Add committee memberships endpoint"
```

**Push to Remote:**
```powershell
git push origin feature/new-endpoint
```

**Update Branch with Latest Main:**
```powershell
git checkout main
git pull origin main
git checkout feature/new-endpoint
git merge main
```

### Pull Request Process

1. **Create PR on GitHub/GitLab**
2. **Ensure Tests Pass**
3. **Request Review**
4. **Address Feedback**
5. **Merge to Main**
6. **Delete Feature Branch**

---

## Deployment

### Local Development Deployment

Already covered above with `uvicorn --reload`.

### Production Deployment (Linux Server)

**Prerequisites:**
- Ubuntu 22.04 LTS server
- Python 3.10+
- Nginx
- Systemd

**Step 1: Server Setup**

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python
sudo apt install python3.10 python3.10-venv python3-pip -y

# Install Nginx
sudo apt install nginx -y

# Create app user
sudo useradd -m -s /bin/bash parly
sudo su - parly
```

**Step 2: Deploy Application**

```bash
# Clone repository
git clone <repo-url> /home/parly/parly
cd /home/parly/parly

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -e .

# Run initial data pipeline
python run_pipeline.py
```

**Step 3: Create Systemd Service**

```bash
# As root, create service file
sudo nano /etc/systemd/system/parly-api.service
```

**Service File Content:**
```ini
[Unit]
Description=Parly Parliamentary Data API
After=network.target

[Service]
Type=simple
User=parly
WorkingDirectory=/home/parly/parly
Environment="PATH=/home/parly/parly/venv/bin"
ExecStart=/home/parly/parly/venv/bin/uvicorn api.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Enable and Start Service:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable parly-api
sudo systemctl start parly-api
sudo systemctl status parly-api
```

**Step 4: Configure Nginx**

```bash
sudo nano /etc/nginx/sites-available/parly
```

**Nginx Configuration:**
```nginx
server {
    listen 80;
    server_name parly.example.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /docs {
        proxy_pass http://127.0.0.1:8000/docs;
        proxy_set_header Host $host;
    }

    location /redoc {
        proxy_pass http://127.0.0.1:8000/redoc;
        proxy_set_header Host $host;
    }
}
```

**Enable Site:**
```bash
sudo ln -s /etc/nginx/sites-available/parly /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

**Step 5: Set Up SSL (Optional but Recommended)**

```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d parly.example.com
```

---

## Monitoring and Maintenance

### Logging

**Application Logs:**
- **Location:** stdout (captured by systemd in production)
- **View Logs:** 
  ```bash
  sudo journalctl -u parly-api -f
  ```

**Nginx Logs:**
- **Access Log:** `/var/log/nginx/access.log`
- **Error Log:** `/var/log/nginx/error.log`

### Database Maintenance

**Backup Database:**
```powershell
# Windows
copy data\parliament.db data\backups\parliament_$(Get-Date -Format 'yyyyMMdd').db

# Linux
cp data/parliament.db data/backups/parliament_$(date +%Y%m%d).db
```

**Check Database Size:**
```powershell
# Windows
(Get-Item data\parliament.db).Length / 1MB

# Linux
du -h data/parliament.db
```

**Optimize Database (SQLite VACUUM):**
```python
import sqlite3
conn = sqlite3.connect('data/parliament.db')
conn.execute('VACUUM')
conn.close()
```

### Performance Monitoring

**Check API Response Times:**
```powershell
Measure-Command { Invoke-WebRequest http://localhost:8000/api/members }
```

**Monitor Resource Usage (Linux):**
```bash
# CPU and Memory
top -p $(pgrep -f uvicorn)

# Disk I/O
iostat -x 1
```

### Health Checks

**API Health Check:**
```powershell
curl http://localhost:8000/health
```

**Expected Response:**
```json
{"status": "healthy"}
```

**Database Connectivity Check:**
```powershell
python -c "from db_setup.create_database import Session; s = Session(); print(f'Members: {s.query(__import__('db_setup.create_database').create_database.Member).count()}'); s.close()"
```

---

## Troubleshooting

### API Won't Start

**Symptom:** `uvicorn api.main:app` fails

**Debugging Steps:**
1. Check if port 8000 is in use:
   ```powershell
   netstat -ano | findstr :8000
   ```

2. Verify imports work:
   ```powershell
   python -c "from api.main import app; print('OK')"
   ```

3. Check for missing dependencies:
   ```powershell
   pip list
   ```

### Slow API Responses

**Symptom:** Requests take >1 second

**Solutions:**
1. **Add Database Indexes:**
   ```python
   # In db_setup/create_database.py
   from sqlalchemy import Index
   
   Index('idx_votes_member_date', Vote.member_id, Vote.vote_date)
   Index('idx_roles_member_type', Role.member_id, Role.role_type)
   ```

2. **Reduce Pagination Size:**
   Change default `per_page` from 50 to 25

3. **Enable Query Caching (future enhancement)**

### Scraper Failures

**Symptom:** Scraper script exits with errors

**Common Causes:**
1. **Network Issues:** Website is down or unreachable
   - **Solution:** Retry later, check internet connection

2. **HTML/XML Structure Changed:** Parsing logic breaks
   - **Solution:** Inspect the actual HTML/XML, update selectors

3. **Rate Limiting:** Too many requests too quickly
   - **Solution:** Increase sleep duration between requests

**Debug Individual Requests:**
```python
import requests
url = "https://www.ourcommons.ca/members/en/ziad-aboultaif(89156)/roles"
response = requests.get(url)
print(response.status_code)
print(response.text[:500])
```

---

## Data Quality Checks

### Verification Scripts

**Check for Missing Data:**
```python
from db_setup.create_database import Session, Member, Role, Vote

session = Session()

# Members without roles
members_no_roles = session.query(Member).filter(
    ~Member.roles.any()
).all()

print(f"Members without roles: {len(members_no_roles)}")

# Members without votes
members_no_votes = session.query(Member).filter(
    ~Member.votes.any()
).all()

print(f"Members without votes: {len(members_no_votes)}")

session.close()
```

**Check Data Consistency:**
```python
# Verify all foreign keys are valid
from sqlalchemy import func

invalid_votes = session.query(Vote).filter(
    ~Vote.member_id.in_(session.query(Member.member_id))
).count()

print(f"Invalid vote records: {invalid_votes}")
```

---

## Best Practices

### 1. Always Use Virtual Environment
Never install packages globally. Always activate the virtual environment.

### 2. Test Before Committing
Run tests before pushing changes:
```powershell
pytest tests/ -v && git push
```

### 3. Backup Before Major Changes
Before schema changes or major refactoring:
```powershell
copy data\parliament.db data\backups\parliament_before_change.db
```

### 4. Document as You Go
Update relevant documentation when making changes.

### 5. Follow Type Annotations
Always include type hints for maintainability.

### 6. Keep Dependencies Updated
Regularly update dependencies for security:
```powershell
pip list --outdated
pip install --upgrade <package>
```

### 7. Monitor Logs in Production
Regularly review logs for errors or warnings.

---

## Quick Reference

**Start Development:**
```powershell
cd C:\Users\solastic\prj\Parly
.\venv\Scripts\Activate.ps1
uvicorn api.main:app --reload
```

**Run Tests:**
```powershell
pytest tests/ -v
```

**Full Data Refresh:**
```powershell
python run_pipeline.py
```

**Update Single Data Type:**
```powershell
python scripts/extraction/fetch_votes.py
```

**Check Database Stats:**
```powershell
python scripts/db_check.py
```

**Format Code:**
```powershell
black api/ scripts/ db_setup/
```

---

## Resources

- **FastAPI Documentation:** https://fastapi.tiangolo.com/
- **SQLAlchemy Documentation:** https://docs.sqlalchemy.org/
- **Pydantic Documentation:** https://docs.pydantic.dev/
- **Pytest Documentation:** https://docs.pytest.org/

---

## Support

For issues or questions:
1. Check this documentation first
2. Review the TECHNICAL_SPECIFICATION.md
3. Search existing GitHub issues
4. Create a new issue with:
   - Clear description of the problem
   - Steps to reproduce
   - Expected vs actual behavior
   - Relevant logs or error messages

