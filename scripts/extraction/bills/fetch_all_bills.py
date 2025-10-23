"""
Comprehensive bills extractor for Canadian Parliament - ALL BILLS (House + Senate).

Fetches ALL bills by parliament session from LEGISinfo XML API,
regardless of sponsor (MPs or Senators).

This approach is more comprehensive than fetching by member/senator sponsor
because it captures:
- All House bills (C-prefix)
- All Senate bills (S-prefix)
- Government bills without individual sponsors
- Bills where sponsor info may be incomplete
"""

import requests
import xml.etree.ElementTree as ET
import sys
import os
import time
import logging
from datetime import datetime
from pathlib import Path

# Add parent directories for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../'))

from db_setup.create_database import Bill, Senator, Session

# ==================== CONFIGURATION ====================

CONFIG = {
    'timeout': 15,
    'rate_limit_seconds': 3,  # Be polite to the server
    'max_retries': 3,
    'user_agent': 'ParlyDataCollector/1.0 (Educational Research; Parliamentary Data API)',
    'checkpoint_file': 'data/all_bills_checkpoint.txt'
}

# Parliaments to scrape (35-45, sessions 1-3 typical)
# Parliament 35: 1994-1997
# Parliament 36-44: 1997-2021
# Parliament 45: 2025-present
PARLIAMENTS = [
    (35, 1), (35, 2),
    (36, 1), (36, 2),
    (37, 1), (37, 2), (37, 3),
    (38, 1),
    (39, 1), (39, 2),
    (40, 1), (40, 2), (40, 3),
    (41, 1), (41, 2),
    (42, 1),
    (43, 1), (43, 2),
    (44, 1),
    (45, 1),
]

# ==================== LOGGING SETUP ====================

def setup_logging():
    """Set up structured logging with file and console output."""
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.FileHandler(log_dir / 'all_bills_scraper.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()

# ==================== REQUEST HELPERS ====================

# Create persistent session for connection pooling
http_session = requests.Session()
http_session.headers.update({
    'User-Agent': CONFIG['user_agent']
})

def fetch_with_retry(url, max_retries=None):
    """
    Fetch URL with retry logic and exponential backoff.

    Args:
        url: URL to fetch
        max_retries: Number of retries (defaults to CONFIG value)

    Returns:
        Response content bytes, or None if all retries failed
    """
    max_retries = max_retries or CONFIG['max_retries']

    for attempt in range(max_retries):
        try:
            response = http_session.get(url, timeout=CONFIG['timeout'])

            if response.status_code == 200:
                return response.content

            elif response.status_code == 429:  # Rate limited
                wait_time = 2 ** attempt * 5  # Exponential backoff (5s, 10s, 20s)
                logger.warning(f"Rate limited (429), waiting {wait_time}s before retry {attempt+1}/{max_retries}")
                time.sleep(wait_time)

            elif response.status_code >= 500:  # Server error
                wait_time = 2 ** attempt  # Exponential backoff (1s, 2s, 4s)
                logger.warning(f"Server error ({response.status_code}), retry {attempt+1}/{max_retries} after {wait_time}s")
                time.sleep(wait_time)

            else:
                logger.error(f"HTTP {response.status_code} for {url}")
                return None

        except requests.Timeout:
            logger.warning(f"Timeout on attempt {attempt+1}/{max_retries}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)

        except requests.RequestException as e:
            logger.error(f"Request error: {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)

    logger.error(f"Failed after {max_retries} attempts: {url}")
    return None

# ==================== DATA PARSING ====================

def parse_bills_xml(xml_data):
    """
    Parse bills XML and return list of bill dictionaries.

    Args:
        xml_data: Raw XML bytes from parl.ca

    Returns:
        List of bill dictionaries ready for database insertion
    """
    try:
        root = ET.fromstring(xml_data)
        bills = []

        for bill_elem in root.findall('.//Bill'):
            # Extract all fields
            bill_id = bill_elem.find('BillId')
            bill_number = bill_elem.find('BillNumberFormatted')
            parliament_num = bill_elem.find('ParliamentNumber')
            session_num = bill_elem.find('SessionNumber')
            short_title = bill_elem.find('ShortTitleEn')
            long_title = bill_elem.find('LongTitleEn')
            status = bill_elem.find('LatestCompletedMajorStageEn')
            chamber_id = bill_elem.find('OriginatingChamberId')
            sponsor_name = bill_elem.find('SponsorEn')

            # Skip if missing critical fields
            if not all([bill_id is not None, bill_number is not None,
                       parliament_num is not None, session_num is not None]):
                logger.debug(f"Skipping bill with missing critical fields")
                continue

            # Map chamber ID to name (1 = House of Commons, 2 = Senate)
            chamber_name = "House of Commons" if chamber_id is not None and chamber_id.text == "1" else "Senate"

            # Extract sponsor name (format: "Hon. John Doe" or "Sen. Jane Smith")
            sponsor_text = sponsor_name.text if sponsor_name is not None else None

            bill_dict = {
                'legisinfo_bill_id': int(bill_id.text),
                'bill_number': bill_number.text,
                'parliament_number': int(parliament_num.text),
                'session_number': int(session_num.text),
                'short_title': short_title.text if short_title is not None else None,
                'long_title': long_title.text if long_title is not None else None,
                'status': status.text if status is not None else "Introduced",
                'chamber': chamber_name,
                'sponsor_name_raw': sponsor_text,  # Will process this later
            }

            bills.append(bill_dict)

        return bills

    except Exception as e:
        logger.error(f"ERROR parsing XML: {e}")
        return []

# ==================== SENATOR MATCHING ====================

def get_senator_lookup(session):
    """
    Create a lookup dictionary for senators by name.

    Returns:
        Dict mapping senator names to senator_ids
    """
    senators = {}
    for senator in session.query(Senator).all():
        # Store both full name and potential variations
        senators[senator.name.lower()] = senator.senator_id
        # Also try "Last, First" format
        name_parts = senator.name.split()
        if len(name_parts) >= 2:
            last_first = f"{name_parts[-1]}, {' '.join(name_parts[:-1])}"
            senators[last_first.lower()] = senator.senator_id

    return senators

def match_sponsor(sponsor_name_raw, senator_lookup):
    """
    Match sponsor name to senator_id if it's a senator.

    Args:
        sponsor_name_raw: Raw sponsor string from XML (e.g., "Sen. Yuen Pau Woo")
        senator_lookup: Dict mapping senator names to IDs

    Returns:
        tuple: (sponsor_id, senator_sponsor_id)
               - sponsor_id is None (MPs handled separately)
               - senator_sponsor_id is senator ID or None
    """
    if not sponsor_name_raw:
        return (None, None)

    # Check if it's a senator (starts with "Sen.")
    if sponsor_name_raw.startswith("Sen."):
        # Extract senator name (remove "Sen. " prefix)
        senator_name = sponsor_name_raw.replace("Sen. ", "").strip()

        # Try exact match
        senator_id = senator_lookup.get(senator_name.lower())

        if senator_id:
            return (None, senator_id)
        else:
            logger.warning(f"Senator not found in database: {senator_name}")
            return (None, None)

    # It's an MP sponsor - leave sponsor_id as None (will be handled by MP-sponsor scraper)
    return (None, None)

# ==================== DATABASE OPERATIONS ====================

def get_existing_bill_ids(session):
    """
    Get set of bill IDs (legisinfo_bill_id) already in database.

    Returns:
        Set of legisinfo_bill_id values for duplicate checking
    """
    bill_ids = set()
    bills = session.query(Bill.legisinfo_bill_id).filter(Bill.legisinfo_bill_id.isnot(None)).all()
    for (bill_id,) in bills:
        bill_ids.add(bill_id)
    return bill_ids

# ==================== MAIN SCRAPER ====================

def fetch_bills_for_parliament(parliament_num, session_num, senator_lookup, existing_bill_ids, db_session):
    """
    Fetch all bills for a specific parliament session.

    Args:
        parliament_num: Parliament number (e.g., 44)
        session_num: Session number (e.g., 1)
        senator_lookup: Dict mapping senator names to IDs
        existing_bill_ids: Set of existing bill IDs in database
        db_session: SQLAlchemy database session

    Returns:
        Number of new bills inserted
    """
    parl_session = f"{parliament_num}-{session_num}"
    url = f"https://www.parl.ca/legisinfo/en/bills/xml?parlsession={parl_session}"

    logger.info(f"Fetching bills for Parliament {parl_session}...")

    # Fetch XML
    xml_data = fetch_with_retry(url)
    if not xml_data:
        logger.error(f"Failed to fetch bills for {parl_session}")
        return 0

    # Parse bills
    bills_data = parse_bills_xml(xml_data)
    if not bills_data:
        logger.warning(f"No bills found for {parl_session}")
        return 0

    logger.info(f"  Found {len(bills_data)} bills in XML")

    # Insert only new bills
    new_bills = 0
    for bill_dict in bills_data:
        # Check for duplicates using legisinfo_bill_id
        if bill_dict['legisinfo_bill_id'] in existing_bill_ids:
            continue

        # Match sponsor to senator if applicable
        sponsor_id, senator_sponsor_id = match_sponsor(
            bill_dict.pop('sponsor_name_raw'),
            senator_lookup
        )

        bill_dict['sponsor_id'] = sponsor_id
        bill_dict['senator_sponsor_id'] = senator_sponsor_id

        # Insert new bill
        bill = Bill(**bill_dict)
        db_session.add(bill)
        existing_bill_ids.add(bill_dict['legisinfo_bill_id'])
        new_bills += 1

    return new_bills

def main():
    """Main execution: fetch all bills for all parliaments."""
    logger.info("="*70)
    logger.info("COMPREHENSIVE BILLS EXTRACTION (ALL PARLIAMENTS)")
    logger.info("="*70)

    session = Session()

    try:
        # Step 1: Load senator lookup
        logger.info("\nLoading senators from database...")
        senator_lookup = get_senator_lookup(session)
        logger.info(f"Loaded {len(senator_lookup)} senator name variations")

        # Step 2: Get existing bill IDs
        logger.info("\nLoading existing bills from database...")
        existing_bill_ids = get_existing_bill_ids(session)
        logger.info(f"Found {len(existing_bill_ids)} existing bills")

        # Step 3: Process each parliament session
        logger.info(f"\nProcessing {len(PARLIAMENTS)} parliament sessions...")

        total_new_bills = 0
        sessions_processed = 0
        sessions_with_bills = 0

        for parliament_num, session_num in PARLIAMENTS:
            new_bills = fetch_bills_for_parliament(
                parliament_num,
                session_num,
                senator_lookup,
                existing_bill_ids,
                session
            )

            sessions_processed += 1

            if new_bills > 0:
                session.commit()  # Commit after each parliament session
                total_new_bills += new_bills
                sessions_with_bills += 1
                logger.info(f"  ✓ Parliament {parliament_num}-{session_num}: Added {new_bills} new bills")
            else:
                logger.info(f"  - Parliament {parliament_num}-{session_num}: No new bills")

            # Rate limiting
            time.sleep(CONFIG['rate_limit_seconds'])

        # Step 4: Summary
        logger.info("\n" + "="*70)
        logger.info("SCRAPER STATISTICS")
        logger.info("="*70)
        logger.info(f"  Parliament sessions processed: {sessions_processed}")
        logger.info(f"  Sessions with new bills: {sessions_with_bills}")
        logger.info(f"  Total new bills inserted: {total_new_bills}")

        # Get final bill count
        total_bills = session.query(Bill).count()
        house_bills = session.query(Bill).filter_by(chamber="House of Commons").count()
        senate_bills = session.query(Bill).filter_by(chamber="Senate").count()

        logger.info(f"\nTotal bills in database: {total_bills}")
        logger.info(f"  House of Commons bills: {house_bills}")
        logger.info(f"  Senate bills: {senate_bills}")

    except Exception as e:
        session.rollback()
        logger.error(f"FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()

    finally:
        http_session.close()
        session.close()

if __name__ == "__main__":
    main()
