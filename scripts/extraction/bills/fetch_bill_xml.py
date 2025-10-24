"""
Bill XML scraper to fetch summaries and full text for bills.

Fetches bill XML from parl.ca which contains:
- Summary (concise description of the bill)
- Preamble (context and reasoning)
- Full legislative text
- Sponsor information

URL Pattern:
https://www.parl.ca/Content/Bills/{parl}{sess}/{chamber}/{bill_type}-{num}/{bill_type}-{num}_1/{bill_type}-{num}_E.xml

Example: Parliament 45, Session 1, Bill C-214
https://www.parl.ca/Content/Bills/451/house/C-214/C-214_1/C-214_E.xml
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

from db_setup.create_database import Bill, Session

# ==================== CONFIGURATION ====================

CONFIG = {
    'timeout': 10,
    'rate_limit_seconds': 1,  # Be gentle with server
    'max_retries': 3,
    'user_agent': 'ParlyDataCollector/1.0 (Educational Research; Parliamentary Data API)',
    'batch_commit_size': 50,  # Commit every N bills
    'checkpoint_file': 'data/bill_xml_checkpoint.txt'
}

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
            logging.FileHandler(log_dir / 'bill_xml_scraper.log'),
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
                # Bill XML doesn't exist (common for old bills or private bills)
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

# ==================== BILL XML PARSING ====================

def build_bill_xml_url(parliament_num, session_num, bill_number, chamber):
    """
    Build URL for bill XML.

    Args:
        parliament_num: Parliament number (e.g., 45)
        session_num: Session number (e.g., 1)
        bill_number: Bill number (e.g., "C-214")
        chamber: Chamber name ("House of Commons" or "Senate") - used for logic

    Returns:
        URL string for the bill XML
    """
    # Extract bill type and number (e.g., "C-214" -> "C", "214")
    bill_type, bill_num = bill_number.split('-')

    # Determine chamber path based on bill type and number:
    # - House bills C-1 to C-200: "Government"
    # - House bills C-200+: "Private"
    # - Senate bills: "Senate" (assumption - need to verify)
    if bill_type == 'C':
        # House of Commons bill
        bill_num_int = int(bill_num)
        chamber_path = "Government" if bill_num_int <= 200 else "Private"
    elif bill_type == 'S':
        # Senate bill - use "Senate" as chamber path
        chamber_path = "Senate"
    else:
        # Unknown bill type - try "Private" as fallback
        chamber_path = "Private"

    # Build URL: /Bills/{parl}{sess}/{chamber}/{type}-{num}/{type}-{num}_1/{type}-{num}_E.xml
    url = (
        f"https://www.parl.ca/Content/Bills/{parliament_num}{session_num}/"
        f"{chamber_path}/{bill_type}-{bill_num}/{bill_type}-{bill_num}_1/{bill_type}-{bill_num}_E.xml"
    )

    return url

def parse_bill_xml(xml_data):
    """
    Parse bill XML and extract summary and other details.

    Args:
        xml_data: Raw XML bytes from parl.ca

    Returns:
        Dict with extracted data, or None if parsing failed
    """
    try:
        root = ET.fromstring(xml_data)

        # Extract summary (most important field)
        summary = None
        summary_elem = root.find('.//Summary/Provision/Text')
        if summary_elem is not None and summary_elem.text:
            summary = summary_elem.text.strip()

        # Extract preamble text (multiple provisions)
        preamble_parts = []
        for preamble_provision in root.findall('.//Preamble/Provision/Text'):
            if preamble_provision is not None and preamble_provision.text:
                preamble_parts.append(preamble_provision.text.strip())

        preamble = ' '.join(preamble_parts) if preamble_parts else None

        # Combine summary and preamble for full context
        full_summary = summary
        if summary and preamble:
            full_summary = f"{summary}\n\nPreamble: {preamble}"
        elif preamble and not summary:
            full_summary = preamble

        # Extract sponsor name (display name like "Mr. Davies", "Sen. Smith")
        sponsor_name = None
        sponsor_elem = root.find('.//BillSponsor')
        if sponsor_elem is not None:
            sponsor_name = ''.join(sponsor_elem.itertext()).strip()

        # Extract bill type from root attribute
        bill_type = root.get('bill-type')  # e.g., "private-public", "government"

        # Extract introduction date (first reading)
        introduction_date = None
        date_elem = root.find('.//BillHistory/Stages/Date')
        if date_elem is not None:
            year = date_elem.find('YYYY')
            month = date_elem.find('MM')
            day = date_elem.find('DD')
            if all([year is not None, month is not None, day is not None]):
                # Format as YYYY-MM-DD for SQLite DATE type
                introduction_date = f"{year.text}-{month.text.zfill(2)}-{day.text.zfill(2)}"

        return {
            'summary': full_summary,
            'sponsor_name': sponsor_name,
            'bill_type': bill_type,
            'introduction_date': introduction_date
        }

    except Exception as e:
        logger.error(f"Error parsing XML: {e}")
        return None

# ==================== CHECKPOINT SYSTEM ====================

def save_checkpoint(bill_id):
    """Save progress checkpoint."""
    checkpoint_path = Path(CONFIG['checkpoint_file'])
    checkpoint_path.parent.mkdir(exist_ok=True)

    with open(checkpoint_path, 'w') as f:
        f.write(f"{bill_id}\n{datetime.now().isoformat()}")

def load_checkpoint():
    """Load last checkpoint."""
    checkpoint_path = Path(CONFIG['checkpoint_file'])

    if not checkpoint_path.exists():
        return None

    try:
        with open(checkpoint_path, 'r') as f:
            bill_id = int(f.readline().strip())
            timestamp = f.readline().strip()
            logger.info(f"Resuming from checkpoint: bill_id={bill_id} (saved at {timestamp})")
            return bill_id
    except Exception as e:
        logger.warning(f"Failed to load checkpoint: {e}")
        return None

def clear_checkpoint():
    """Clear checkpoint file after successful completion."""
    checkpoint_path = Path(CONFIG['checkpoint_file'])
    if checkpoint_path.exists():
        checkpoint_path.unlink()

# ==================== STATISTICS TRACKING ====================

class ScraperStats:
    """Track scraper statistics."""

    def __init__(self):
        self.total_bills_processed = 0
        self.total_summaries_found = 0
        self.total_summaries_updated = 0
        self.total_404s = 0
        self.total_errors = 0
        self.start_time = datetime.now()

    def print_summary(self):
        """Print final statistics."""
        elapsed = (datetime.now() - self.start_time).total_seconds()
        logger.info("="*70)
        logger.info("SCRAPER STATISTICS")
        logger.info("="*70)
        logger.info(f"  Bills processed: {self.total_bills_processed}")
        logger.info(f"  Summaries found: {self.total_summaries_found}")
        logger.info(f"  Summaries updated: {self.total_summaries_updated}")
        logger.info(f"  404s (no XML): {self.total_404s}")
        logger.info(f"  Errors: {self.total_errors}")
        logger.info(f"  Success rate: {self.total_summaries_found / max(self.total_bills_processed, 1) * 100:.1f}%")
        logger.info(f"  Elapsed time: {elapsed:.1f}s ({elapsed/60:.1f} minutes)")
        if self.total_bills_processed > 0:
            logger.info(f"  Average time per bill: {elapsed/self.total_bills_processed:.2f}s")

# ==================== CORE SCRAPER LOGIC ====================

def fetch_and_update_bill_summary(session, bill, stats):
    """
    Fetch bill XML and update summary in database.

    Args:
        session: SQLAlchemy session
        bill: Bill object from database
        stats: ScraperStats object

    Returns:
        True if summary was updated, False otherwise
    """
    # Build URL
    url = build_bill_xml_url(
        bill.parliament_number,
        bill.session_number,
        bill.bill_number,
        bill.chamber
    )

    # Fetch XML
    xml_data = fetch_with_retry(url)

    if not xml_data:
        stats.total_404s += 1
        return False

    # Parse XML
    parsed_data = parse_bill_xml(xml_data)

    if not parsed_data:
        stats.total_errors += 1
        return False

    # Update bill with extracted data
    updated = False

    if parsed_data.get('summary'):
        bill.summary = parsed_data['summary']
        stats.total_summaries_found += 1
        updated = True

    if parsed_data.get('sponsor_name'):
        bill.sponsor_name = parsed_data['sponsor_name']
        updated = True

    if parsed_data.get('bill_type'):
        bill.bill_type = parsed_data['bill_type']
        updated = True

    if parsed_data.get('introduction_date'):
        # Convert date string to Python date object for SQLAlchemy
        try:
            bill.introduction_date = datetime.strptime(parsed_data['introduction_date'], '%Y-%m-%d').date()
            updated = True
        except ValueError as e:
            logger.warning(f"Invalid date format for bill {bill.bill_number}: {parsed_data['introduction_date']} - {e}")
            # Keep the old date or set to None if invalid

    if updated:
        stats.total_summaries_updated += 1

    return updated

def main():
    """Main execution: fetch bill summaries for all bills."""
    logger.info("="*70)
    logger.info("BILL XML SCRAPER - Fetching Summaries")
    logger.info("="*70)

    session = Session()
    stats = ScraperStats()

    try:
        # Load checkpoint (if resuming)
        last_checkpoint = load_checkpoint()

        # Get all bills that need XML data (missing summary, sponsor_name, bill_type, or introduction_date)
        logger.info("Fetching bills from database...")

        # Query bills that are missing any XML-derived fields
        query = session.query(Bill).filter(
            (Bill.summary.is_(None)) |
            (Bill.sponsor_name.is_(None)) |
            (Bill.bill_type.is_(None)) |
            (Bill.introduction_date.is_(None))
        )

        # If resuming, skip to checkpoint
        if last_checkpoint:
            query = query.filter(Bill.bill_id >= last_checkpoint)

        # Order by parliament and session for logical progression
        bills = query.order_by(
            Bill.parliament_number.desc(),
            Bill.session_number.desc()
        ).all()

        logger.info(f"Found {len(bills)} bills missing XML data")

        if not bills:
            logger.info("No bills to process - all bills have complete XML data!")
            return

        # Process each bill
        logger.info("Processing bills...")
        logger.info(f"(This will take ~{CONFIG['rate_limit_seconds']}s per bill)")

        for i, bill in enumerate(bills):
            try:
                logger.info(
                    f"[{i+1}/{len(bills)}] {bill.bill_number} "
                    f"(Parl {bill.parliament_number}-{bill.session_number})"
                )

                success = fetch_and_update_bill_summary(session, bill, stats)

                stats.total_bills_processed += 1

                if success:
                    logger.info(f"    XML data updated")
                else:
                    logger.debug(f"    No XML data found")

                # Batch commit
                if (i + 1) % CONFIG['batch_commit_size'] == 0:
                    session.commit()
                    save_checkpoint(bill.bill_id)
                    logger.info(f"Checkpoint saved at bill {i+1}")

                # Rate limiting
                time.sleep(CONFIG['rate_limit_seconds'])

            except Exception as e:
                session.rollback()
                stats.total_errors += 1
                logger.error(f"Error processing {bill.bill_number}: {e}")
                continue

        # Final commit
        session.commit()
        clear_checkpoint()

        # Print statistics
        stats.print_summary()

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
