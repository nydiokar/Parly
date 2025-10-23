# Bill Scrapers

Three production scrapers to collect complete bill data:

## 1. fetch_all_bills.py
**What**: Fetches bill metadata (number, title, status, sponsor)
**Source**: LEGISinfo XML API (by parliament session)
**Run**: `python scripts/extraction/bills/fetch_all_bills.py`
**Runtime**: ~4 hours (covers Parliaments 35-45)

## 2. fetch_bill_progress.py
**What**: Fetches bill progress stages (first reading, committee, royal assent, etc.)
**Source**: LEGISinfo JSON API
**Run**: `python scripts/extraction/bills/fetch_bill_progress.py`
**Runtime**: ~2 hours (for all bills in database)

## 3. fetch_bill_xml.py
**What**: Fetches bill details from XML (summary, sponsor name, bill type, introduction date)
**Source**: Parliament of Canada bill XML files
**Run**: `python scripts/extraction/bills/fetch_bill_xml.py`
**Runtime**: ~2 hours (for all bills in database)
**Note**: Requires database migration first

**Extracts**:
- Summary + preamble text
- Sponsor display name ("Mr. Davies", "Sen. Smith")
- Bill type ("government", "private-public")
- Introduction date (first reading)

## Typical Workflow

**First time (full data collection)**:
```bash
# 1. Get all bills metadata
python scripts/extraction/bills/fetch_all_bills.py

# 2. Get progress for those bills
python scripts/extraction/bills/fetch_bill_progress.py

# 3. Run database migration (adds 4 XML fields to bills table)
alembic upgrade head

# 4. Get bill XML data (summary, sponsor_name, bill_type, introduction_date)
python scripts/extraction/bills/fetch_bill_xml.py
```

**Updates (incremental)**:
```bash
# All three scrapers are incremental - they skip existing data
# Just run them periodically to get new bills
python scripts/extraction/bills/fetch_all_bills.py
python scripts/extraction/bills/fetch_bill_progress.py
python scripts/extraction/bills/fetch_bill_xml.py
```

## Current Database Status
- **7,061 bills** with metadata (House + Senate)
- **~10,000 progress events** tracked
- **0 bills** with XML data (summary, sponsor_name, bill_type, introduction_date)
  - Need to run migration + fetch_bill_xml.py
