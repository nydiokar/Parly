# Parly - Parliamentary Data API

## Project Vision

Parly is a standalone service designed to provide a comprehensive, clean, and accessible API layer for Canadian parliamentary data. Its primary goal is to automate the collection, storage, and retrieval of information related to Members of Parliament (MPs), their roles, voting records, sponsored bills, and debate interventions.

This project serves as the foundational data provider for future applications, including the originally envisioned LLM-powered analysis system. By focusing first on a robust and reliable API, we enable a wide range of potential use cases.

---

## Documentation

This README serves as the entry point to the comprehensive documentation suite. For detailed information, please refer to the following documents in the `docs/` directory:

### Core Documentation

📋 **[TECHNICAL_SPECIFICATION.md](docs/architecture/TECHNICAL_SPECIFICATION.md)**
- Complete database schema with all tables and relationships
- Detailed API endpoint specifications with request/response formats
- Pydantic data models and validation rules
- Technical constraints and performance requirements

📊 **[DATA_SOURCES.md](docs/data/DATA_SOURCES.md)**
- All data source URLs and endpoints
- HTML/XML/JSON structure documentation
- Field mapping from sources to database
- Data extraction strategies and best practices
- Rate limiting and politeness policies

🏗️ **[ARCHITECTURE.md](docs/architecture/ARCHITECTURE.md)**
- System architecture overview with component diagrams
- Data flow documentation
- Design decisions and rationale
- Scalability considerations
- Security architecture

🔨 **[IMPLEMENTATION_GUIDE.md](docs/development/IMPLEMENTATION_GUIDE.md)**
- Step-by-step implementation instructions for all phases
- Code examples for each component
- Verification steps and testing procedures
- Troubleshooting guidance
- Estimated time to complete each phase

⚙️ **[DEVELOPMENT_WORKFLOW.md](docs/development/DEVELOPMENT_WORKFLOW.md)**
- Development environment setup
- Testing strategy and examples
- Git workflow and branching strategy
- Deployment procedures (local and production)
- Monitoring and maintenance tasks

---

## Quick Start

### For Developers Building the Project

1. **Read the documentation in this order:**
   - Start with [ARCHITECTURE.md](docs/architecture/ARCHITECTURE.md) to understand the system
   - Review [TECHNICAL_SPECIFICATION.md](docs/architecture/TECHNICAL_SPECIFICATION.md) for detailed specs
   - Follow [IMPLEMENTATION_GUIDE.md](docs/development/IMPLEMENTATION_GUIDE.md) step-by-step

2. **Set up your environment:**
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   pip install -e ".[dev]"
   ```

3. **Start implementing:**
   Follow the three-phase roadmap in the Implementation Guide.

### For LLMs Building the Project

The documentation has been specifically designed to enable autonomous implementation:

1. **Begin with [IMPLEMENTATION_GUIDE.md](docs/development/IMPLEMENTATION_GUIDE.md)** - It provides complete, step-by-step instructions
2. **Reference [TECHNICAL_SPECIFICATION.md](docs/architecture/TECHNICAL_SPECIFICATION.md)** - For exact schemas and specifications
3. **Consult [DATA_SOURCES.md](docs/data/DATA_SOURCES.md)** - For scraping implementation details
4. **Check [DEVELOPMENT_WORKFLOW.md](docs/development/DEVELOPMENT_WORKFLOW.md)** - For testing and deployment

All code examples are complete and ready to use. Each step includes verification commands to confirm success.

---

## Current State & Progress

### ✅ Completed
- Database schema definition (SQLAlchemy)
- Member ID scraper (functional)
- Member roles scraper (functional)
- Scraped data: `member_ids.csv` and `member_roles.json`
- Comprehensive documentation suite

### 🚧 In Progress / To Do
- Populate database with existing scraped data
- Complete votes scraper
- Create bills scraper
- Create bill progress scraper
- Build FastAPI application
- Implement all API endpoints
- Add testing suite
- Create orchestration script

**For detailed roadmap, see [IMPLEMENTATION_GUIDE.md](docs/development/IMPLEMENTATION_GUIDE.md)**

---

## Technical Architecture (Summary)

**Data Pipeline:**
```
Scrapers (Python) → Raw Data (JSON/CSV) → Database (SQLite) → API (FastAPI) → Clients
```

**Technology Stack:**
- **Language:** Python 3.10+
- **Database:** SQLite 3
- **ORM:** SQLAlchemy 2.0
- **API Framework:** FastAPI
- **Data Validation:** Pydantic 2.0
- **Testing:** pytest

**For detailed architecture, see [ARCHITECTURE.md](docs/architecture/ARCHITECTURE.md)**

---

## Project Structure

```
Parly/
├── docs/                           # Comprehensive documentation
│   ├── architecture/              # System architecture and specs
│   │   ├── ARCHITECTURE.md
│   │   ├── TECHNICAL_SPECIFICATION.md
│   │   └── DATABASE_SCHEMA.md
│   ├── data/                      # Data sources and scraping
│   │   ├── DATA_SOURCES.md
│   │   └── SCRAPING_BEST_PRACTICES.md
│   ├── development/               # Development workflow and setup
│   │   ├── DEVELOPMENT_WORKFLOW.md
│   │   ├── IMPLEMENTATION_GUIDE.md
│   │   └── SETUP.md
│   ├── analytics/                 # Analytics and planning
│   │   ├── ANALYTICS_IDEAS.md
│   │   ├── ROADMAP.md
│   │   ├── EXTERNAL_CORRELATIONS.md
│   │   ├── VIRAL_ANALYTICS_CONCEPTS.md
│   │   └── WILD_DISCOVERIES.md
│   └── historical/                # Historical research and findings
│       └── historical_parlyinfo_search.md
├── api/                           # FastAPI application (to be created)
│   ├── main.py
│   ├── models.py
│   ├── database.py
│   └── routes/
├── db_setup/                      # Database setup and insertion scripts
│   ├── create_database.py        # SQLAlchemy schema
│   ├── insert_roles_db.py        # Insert roles data
│   └── url_templates.py          # URL templates for scraping
├── scripts/                       # Data extraction scripts
│   └── extraction/
│       ├── member_id_scraper.py  # ✅ Complete
│       ├── scrape_roles.py       # ✅ Complete
│       ├── fetch_votes.py        # ⚠️ Needs completion
│       ├── fetch_bills.py        # ❌ To be created
│       └── fetch_bill_progress.py # ❌ To be created
├── data/                          # Data storage
│   ├── member_ids.csv            # ✅ Scraped
│   ├── member_roles.json         # ✅ Scraped
│   ├── parliament.db             # SQLite database
│   └── raw/                      # Example data files
├── tests/                         # Test suite (to be created)
├── README.md                      # This file
├── requirements.txt               # Python dependencies
└── pyproject.toml                # Modern Python config (to be created)
```

---

## API Endpoints (Planned)

Once implemented, the API will provide the following endpoints:

- `GET /api/members` - List all members with filtering
- `GET /api/members/{id}` - Get member details
- `GET /api/members/{id}/roles` - Get member roles
- `GET /api/members/{id}/votes` - Get member voting records
- `GET /api/bills` - List all bills with filtering
- `GET /api/bills/{id}` - Get bill details with progress
- `GET /api/statistics` - Get aggregate statistics

**Full API specification in [TECHNICAL_SPECIFICATION.md](docs/architecture/TECHNICAL_SPECIFICATION.md)**

---

## Implementation Timeline

**Estimated time to complete:** 9-13 hours of active development

- **Phase 1:** Data Foundation - 4-6 hours (+ scraping wait time)
- **Phase 2:** API Layer - 3-4 hours
- **Phase 3:** Refinement - 2-3 hours

**Detailed breakdown in [IMPLEMENTATION_GUIDE.md](docs/development/IMPLEMENTATION_GUIDE.md)**

---

## Future Vision: The Analysis Layer

Once the Parliamentary Data API is stable and reliable, the original vision of an LLM-powered analysis system can be realized. This future **Analysis Layer** would be a separate service that consumes the API, allowing it to:

- Perform sentiment analysis on debate transcripts
- Identify voting patterns and caucus cohesion
- Answer natural language questions about parliamentary activities
- Track member positions on issues over time
- Generate insights about parliamentary dynamics

By decoupling the data layer from the analysis layer, we ensure that the project remains modular, scalable, and maintainable.

---

## Contributing

1. Read the [DEVELOPMENT_WORKFLOW.md](docs/development/DEVELOPMENT_WORKFLOW.md)
2. Follow the git workflow and code style guidelines
3. Write tests for new features
4. Update documentation as needed
5. Submit pull requests for review

---

## License

MIT

---

## Contact

For questions, issues, or contributions, please create an issue in the repository.
