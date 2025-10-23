# System Architecture

## Overview

This document describes the system architecture of the Parly Parliamentary Data API, including component interactions, data flow, and design decisions.

---

## High-Level Architecture

The Parly system follows a classic three-tier architecture:

```
┌─────────────────────────────────────────────────────────────┐
│                       CLIENT LAYER                           │
│  (Web Browsers, CLI Tools, Other Applications, LLMs)        │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTP/REST
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                    APPLICATION LAYER                         │
│                    (FastAPI Server)                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Routes     │  │   Models     │  │  Database    │     │
│  │  (Endpoints) │  │  (Pydantic)  │  │  Connection  │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└────────────────────┬────────────────────────────────────────┘
                     │ SQLAlchemy ORM
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                      DATA LAYER                              │
│                   (SQLite Database)                          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │
│  │ members  │ │  roles   │ │  votes   │ │  bills   │      │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘      │
└────────────────────┬────────────────────────────────────────┘
                     ▲
                     │ SQLAlchemy ORM
┌────────────────────┴────────────────────────────────────────┐
│                  EXTRACTION LAYER                            │
│                  (Scraping Scripts)                          │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐             │
│  │  Member    │ │   Roles    │ │   Votes    │             │
│  │  Scraper   │ │  Scraper   │ │  Scraper   │   ...       │
│  └────────────┘ └────────────┘ └────────────┘             │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTP/HTTPS
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                    EXTERNAL SOURCES                          │
│         (ourcommons.ca, parl.ca)                            │
└─────────────────────────────────────────────────────────────┘
```

---

## Component Details

### 1. Extraction Layer

**Purpose:** Automate the collection of parliamentary data from external websites.

**Components:**

#### A. Scraping Scripts (`scripts/extraction/`)
Individual Python scripts responsible for extracting specific data types:

- **`member_id_scraper.py`**
  - **Responsibility:** Scrape the list of all MPs with their IDs
  - **Input:** None (fetches from fixed URL)
  - **Output:** `data/member_ids.csv`
  - **Dependencies:** `requests`, `beautifulsoup4`, `pandas`

- **`scrape_roles.py`**
  - **Responsibility:** Scrape detailed role information for each member
  - **Input:** `data/member_ids.csv`
  - **Output:** `data/member_roles.json`
  - **Dependencies:** `requests`, `beautifulsoup4`

- **`fetch_votes.py`** (to be completed)
  - **Responsibility:** Scrape voting records for each member
  - **Input:** `data/member_ids.csv`
  - **Output:** Direct database insertion
  - **Dependencies:** `requests`, `xml.etree.ElementTree`

- **`fetch_bills.py`** (to be created)
  - **Responsibility:** Scrape bills sponsored by each member
  - **Input:** `data/member_ids.csv`
  - **Output:** Direct database insertion
  - **Dependencies:** `requests`, `xml.etree.ElementTree`

- **`fetch_bill_progress.py`** (to be created)
  - **Responsibility:** Scrape legislative progress for each bill
  - **Input:** Bills from database
  - **Output:** Direct database insertion
  - **Dependencies:** `requests`, `json`

**Design Principles:**
- **Single Responsibility:** Each script handles one data type
- **Idempotency:** Scripts can be run multiple times safely
- **Error Resilience:** Individual failures don't stop the entire process
- **Rate Limiting:** Built-in delays to respect server resources

#### B. Data Insertion Scripts (`db_setup/`)

- **`create_database.py`**
  - **Responsibility:** Define database schema and initialize database
  - **Input:** None
  - **Output:** `data/parliament.db` (empty database with tables)
  - **Dependencies:** `sqlalchemy`

- **`insert_roles_db.py`**
  - **Responsibility:** Parse scraped roles JSON and insert into database
  - **Input:** `data/member_roles.json`
  - **Output:** Populated `members` and `roles` tables
  - **Dependencies:** `sqlalchemy`, `json`

- **`insert_votes_db.py`** (to be created)
  - **Responsibility:** Insert votes data into database
  - **Input:** Votes data (from scraper)
  - **Output:** Populated `votes` table

- **`insert_bills_db.py`** (to be created)
  - **Responsibility:** Insert bills and progress data into database
  - **Input:** Bills data (from scraper)
  - **Output:** Populated `bills` and `bill_progress` tables

---

### 2. Data Layer

**Purpose:** Persistent storage of all parliamentary data in a structured, queryable format.

**Technology:** SQLite 3

**Why SQLite?**
- Self-contained (single file)
- No server setup required
- Sufficient for read-heavy workloads
- Easy to backup and distribute
- Can handle millions of records efficiently

**Database File Location:** `data/parliament.db`

**Schema Management:** SQLAlchemy ORM with declarative base

**Key Relationships:**
```
members (1) ───< (N) roles
members (1) ───< (N) votes
members (1) ───< (N) bills [as sponsor]
bills (1) ───< (N) bill_progress
members (1) ───< (N) parliamentary_associations
```

**Indexing Strategy:**
- Primary keys: Auto-indexed
- Foreign keys: Create indexes for `member_id` in all related tables
- Query-heavy columns: Create indexes on `vote_date`, `parliament_number`, `party`

---

### 3. Application Layer (API)

**Purpose:** Expose parliamentary data through a clean, RESTful API.

**Technology:** FastAPI (Python web framework)

**Why FastAPI?**
- Automatic API documentation (Swagger/OpenAPI)
- Fast performance (async support)
- Type safety with Pydantic
- Modern Python (3.10+)
- Excellent developer experience

#### Directory Structure:
```
api/
├── main.py              # Application entry point
├── database.py          # Database connection and session management
├── models.py            # Pydantic models for request/response
├── dependencies.py      # Shared dependencies (e.g., get_db)
└── routes/
    ├── __init__.py
    ├── members.py       # Member-related endpoints
    ├── votes.py         # Vote-related endpoints
    ├── bills.py         # Bill-related endpoints
    └── statistics.py    # Aggregate statistics endpoints
```

#### Component Responsibilities:

**`main.py`:**
- Initialize FastAPI application
- Register all route modules
- Configure CORS middleware
- Set up error handlers
- Configure API metadata

**`database.py`:**
- Create SQLAlchemy engine
- Define session factory
- Provide dependency injection for database sessions

**`models.py`:**
- Define Pydantic models for all API responses
- Implement data validation
- Provide serialization logic

**`routes/`:**
- Implement endpoint logic
- Handle query parameters
- Perform database queries
- Return formatted responses

#### Request Flow:
```
1. Client sends HTTP request
   ↓
2. FastAPI routes request to appropriate handler
   ↓
3. Handler validates query parameters (Pydantic)
   ↓
4. Handler obtains database session (dependency injection)
   ↓
5. Handler executes SQLAlchemy query
   ↓
6. Handler serializes result using Pydantic models
   ↓
7. FastAPI returns JSON response
```

---

### 4. Client Layer

**Purpose:** Consume the API for various use cases.

**Potential Clients:**
- **Web Applications:** Frontend dashboards for data visualization
- **CLI Tools:** Command-line interfaces for querying data
- **LLM Agents:** AI systems using the API for analysis
- **Data Scientists:** Research and analysis tools
- **Other Services:** Integration with other government data systems

**API Contract:**
- All responses in JSON format
- RESTful URL structure
- Standard HTTP status codes
- Pagination for large result sets
- Filtering via query parameters

---

## Data Flow

### Initial Data Population Flow

```
1. Run member_id_scraper.py
   └─> Scrapes ourcommons.ca
   └─> Outputs: member_ids.csv

2. Run scrape_roles.py
   └─> Reads: member_ids.csv
   └─> Scrapes ourcommons.ca (338 requests)
   └─> Outputs: member_roles.json

3. Run create_database.py
   └─> Creates: parliament.db with empty tables

4. Run insert_roles_db.py
   └─> Reads: member_roles.json
   └─> Inserts into: members and roles tables

5. Run fetch_votes.py (for all members)
   └─> Reads: member_ids.csv
   └─> Scrapes ourcommons.ca (338 requests)
   └─> Inserts into: votes table

6. Run fetch_bills.py (for all members)
   └─> Reads: member_ids.csv
   └─> Scrapes parl.ca (338 requests)
   └─> Inserts into: bills table

7. Run fetch_bill_progress.py (for all bills)
   └─> Reads: bills from database
   └─> Scrapes parl.ca (N requests, N = number of bills)
   └─> Inserts into: bill_progress table

8. Start API server
   └─> Reads: parliament.db
   └─> Serves: HTTP API
```

### Runtime Query Flow

```
1. Client → HTTP GET /api/members/89156
                ↓
2. FastAPI → Route Handler (routes/members.py)
                ↓
3. Handler → Validate parameters
                ↓
4. Handler → Query database via SQLAlchemy
                ↓
5. SQLAlchemy → Execute SELECT on parliament.db
                ↓
6. Database → Return rows
                ↓
7. Handler → Serialize to Pydantic model
                ↓
8. FastAPI → Return JSON response
                ↓
9. Client ← Receive member data
```

---

## Design Decisions

### 1. Why Separate Scraping from API?

**Decision:** Keep data extraction scripts separate from the API server.

**Rationale:**
- **Separation of Concerns:** Scraping is a batch operation; API is a request-response service
- **Different Schedules:** Scraping runs periodically; API runs continuously
- **Error Isolation:** Scraping failures don't affect API availability
- **Maintainability:** Easier to update scraping logic without touching API

**Alternative Considered:** Combined system with background tasks
**Why Rejected:** Adds complexity, makes debugging harder, couples unrelated concerns

---

### 2. Why SQLite Instead of PostgreSQL?

**Decision:** Use SQLite for the database.

**Rationale:**
- **Simplicity:** No server setup, single file
- **Portability:** Easy to backup, share, and deploy
- **Sufficient Performance:** Read-heavy workload suits SQLite well
- **Low Maintenance:** No configuration, no tuning needed
- **Project Scope:** Not expecting millions of concurrent users

**When to Migrate:** If concurrent write operations become frequent or database size exceeds 100GB

---

### 3. Why FastAPI Instead of Flask?

**Decision:** Use FastAPI as the web framework.

**Rationale:**
- **Automatic Documentation:** Built-in Swagger UI
- **Type Safety:** Pydantic integration catches errors early
- **Performance:** Faster than Flask for async operations
- **Modern:** Better async/await support
- **Developer Experience:** Less boilerplate code

**Alternative Considered:** Flask
**Why Rejected:** Requires more manual setup for documentation and validation

---

### 4. Why JSON for Intermediate Storage?

**Decision:** Use JSON files for scraped data before database insertion (for roles).

**Rationale:**
- **Debugging:** Easy to inspect scraped data
- **Recovery:** Can re-insert data without re-scraping
- **Flexibility:** Can adjust database schema without re-scraping
- **Historical Record:** Preserves original scraped format

**Trade-off:** Extra storage space, but negligible given data size

---

### 5. Why Not Cache API Responses?

**Decision:** No response caching in Phase 1.

**Rationale:**
- **Simplicity First:** Caching adds complexity
- **Data Freshness:** Database is the source of truth
- **Read Performance:** SQLite is fast enough for expected load
- **YAGNI Principle:** Add caching only when needed

**When to Add:** If response times exceed 500ms or query volume causes bottlenecks

---

## Scalability Considerations

### Current Limitations:
- **Single-threaded SQLite:** Handles ~50,000 reads/second (sufficient)
- **No Load Balancing:** Single API server instance
- **No CDN:** All requests hit the server directly

### Future Scaling Paths:

**If Read Load Increases:**
1. Add read replicas (SQLite supports multiple readers)
2. Implement response caching (Redis)
3. Add CDN for static responses

**If Write Load Increases:**
1. Migrate to PostgreSQL
2. Implement write batching
3. Use connection pooling

**If API Becomes Critical Infrastructure:**
1. Add horizontal scaling (multiple API instances)
2. Implement load balancing
3. Add monitoring and alerting

---

## Security Architecture

### Current Security Measures:
1. **Input Validation:** All inputs validated via Pydantic
2. **SQL Injection Prevention:** SQLAlchemy ORM (no raw SQL)
3. **Rate Limiting:** Planned implementation (100 req/min per IP)

### Future Security Enhancements:
1. **Authentication:** API keys for tracked usage
2. **HTTPS:** SSL/TLS for encrypted communication
3. **CORS Configuration:** Restrict allowed origins
4. **Audit Logging:** Track all API access

---

## Error Handling Strategy

### Scraping Layer:
- **Network Errors:** Retry with exponential backoff (3 attempts)
- **Parsing Errors:** Log and continue (skip problematic records)
- **Data Validation Errors:** Log warning, insert with NULL values

### API Layer:
- **Invalid Parameters:** 400 Bad Request with error details
- **Resource Not Found:** 404 Not Found
- **Database Errors:** 500 Internal Server Error (log full stack trace)
- **Rate Limit Exceeded:** 429 Too Many Requests

### Logging:
- **Level:** INFO for normal operations, ERROR for failures
- **Format:** JSON structured logs for easy parsing
- **Destination:** Console (stdout) and file (`logs/parly.log`)

---

## Testing Strategy

### Unit Tests:
- **Target:** Individual functions (parsing, validation)
- **Framework:** pytest
- **Coverage Goal:** 80%+

### Integration Tests:
- **Target:** Database operations, API endpoints
- **Framework:** pytest with test database
- **Approach:** Test each endpoint with various inputs

### End-to-End Tests:
- **Target:** Full data pipeline (scrape → insert → query)
- **Framework:** pytest with fixtures
- **Approach:** Use sample data from `data/raw/`

---

## Deployment Architecture

### Development Environment:
```
Local Machine
├── Python 3.10+ virtual environment
├── SQLite database (data/parliament.db)
├── Uvicorn development server
└── No external dependencies
```

### Production Environment (Recommended):
```
Linux Server (Ubuntu 22.04 LTS)
├── Python 3.10+ virtual environment
├── SQLite database (data/parliament.db)
├── Uvicorn with Gunicorn (process manager)
├── Nginx (reverse proxy)
├── Systemd service (auto-restart)
└── Cron jobs (scheduled scraping)
```

---

## Future Architecture: Analysis Layer

**Note:** This is not part of Phase 1 but represents the long-term vision.

```
┌────────────────────────────────────────┐
│        LLM Analysis Service            │
│  ┌──────────────┐  ┌──────────────┐   │
│  │  Sentiment   │  │   Pattern    │   │
│  │  Analysis    │  │  Detection   │   │
│  └──────────────┘  └──────────────┘   │
└───────────┬────────────────────────────┘
            │ Consumes API
            ▼
┌────────────────────────────────────────┐
│      Parly Data API (This Project)     │
└────────────────────────────────────────┘
```

**Decoupling Strategy:**
- Analysis layer is a separate service
- Consumes data via API (no direct database access)
- Can be developed independently
- Allows for multiple analysis implementations

---

## Monitoring and Observability

### Metrics to Track (Future):
- **API Performance:** Request latency, error rates
- **Database Performance:** Query execution time, connection pool usage
- **Scraping Health:** Success rates, data freshness
- **Resource Usage:** CPU, memory, disk I/O

### Tools (Future):
- **Logging:** Python logging module → JSON format
- **Metrics:** Prometheus
- **Visualization:** Grafana
- **Alerting:** Email/Slack notifications

---

## Summary

The Parly architecture is designed with simplicity, maintainability, and modularity as core principles. The separation of concerns between extraction, storage, and API layers allows for independent development and deployment of each component. The choice of SQLite and FastAPI provides a balance between simplicity and functionality, making the system accessible to developers while remaining robust enough for production use.

