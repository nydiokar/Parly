"""
Incremental bills extractor for Canadian Parliament.

Follows the PROVEN pattern from fetch_votes.py with production-grade enhancements:
1. Fetch all members from database (with their IDs)
2. For each member, fetch their sponsored bills XML from parl.ca
3. Parse bills and check against existing bills in database (using legisinfo_bill_id)
4. Insert only new bills (incremental, duplicate-safe)
5. Commit in batches for reliability and performance
6. Implements production standards from scraper_template.py:
   - Retry logic with exponential backoff
   - User-Agent header
   - Structured logging
   - Progress checkpointing (resume capability)
   - Request session pooling
   - Data validation
   - Statistics tracking
   - Graceful shutdown handling
"""

import requests
import xml.etree.ElementTree as ET
import sys
import os
import time
import logging
import signal
from datetime import datetime
from pathlib import Path

# Add parent directories for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../'))

from db_setup.create_database import Member, Bill, Session

# ==================== CONFIGURATION ====================

CONFIG = {
    'timeout': 10,
    'rate_limit_seconds': 2,
    'max_retries': 3,
    'user_agent': 'ParlyDataCollector/1.0 (Educational Research; Parliamentary Data API)',
    'batch_commit_size': 10,  # Commit every N members
    'checkpoint_file': 'data/bills_checkpoint.txt'
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
            logging.FileHandler(log_dir / 'bills_scraper.log'),
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

# ==================== CHECKPOINT SYSTEM ====================

def save_checkpoint(member_id):
    """Save progress checkpoint."""
    checkpoint_path = Path(CONFIG['checkpoint_file'])
    checkpoint_path.parent.mkdir(exist_ok=True)

    with open(checkpoint_path, 'w') as f:
        f.write(f"{member_id}\n{datetime.now().isoformat()}")

    logger.debug(f"Checkpoint saved: {member_id}")

def load_checkpoint():
    """Load last checkpoint."""
    checkpoint_path = Path(CONFIG['checkpoint_file'])

    if not checkpoint_path.exists():
        return None

    try:
        with open(checkpoint_path, 'r') as f:
            member_id = int(f.readline().strip())
            timestamp = f.readline().strip()
            logger.info(f"Resuming from checkpoint: member_id={member_id} (saved at {timestamp})")
            return member_id
    except Exception as e:
        logger.warning(f"Failed to load checkpoint: {e}")
        return None

def clear_checkpoint():
    """Clear checkpoint file after successful completion."""
    checkpoint_path = Path(CONFIG['checkpoint_file'])
    if checkpoint_path.exists():
        checkpoint_path.unlink()
        logger.info("Checkpoint cleared")

# ==================== DATA VALIDATION ====================

def validate_bill_data(bill_dict):
    """
    Validate bill data before insertion.

    Args:
        bill_dict: Dictionary of bill data to validate

    Returns:
        True if valid, False otherwise
    """
    # Check required fields
    required_fields = ['legisinfo_bill_id', 'bill_number', 'parliament_number', 'session_number']
    for field in required_fields:
        if field not in bill_dict or bill_dict[field] is None:
            logger.warning(f"Missing required field: {field}")
            return False

    # Validate parliament number range
    if bill_dict['parliament_number'] < 35 or bill_dict['parliament_number'] > 50:
        logger.warning(f"Invalid parliament number: {bill_dict['parliament_number']}")
        return False

    return True

# ==================== STATISTICS TRACKING ====================

class ScraperStats:
    """Track scraper statistics."""

    def __init__(self):
        self.total_members_processed = 0
        self.total_bills_fetched = 0
        self.total_bills_inserted = 0
        self.total_bills_skipped = 0
        self.members_with_bills = 0
        self.total_errors = 0
        self.start_time = datetime.now()

    def print_summary(self):
        """Print final statistics."""
        elapsed = (datetime.now() - self.start_time).total_seconds()
        logger.info("="*70)
        logger.info("SCRAPER STATISTICS")
        logger.info("="*70)
        logger.info(f"  Members processed: {self.total_members_processed}")
        logger.info(f"  Members with bills: {self.members_with_bills}")
        logger.info(f"  Total bills fetched: {self.total_bills_fetched}")
        logger.info(f"  Total bills inserted: {self.total_bills_inserted}")
        logger.info(f"  Total bills skipped (duplicates): {self.total_bills_skipped}")
        logger.info(f"  Total errors: {self.total_errors}")
        logger.info(f"  Elapsed time: {elapsed:.1f}s ({elapsed/60:.1f} minutes)")
        if self.total_members_processed > 0:
            logger.info(f"  Average time per member: {elapsed/self.total_members_processed:.2f}s")

# ==================== GRACEFUL SHUTDOWN ====================

shutdown_requested = False

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    global shutdown_requested
    logger.info("Shutdown signal received. Finishing current operation...")
    shutdown_requested = True

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# ==================== CORE SCRAPER LOGIC ====================

def fetch_member_bills_xml(member_id):
    """
    Fetch bills XML for a member using their member ID.

    Args:
        member_id: Member's unique ID (SponsorId in parl.ca)

    Returns:
        XML content as bytes, or None if failed
    """
    url = f"https://www.parl.ca/legisinfo/en/bills/xml?parlsession=all&sponsor={member_id}&advancedview=true"
    return fetch_with_retry(url)

def parse_bills_xml(xml_data, sponsor_id):
    """
    Parse bills XML and return list of bill dictionaries.

    Args:
        xml_data: Raw XML bytes from parl.ca
        sponsor_id: The member's ID for linking bills

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
            chamber = bill_elem.find('OriginatingChamberId')

            # Skip if missing critical fields
            if not all([bill_id is not None, bill_number is not None,
                       parliament_num is not None, session_num is not None]):
                logger.debug(f"Skipping bill with missing critical fields")
                continue

            # Map chamber ID to name (1 = House of Commons, 2 = Senate)
            chamber_name = "House of Commons" if chamber is not None and chamber.text == "1" else "Senate"

            bill_dict = {
                'legisinfo_bill_id': int(bill_id.text),
                'bill_number': bill_number.text,
                'parliament_number': int(parliament_num.text),
                'session_number': int(session_num.text),
                'short_title': short_title.text if short_title is not None else None,
                'long_title': long_title.text if long_title is not None else None,
                'status': status.text if status is not None else "Introduced",
                'sponsor_id': sponsor_id,
                'chamber': chamber_name
            }

            bills.append(bill_dict)

        return bills

    except Exception as e:
        logger.error(f"ERROR parsing XML: {e}")
        return []

def get_all_members_from_db(session):
    """
    Get all members from database.

    Returns:
        List of dicts: [{'id': 123, 'name': 'John Doe'}, ...]
    """
    members = []

    for member in session.query(Member).all():
        members.append({
            'id': member.member_id,
            'name': member.name
        })

    return members

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

def insert_bills_for_member(session, member_data, existing_bill_ids, stats):
    """
    Fetch and insert bills for a single member (incremental, duplicate-safe).

    Args:
        session: SQLAlchemy session
        member_data: Dict with 'id' and 'name'
        existing_bill_ids: Set of legisinfo_bill_id already in database
        stats: ScraperStats object

    Returns:
        Number of new bills inserted
    """
    member_id = member_data['id']
    member_name = member_data['name']

    # Fetch bills XML
    xml_data = fetch_member_bills_xml(member_id)
    if not xml_data:
        return 0

    # Parse bills
    bills_data = parse_bills_xml(xml_data, member_id)
    if not bills_data:
        return 0

    stats.total_bills_fetched += len(bills_data)

    # Insert only new bills
    new_bills = 0
    for bill_dict in bills_data:
        # Validate data
        if not validate_bill_data(bill_dict):
            stats.total_errors += 1
            continue

        # Check for duplicates using legisinfo_bill_id
        if bill_dict['legisinfo_bill_id'] in existing_bill_ids:
            stats.total_bills_skipped += 1
            continue

        # Insert new bill
        bill = Bill(**bill_dict)
        session.add(bill)
        existing_bill_ids.add(bill_dict['legisinfo_bill_id'])  # Update set to prevent duplicates in same run
        new_bills += 1

    return new_bills

def main():
    """Main execution: fetch bills for all members incrementally."""
    logger.info("="*70)
    logger.info("INCREMENTAL BILLS EXTRACTION")
    logger.info("="*70)

    session = Session()
    stats = ScraperStats()

    try:
        # Load checkpoint (if resuming)
        last_checkpoint = load_checkpoint()

        # Step 1: Get all members from database
        logger.info("Fetching all members from database...")
        members = get_all_members_from_db(session)
        logger.info(f"Found {len(members)} members")

        if not members:
            logger.error("No members in database. Run member scrapers first.")
            return

        # Find resume point
        start_index = 0
        if last_checkpoint:
            for i, member in enumerate(members):
                if member['id'] == last_checkpoint:
                    start_index = i + 1
                    break

        # Step 2: Get existing bill IDs for duplicate prevention
        logger.info("Loading existing bills from database...")
        existing_bill_ids = get_existing_bill_ids(session)
        logger.info(f"Found {len(existing_bill_ids)} existing bills")

        # Step 3: Process each member
        logger.info(f"Processing bills for {len(members) - start_index} members (starting from index {start_index})...")
        logger.info(f"(This will take a while - ~{CONFIG['rate_limit_seconds']} seconds per member)")

        for i, member_data in enumerate(members[start_index:], start=start_index):
            if shutdown_requested:
                logger.info("Shutdown requested, saving progress...")
                session.commit()
                save_checkpoint(member_data['id'])
                break

            member_name = member_data['name']

            logger.info(f"[{i+1}/{len(members)}] {member_name}")

            try:
                new_bills = insert_bills_for_member(session, member_data, existing_bill_ids, stats)

                stats.total_members_processed += 1

                if new_bills > 0:
                    stats.total_bills_inserted += new_bills
                    stats.members_with_bills += 1
                    logger.info(f"    Added {new_bills} new bills")
                else:
                    logger.info(f"    No new bills")

                # Batch commit for performance
                if (i + 1) % CONFIG['batch_commit_size'] == 0:
                    session.commit()
                    save_checkpoint(member_data['id'])
                    logger.info(f"Checkpoint saved at member {i+1}")

                # Rate limiting
                time.sleep(CONFIG['rate_limit_seconds'])

            except Exception as e:
                session.rollback()
                stats.total_errors += 1
                logger.error(f"ERROR processing {member_name}: {e}")
                continue

        # Final commit
        session.commit()
        clear_checkpoint()

        # Step 4: Print statistics
        stats.print_summary()

        # Get final bill count
        total_bills = session.query(Bill).count()
        logger.info(f"\nTotal bills in database: {total_bills}")

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
