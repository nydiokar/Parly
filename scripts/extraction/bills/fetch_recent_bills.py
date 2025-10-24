"""
Fetch recently introduced bills from Parliament API.

This script fetches new bills that have been recently introduced and adds them
to the database with complete metadata (sponsor, date, type, etc.).

Run this periodically (daily/weekly) to keep the database current with new legislation.

Uses the "recent_bills" endpoint: https://www.parl.ca/legisinfo/en/overview/json/recentlyintroduced
"""

import json
import sys
import os
import time
import logging
import requests
from datetime import datetime
from pathlib import Path

# Add parent directories for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../'))

from db_setup.create_database import Bill, Senator, Session

# ==================== CONFIGURATION ====================

CONFIG = {
    'timeout': 15,
    'rate_limit_seconds': 1,
    'max_retries': 3,
    'user_agent': 'ParlyDataCollector/1.0 (Educational Research; Parliamentary Data API)',
    'recent_bills_url': 'https://www.parl.ca/legisinfo/en/overview/json/recentlyintroduced'
}

# ==================== LOGGING SETUP ====================

def setup_logging():
    """Set up structured logging."""
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.FileHandler(log_dir / 'recent_bills_scraper.log'),
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

            elif response.status_code == 404:
                # Resource not found
                return None

            elif response.status_code == 429:  # Rate limited
                wait_time = 2 ** attempt * 5
                logger.warning(f"Rate limited (429), waiting {wait_time}s before retry {attempt+1}/{max_retries}")
                time.sleep(wait_time)

            elif response.status_code >= 500:  # Server error
                wait_time = 2 ** attempt
                logger.warning(f"Server error ({response.status_code}), retry {attempt+1}/{max_retries} after {wait_time}s")
                time.sleep(wait_time)

            else:
                logger.debug(f"HTTP {response.status_code} for {url}")
                return None

        except requests.Timeout:
            logger.warning(f"Timeout on attempt {attempt+1}/{max_retries}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)

        except requests.RequestException as e:
            logger.debug(f"Request error: {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)

    return None

# ==================== DATA EXTRACTION ====================

def extract_sponsor_name(bill_data):
    """Extract sponsor name from bill data."""
    return bill_data.get('SponsorPersonName')

def extract_introduction_date(bill_data):
    """Extract introduction date from bill data."""
    # Try multiple date fields in order of preference
    date_fields = [
        'PassedHouseFirstReadingDateTime',
        'PassedSenateFirstReadingDateTime',
        'LatestBillEventDateTime'
    ]

    for field in date_fields:
        date_str = bill_data.get(field)
        if date_str:
            try:
                # Handle different date formats
                if 'T' in date_str:
                    # ISO format with time: "2024-03-18T16:16:43.517"
                    date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                else:
                    # Date only format
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d')

                return date_obj.date()
            except ValueError:
                continue

    return None

def extract_bill_type(bill_data):
    """Extract bill type from bill data."""
    doc_type = bill_data.get('BillDocumentTypeNameEn', '')
    is_gov = bill_data.get('IsGovernmentBill', False)

    # Map document types to our bill_type field
    if is_gov:
        return 'government'
    elif 'Private Member' in doc_type:
        return 'private-public'  # Most common type for private bills
    elif 'Senate' in doc_type:
        return 'private-public'  # Senate bills are typically private-public
    else:
        return 'private-public'  # Default fallback

def create_bill_from_data(bill_data):
    """
    Create a Bill object from the API data.

    Args:
        bill_data: Dict from recent bills API

    Returns:
        Bill object ready for database insertion
    """
    legisinfo_id = bill_data.get('Id')
    bill_number = bill_data.get('NumberCode')
    parliament_num = bill_data.get('ParliamentNumber')
    session_num = bill_data.get('SessionNumber')

    if not all([legisinfo_id, bill_number, parliament_num, session_num]):
        logger.warning(f"Missing required fields for bill: {bill_data.get('NumberCode')}")
        return None

    # Extract data
    sponsor_name = extract_sponsor_name(bill_data)
    intro_date = extract_introduction_date(bill_data)
    bill_type = extract_bill_type(bill_data)

    # Create bill object
    bill = Bill(
        legisinfo_bill_id=legisinfo_id,
        bill_number=bill_number,
        parliament_number=parliament_num,
        session_number=session_num,
        short_title=bill_data.get('ShortTitleEn'),
        long_title=bill_data.get('LongTitleEn'),
        sponsor_name=sponsor_name,
        bill_type=bill_type,
        introduction_date=intro_date,
        chamber='House of Commons' if bill_data.get('IsHouseBill') else 'Senate'
    )

    return bill

# ==================== MAIN LOGIC ====================

def fetch_recent_bills():
    """
    Fetch recently introduced bills from Parliament API.

    Returns:
        List of bill data dictionaries, or None if failed
    """
    logger.info("Fetching recently introduced bills...")
    content = fetch_with_retry(CONFIG['recent_bills_url'])

    if not content:
        logger.error("Failed to fetch recent bills")
        return None

    try:
        bills_data = json.loads(content.decode('utf-8'))
        if isinstance(bills_data, list):
            logger.info(f"Found {len(bills_data)} recently introduced bills")
            return bills_data
        else:
            logger.error("Unexpected response format")
            return None

    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {e}")
        return None

def process_recent_bills(session, bills_data):
    """
    Process recent bills data and add new bills to database.

    Args:
        session: SQLAlchemy session
        bills_data: List of bill data from API

    Returns:
        Tuple of (new_bills_added, errors)
    """
    new_bills = 0
    errors = 0

    for bill_data in bills_data:
        try:
            legisinfo_id = bill_data.get('Id')
            bill_number = bill_data.get('NumberCode')

            if not legisinfo_id:
                logger.warning(f"Bill missing ID: {bill_number}")
                errors += 1
                continue

            # Check if bill already exists
            existing_bill = session.query(Bill).filter(
                (Bill.legisinfo_bill_id == legisinfo_id) |
                ((Bill.bill_number == bill_number) &
                 (Bill.parliament_number == bill_data.get('ParliamentNumber')) &
                 (Bill.session_number == bill_data.get('SessionNumber')))
            ).first()

            if existing_bill:
                logger.debug(f"Bill already exists: {bill_number}")
                continue

            # Create new bill
            bill = create_bill_from_data(bill_data)
            if bill:
                session.add(bill)
                new_bills += 1
                logger.info(f"Added new bill: {bill_number} (P{bill.parliament_number}-S{bill.session_number}) - {bill.sponsor_name}")
            else:
                logger.warning(f"Failed to create bill object: {bill_number}")
                errors += 1

        except Exception as e:
            logger.error(f"Error processing bill {bill_data.get('NumberCode')}: {e}")
            errors += 1
            continue

    return new_bills, errors

def main():
    """Main execution: fetch and process recently introduced bills."""
    logger.info("="*70)
    logger.info("FETCH RECENT BILLS - Real-time Updates")
    logger.info("="*70)

    start_time = datetime.now()
    session = Session()

    try:
        # Fetch recent bills
        bills_data = fetch_recent_bills()
        if not bills_data:
            logger.error("No recent bills data available")
            return

        # Process bills
        logger.info("Processing recent bills...")
        new_bills, errors = process_recent_bills(session, bills_data)

        # Commit changes
        if new_bills > 0:
            session.commit()
            logger.info(f"Committed {new_bills} new bills to database")
        else:
            logger.info("No new bills to commit")

        # Print summary
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info("="*70)
        logger.info("COMPLETION SUMMARY")
        logger.info("="*70)
        logger.info(f"  Recent bills fetched: {len(bills_data)}")
        logger.info(f"  New bills added: {new_bills}")
        logger.info(f"  Errors: {errors}")
        logger.info(f"  Elapsed time: {elapsed:.1f}s")

        if new_bills > 0:
            logger.info("✅ Database updated with new legislation!")
        else:
            logger.info("ℹ️  No new bills found (database is up to date)")

    except Exception as e:
        session.rollback()
        logger.error(f"FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()

    finally:
        session.close()

if __name__ == "__main__":
    main()
