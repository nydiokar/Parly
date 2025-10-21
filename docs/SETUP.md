# Parly Project Setup Guide

This guide provides step-by-step instructions for setting up and running the Parly Canadian Parliament Data API project.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Detailed Installation](#detailed-installation)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [API Usage](#api-usage)
- [Data Scraping](#data-scraping)
- [Testing](#testing)
- [Development](#development)
- [Troubleshooting](#troubleshooting)

## Prerequisites

- **Python 3.9+** (Python 3.13 recommended)
- **Git** for cloning the repository
- **Internet connection** for data scraping and dependencies

### Optional Prerequisites

- **Virtual environment tool** (venv, conda, or similar)
- **PostgreSQL** (if you want to use PostgreSQL instead of SQLite)

## Quick Start

For experienced users who want to get running quickly:

```bash
# Clone and enter the repository
git clone <repository-url>
cd Parly

# Install with all dependencies
pip install -e ".[dev]"

# Run the API server
uvicorn api.main:app --reload --port 8000

# Access the API documentation
open http://localhost:8000/docs
```

The database is pre-populated with Canadian parliamentary data, so the API will be fully functional immediately.

## Detailed Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd Parly
```

### 2. Set Up Python Environment

It's recommended to use a virtual environment:

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies

```bash
# Install core dependencies
pip install -e .

# Install development dependencies (recommended)
pip install -e ".[dev]"
```

The development dependencies include:
- `pytest` - Testing framework
- `ruff` - Code linting and formatting
- `mypy` - Type checking
- `httpx` - HTTP client for testing

### 4. Verify Installation

```bash
# Check that everything is installed correctly
python -c "import parly; print('Installation successful!')"

# Run tests to verify everything works
pytest
```

## Configuration

The application uses centralized configuration via `config.py`. You can customize settings using environment variables or a `.env` file.

### Basic Configuration

Create a `.env` file in the project root (optional):

```bash
# Copy the example configuration
cp .env.example .env
```

### Key Configuration Options

```bash
# Database
DATABASE_URL=sqlite:///data/parliament.db

# API Server
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=true  # Set to false for production

# Logging
LOG_LEVEL=INFO
LOG_FILE_ENABLED=true

# Scraper settings (if you plan to update data)
SCRAPER_RATE_LIMIT=1.0
SCRAPER_MAX_RETRIES=3
```

### Environment Variables

All configuration can be overridden with environment variables:

```bash
export API_PORT=3000
export LOG_LEVEL=DEBUG
uvicorn api.main:app --reload
```

## Running the Application

### Development Mode

```bash
# Start the API server with auto-reload
uvicorn api.main:app --reload --port 8000

# Or use the configuration settings
python api/main.py
```

### Production Mode

```bash
# Set production environment
export ENVIRONMENT=production
export API_RELOAD=false

# Run with multiple workers
uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Using Docker (Future)

Docker support will be added in a future update. For now, use the direct Python approach.

## API Usage

### Access Points

- **API Documentation**: http://localhost:8000/docs
- **Interactive API**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health
- **Root Endpoint**: http://localhost:8000/

### Key Endpoints

```bash
# Get API statistics
curl http://localhost:8000/stats

# List members with pagination
curl "http://localhost:8000/members/?page=1&page_size=10"

# Filter members by party
curl "http://localhost:8000/members/?party=Liberal"

# Get detailed member information
curl http://localhost:8000/members/1

# List votes
curl "http://localhost:8000/votes/?page=1&page_size=10"

# Get detailed vote information
curl http://localhost:8000/votes/1

# List bills
curl "http://localhost:8000/bills/?page=1&page_size=10"

# Search bills by title
curl "http://localhost:8000/bills/?search=climate"
```

### Response Format

All endpoints return JSON responses. The API uses pagination for list endpoints:

```json
{
  "total": 455,
  "page": 1,
  "page_size": 10,
  "total_pages": 46,
  "items": [...]
}
```

## Data Scraping

The project includes pre-populated data, but you can update it using the scrapers:

### Update Member Data

```bash
python scripts/extraction/members/member_id_scraper.py
python scripts/extraction/members/update_members_simple.py
```

### Update Vote Data

```bash
python scripts/extraction/votes/fetch_votes.py
```

### Update Bill Data

```bash
python scripts/extraction/bills/fetch_bills.py
python scripts/extraction/bills/fetch_bill_progress.py
```

### Scraper Configuration

Scrapers respect rate limits and include error handling. Configure scraper behavior in your `.env` file:

```bash
SCRAPER_RATE_LIMIT=1.0  # Requests per second
SCRAPER_MAX_RETRIES=3
SCRAPER_TIMEOUT=30
```

## Testing

### Run All Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_api.py

# Run with coverage
pytest --cov=api --cov-report=html
```

### Test Coverage

The test suite covers:
- All API endpoints
- Data serialization/deserialization
- Pagination and filtering
- Error handling
- Database integrity

### Continuous Integration

Tests are designed to run in CI/CD environments. All tests should pass before deployment.

## Development

### Code Quality

```bash
# Format code
ruff format .

# Lint code
ruff check .

# Type check
mypy api/ scripts/
```

### Database Migrations

The project uses Alembic for database versioning:

```bash
# Check current migration status
alembic current

# View migration history
alembic history

# Create new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head
```

### Adding New Features

1. **API Endpoints**: Add routes in `api/routes/`
2. **Models**: Update `api/models.py` for new response schemas
3. **Database**: Add models in `db_setup/create_database.py` and create migrations
4. **Tests**: Add tests in `tests/` following existing patterns

### Project Structure

```
Parly/
├── api/                    # FastAPI application
│   ├── main.py            # Main application
│   ├── database.py        # Database connection
│   ├── models.py          # Pydantic models
│   └── routes/            # API endpoints
├── config.py              # Configuration management
├── db_setup/              # Database schema
├── migrations/            # Database migrations
├── scripts/               # Data scraping scripts
├── tests/                 # Test suite
├── data/                  # Data storage
└── docs/                  # Documentation
```

## Troubleshooting

### Common Issues

#### Import Errors

```bash
# Install missing dependencies
pip install -e ".[dev]"

# Check Python version
python --version
```

#### Database Connection Issues

```bash
# Check database file exists
ls -la data/parliament.db

# Reset database (WARNING: destroys data)
rm data/parliament.db
python db_setup/create_database.py
# Then re-run scrapers to populate data
```

#### Port Already in Use

```bash
# Use different port
uvicorn api.main:app --port 3000

# Find and kill process using port 8000
lsof -ti:8000 | xargs kill -9
```

#### Scraper Rate Limiting

If scrapers are getting blocked:

```bash
# Increase delays between requests
export SCRAPER_RATE_LIMIT=0.5

# Reduce concurrent requests
export SCRAPER_MAX_RETRIES=1
```

### Logs and Debugging

```bash
# Check logs
tail -f logs/parly.log

# Enable debug logging
export LOG_LEVEL=DEBUG

# Run with verbose output
uvicorn api.main:app --reload --log-level debug
```

### Getting Help

1. Check the API documentation at `/docs`
2. Review the database schema in `docs/DATABASE_SCHEMA.md`
3. Check existing issues in the project repository
4. Run tests to verify your setup: `pytest`

## Production Deployment

For production deployment:

1. Set `ENVIRONMENT=production`
2. Use a production WSGI server (Gunicorn, Uvicorn with workers)
3. Configure proper logging and monitoring
4. Set up database backups
5. Configure CORS appropriately
6. Use environment variables for sensitive settings

Example production startup:

```bash
export ENVIRONMENT=production
export API_HOST=0.0.0.0
export API_PORT=8000
export LOG_LEVEL=WARNING

uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

---

*This setup guide is current as of the latest project state. Check the PROGRESS_LOG.md for the most recent updates.*
