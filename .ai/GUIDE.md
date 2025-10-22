# Work Guide

Reference for what to build/fix/improve in the Parly Parliamentary Data API project.

---

## Project Goal

Build an AI-powered parliamentary intelligence system for Canadian parliamentary data analysis.

---

## Main Documentation

Parly has comprehensive documentation in the `docs/` directory:

- **README.md** - Project overview and quick start
- **PROGRESS_LOG.md** - Current work artifacts and recent changes (session-specific)
- **docs/ROADMAP.md** - Strategic 4-phase development roadmap
- **docs/IMPLEMENTATION_GUIDE.md** - Step-by-step implementation guide (8 phases)
- **docs/ARCHITECTURE.md** - System architecture and design decisions
- **docs/TECHNICAL_SPECIFICATION.md** - Database schema and API specifications
- **docs/DATABASE_SCHEMA.md** - Current database structure
- **docs/DATA_SOURCES.md** - Data source URLs and extraction strategies
- **docs/DEVELOPMENT_WORKFLOW.md** - Development practices and workflows
- **docs/SCRAPING_BEST_PRACTICES.md** - Production-grade scraping patterns

---

## Task List

Current focus: **Phase 1 of Roadmap** - Structured Data Foundation & Early AI Integration

### Phase 1.2: Structured Data Audit & Expansion (COMPLETED)

1. **Data Source Inventory** (1-2 days)
   - [x] Audit current data sources and completeness
   - [x] Identify missing structured data sources
   - [x] Document data refresh/update processes
   - [x] Historical member data imported (1993-2025, 1,246 members)

2. **Data Quality & Completeness** (2-3 days)
   - [ ] Verify data integrity across all tables
   - [ ] Add data validation checks
   - [ ] Document data gaps and completeness metrics

### Phase 1.3: Basic Analytics Layer

3. **Core Analytics API** (3-5 days)
   - [ ] Member activity statistics endpoints
   - [ ] Bill progression metrics endpoints
   - [ ] Voting pattern summaries
   - [ ] Party/region breakdowns

4. **Data Visualization Endpoints** (2-3 days)
   - [ ] Chart data generation
   - [ ] Timeline data for bills/votes
   - [ ] Statistical aggregations

### Phase 1.4: Early LLM Integration

5. **LLM Query Interface** (1 week)
   - [ ] Natural language queries on structured data
   - [ ] Basic insight generation from existing data
   - [ ] Pattern recognition and correlation analysis

6. **LLM-Powered Reporting** (3-5 days)
   - [ ] Automated report generation
   - [ ] Data-driven insights and summaries
   - [ ] Comparative analysis capabilities

### Deferred Tasks

- Vote schema refactoring (works fine, revisit if performance issues arise)
- Database optimization (current performance acceptable)

---

## Key Files

### Configuration & Setup
- `pyproject.toml` - Modern Python dependency management
- `config.py` - Centralized configuration (database, API, scraping settings)
- `.env.example` - Environment variable template

### API Layer (FastAPI)
- `api/main.py` - FastAPI application entry point
- `api/database.py` - Database connection and session management
- `api/models.py` - Pydantic models for request/response validation
- `api/routes/members.py` - Member endpoints
- `api/routes/votes.py` - Vote endpoints
- `api/routes/bills.py` - Bill endpoints

### Database
- `db_setup/create_database.py` - SQLAlchemy schema definitions
- `data/parliament.db` - SQLite database (1,701 members, 14K+ roles, 105K+ votes, 1K+ bills)

### Data Extraction (Production-Ready Scrapers)
- `scripts/extraction/votes/fetch_votes.py` - Vote scraping with retry logic
- `scripts/extraction/bills/fetch_bills.py` - Bill metadata extraction
- `scripts/extraction/bills/fetch_bill_progress.py` - Legislative progress tracking
- `scripts/extraction/members/update_members_simple.py` - **Ongoing member updates** (automation)
- `scripts/extraction/scraper_template.py` - Template for future scrapers

**Note**: Historical backfill scripts have been deleted. Only `update_members_simple.py` is needed for ongoing member/role updates.

### Testing
- `tests/test_api.py` - Comprehensive API test suite (25 tests, all passing)

---

## Build/Run Commands

```bash
# Install project with all dependencies
pip install -e ".[dev]"

# Start API server (with auto-reload)
uvicorn api.main:app --reload --port 8000

# Access interactive API documentation
# Open http://localhost:8000/docs in browser

# Run all tests
pytest

# Run tests with verbose output
pytest -v

# Run specific test file
pytest tests/test_api.py

# Run scrapers to update data (production scrapers with checkpointing)
python scripts/extraction/votes/fetch_votes.py
python scripts/extraction/bills/fetch_bills.py
python scripts/extraction/bills/fetch_bill_progress.py

# Quick API health check
curl http://localhost:8000/stats
```

---

## Testing Strategy

1. **API Testing**: Run `pytest` before committing any changes
   - All 25 tests must pass
   - Tests cover all endpoints, pagination, filtering, data integrity

2. **Manual API Testing**: Start server and use interactive docs
   - Navigate to http://localhost:8000/docs
   - Test endpoints with different parameters
   - Verify response formats and data accuracy

3. **Data Validation**: After running scrapers
   - Check logs in `logs/` directory for errors
   - Verify database record counts match expectations
   - Run `curl http://localhost:8000/stats` to see counts

4. **Integration Testing**: End-to-end workflows
   - Run scraper → verify database → test API → verify response

---

## Reference Material

**Primary Documentation** (well-maintained):
- `docs/ROADMAP.md` - Development phases and strategic direction
- `docs/IMPLEMENTATION_GUIDE.md` - Detailed implementation steps
- `docs/DATABASE_SCHEMA.md` - Database table structures and relationships
- `docs/ARCHITECTURE.md` - System design and data flow

**Code Patterns**:
- Review existing scrapers for production patterns (retry, checkpointing, logging)
- API routes follow consistent structure (pagination, filtering, error handling)
- Pydantic models define strict validation rules

**External References**:
- FastAPI docs: https://fastapi.tiangolo.com
- SQLAlchemy 2.0 docs: https://docs.sqlalchemy.org
- Parliament of Canada data sources: See `docs/DATA_SOURCES.md`

---

## Success Criteria

For each task/feature:
- [ ] All tests passing (`pytest`)
- [ ] API documentation updated (docstrings in FastAPI routes)
- [ ] PROGRESS_LOG.md updated with changes
- [ ] CONTEXT.md updated with current state
- [ ] Code follows existing patterns (FastAPI routes, Pydantic models, scraper structure)
- [ ] No breaking changes to existing API endpoints (versioning if needed)

For Phase 1 completion:
- [ ] Data audit complete with documented findings
- [ ] Analytics API endpoints functional
- [ ] LLM integration working with natural language queries
- [ ] All documentation reflects new capabilities

---

## Common Patterns

### API Endpoint Structure
```python
@router.get("/endpoint", response_model=List[ResponseModel])
async def get_items(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
) -> List[ResponseModel]:
    """Endpoint description."""
    # Pagination logic
    skip = (page - 1) * page_size

    # Query with filters
    items = db.query(Model).offset(skip).limit(page_size).all()

    return items
```

### Production Scraper Structure
```python
# Retry logic with exponential backoff
for attempt in range(max_retries):
    try:
        response = session.get(url, timeout=10)
        response.raise_for_status()
        break
    except RequestException as e:
        if attempt < max_retries - 1:
            time.sleep(2 ** attempt)
            continue
        raise

# Checkpoint saving for resume capability
save_checkpoint(processed_items)

# Duplicate prevention
if exists_in_db(item_id):
    continue
```

---

## Troubleshooting

**API Issues**:
- **Server won't start**: Check if port 8000 is available: `netstat -ano | findstr :8000`
- **Tests failing**: Ensure database is populated: `ls -lh data/parliament.db`
- **Import errors**: Reinstall in development mode: `pip install -e ".[dev]"`

**Database Issues**:
- **Empty results**: Verify scrapers ran successfully, check logs in `logs/`
- **Schema errors**: Review `docs/DATABASE_SCHEMA.md` for current structure
- **Performance slow**: Database has 100K+ records, pagination is essential

**Scraper Issues**:
- **Scraper fails**: Check network connection, Parliament website may be down
- **Duplicate data**: Scrapers have built-in duplicate prevention
- **Rate limiting**: Scrapers respect politeness delays (2-5 seconds between requests)

---

**Remember**: Follow existing patterns. Keep changes focused. Test everything. Update CONTEXT.md frequently.
