"""
Incremental bill progress extractor for Canadian Parliament.

Follows the PROVEN pattern with production-grade enhancements:
1. Fetch all bills from database
2. For each bill, fetch progress JSON from parl.ca
3. Parse progress stages (House and Senate)
4. Insert only completed stages (State = 4)
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
import json
import sys
import os
import time
import logging
import signal
from datetime import datetime
from pathlib import Path

# Add parent directories for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../'))

from db_setup.create_database import Bill, BillProgress, Session

# ==================== CONFIGURATION ====================

CONFIG = {
    'timeout': 10,
    'rate_limit_seconds': 1,  # 1 second as per docs
    'max_retries': 3,
    'user_agent': 'ParlyDataCollector/1.0 (Educational Research; Parliamentary Data API)',
    'batch_commit_size': 20,  # Commit every N bills
    'checkpoint_file': 'data/bill_progress_checkpoint.txt'
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
            logging.FileHandler(log_dir / 'bill_progress_scraper.log'),
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

            elif response.status_code == 404:  # Bill not found (expected for some bills)
                logger.debug(f"Bill not found (404): {url}")
                return None

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

def save_checkpoint(bill_id):
    """Save progress checkpoint."""
    checkpoint_path = Path(CONFIG['checkpoint_file'])
    checkpoint_path.parent.mkdir(exist_ok=True)

    with open(checkpoint_path, 'w') as f:
        f.write(f"{bill_id}\n{datetime.now().isoformat()}")

    logger.debug(f"Checkpoint saved: {bill_id}")

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
        logger.info("Checkpoint cleared")

# ==================== DATA VALIDATION ====================

def parse_date(date_string):
    """
    Parse date from JSON format to Python date object.

    Args:
        date_string: Date string in format '2021-11-23T14:20:19.547'

    Returns:
        date object or None
    """
    if not date_string:
        return None

    try:
        # Handle both formats: with and without milliseconds
        if '.' in date_string:
            dt = datetime.strptime(date_string.split('.')[0], '%Y-%m-%dT%H:%M:%S')
        else:
            dt = datetime.strptime(date_string, '%Y-%m-%dT%H:%M:%S')
        return dt.date()
    except Exception as e:
        logger.warning(f"Failed to parse date '{date_string}': {e}")
        return None

def validate_progress_data(progress_dict):
    """
    Validate progress data before insertion.

    Args:
        progress_dict: Dictionary of progress data to validate

    Returns:
        True if valid, False otherwise
    """
    # Check required fields
    required_fields = ['bill_id', 'status']
    for field in required_fields:
        if field not in progress_dict or progress_dict[field] is None:
            logger.warning(f"Missing required field: {field}")
            return False

    return True

# ==================== STATISTICS TRACKING ====================

class ScraperStats:
    """Track scraper statistics."""

    def __init__(self):
        self.total_bills_processed = 0
        self.total_stages_fetched = 0
        self.total_stages_inserted = 0
        self.total_stages_skipped = 0
        self.bills_with_progress = 0
        self.total_errors = 0
        self.bills_not_found = 0
        self.start_time = datetime.now()

    def print_summary(self):
        """Print final statistics."""
        elapsed = (datetime.now() - self.start_time).total_seconds()
        logger.info("="*70)
        logger.info("SCRAPER STATISTICS")
        logger.info("="*70)
        logger.info(f"  Bills processed: {self.total_bills_processed}")
        logger.info(f"  Bills with progress: {self.bills_with_progress}")
        logger.info(f"  Bills not found (404): {self.bills_not_found}")
        logger.info(f"  Total stages fetched: {self.total_stages_fetched}")
        logger.info(f"  Total stages inserted: {self.total_stages_inserted}")
        logger.info(f"  Total stages skipped (not completed): {self.total_stages_skipped}")
        logger.info(f"  Total errors: {self.total_errors}")
        logger.info(f"  Elapsed time: {elapsed:.1f}s ({elapsed/60:.1f} minutes)")
        if self.total_bills_processed > 0:
            logger.info(f"  Average time per bill: {elapsed/self.total_bills_processed:.2f}s")

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

def parse_bill_number(bill_number):
    """
    Parse bill number into type and number.

    Args:
        bill_number: String like 'C-215', 'S-4', etc.

    Returns:
        Tuple of (bill_type, number) or (None, None) if parsing fails
    """
    try:
        # Handle formats like "C-215", "S-4", etc.
        if '-' in bill_number:
            bill_type, num = bill_number.split('-', 1)
            return (bill_type, num)
        else:
            logger.warning(f"Unable to parse bill number: {bill_number}")
            return (None, None)
    except Exception as e:
        logger.error(f"Error parsing bill number '{bill_number}': {e}")
        return (None, None)

def fetch_bill_progress_json(parliament, session, bill_number):
    """
    Fetch bill progress JSON from parl.ca.

    Args:
        parliament: Parliament number
        session: Session number
        bill_number: Full bill number (e.g., 'C-215')

    Returns:
        JSON content bytes, or None if failed
    """
    bill_type, num = parse_bill_number(bill_number)
    if not bill_type or not num:
        return None

    url = f"https://www.parl.ca/LegisInfo/en/bill/{parliament}-{session}/{bill_type}-{num}/json?view=progress"
    return fetch_with_retry(url)

def parse_bill_progress_json(json_data, bill_id):
    """
    Parse bill progress JSON and return list of progress stage dictionaries.

    Args:
        json_data: Raw JSON bytes from parl.ca
        bill_id: The bill's database ID for linking progress

    Returns:
        List of progress dictionaries ready for database insertion
    """
    try:
        data = json.loads(json_data)
        progress_stages = []

        # Handle both formats: list or object
        # parl.ca API sometimes returns a list with one object
        if isinstance(data, list):
            if len(data) == 0:
                return []
            data = data[0]  # Get first element

        # Extract BillStages object
        bill_stages = data.get('BillStages', {})

        # Process House stages
        house_stages = bill_stages.get('HouseBillStages', [])
        for stage in house_stages:
            # Extract ALL stages (not just State = 4)
            stage_dict = {
                'bill_id': bill_id,
                'status': stage.get('BillStageName', 'Unknown'),
                'progress_date': parse_date(stage.get('StateAsOfDate')),
                'state': stage.get('State'),
                'state_name': stage.get('StateName')
            }
            progress_stages.append(stage_dict)

        # Process Senate stages
        senate_stages = bill_stages.get('SenateBillStages', [])
        for stage in senate_stages:
            # Extract ALL stages (not just State = 4)
            stage_dict = {
                'bill_id': bill_id,
                'status': stage.get('BillStageName', 'Unknown'),
                'progress_date': parse_date(stage.get('StateAsOfDate')),
                'state': stage.get('State'),
                'state_name': stage.get('StateName')
            }
            progress_stages.append(stage_dict)

        return progress_stages

    except Exception as e:
        logger.error(f"ERROR parsing JSON: {e}")
        return []

def get_all_bills_from_db(session):
    """
    Get all bills from database.

    Returns:
        List of dicts with bill information
    """
    bills = []

    for bill in session.query(Bill).all():
        bills.append({
            'id': bill.bill_id,
            'number': bill.bill_number,
            'parliament': bill.parliament_number,
            'session': bill.session_number
        })

    return bills

def get_existing_progress_signatures(session, bill_id):
    """
    Get set of progress signatures already in database for this bill.

    Signature format: (bill_id, status, progress_date)
    This uniquely identifies a progress stage for duplicate checking.
    """
    signatures = set()

    progress_records = session.query(BillProgress).filter_by(bill_id=bill_id).all()
    for progress in progress_records:
        sig = (progress.bill_id, progress.status, progress.progress_date)
        signatures.add(sig)

    return signatures

def insert_progress_for_bill(session, bill_data, stats):
    """
    Fetch and insert progress for a single bill (incremental, duplicate-safe).

    Args:
        session: SQLAlchemy session
        bill_data: Dict with bill information
        stats: ScraperStats object

    Returns:
        Number of new progress stages inserted
    """
    bill_id = bill_data['id']
    bill_number = bill_data['number']
    parliament = bill_data['parliament']
    bill_session = bill_data['session']

    # Fetch progress JSON
    json_data = fetch_bill_progress_json(parliament, bill_session, bill_number)
    if not json_data:
        stats.bills_not_found += 1
        return 0

    # Parse progress stages
    progress_data = parse_bill_progress_json(json_data, bill_id)
    if not progress_data:
        return 0

    stats.total_stages_fetched += len(progress_data)

    # Get existing progress to avoid duplicates
    existing_sigs = get_existing_progress_signatures(session, bill_id)

    # Insert only new progress stages
    new_stages = 0
    for progress_dict in progress_data:
        # Validate data
        if not validate_progress_data(progress_dict):
            stats.total_errors += 1
            continue

        # Create signature for duplicate check
        sig = (progress_dict['bill_id'], progress_dict['status'], progress_dict['progress_date'])

        if sig not in existing_sigs:
            progress = BillProgress(**progress_dict)
            session.add(progress)
            new_stages += 1
        else:
            stats.total_stages_skipped += 1

    return new_stages

def main():
    """Main execution: fetch progress for all bills incrementally."""
    logger.info("="*70)
    logger.info("INCREMENTAL BILL PROGRESS EXTRACTION")
    logger.info("="*70)

    session = Session()
    stats = ScraperStats()

    try:
        # Load checkpoint (if resuming)
        last_checkpoint = load_checkpoint()

        # Step 1: Get all bills from database
        logger.info("Fetching all bills from database...")
        bills = get_all_bills_from_db(session)
        logger.info(f"Found {len(bills)} bills")

        if not bills:
            logger.error("No bills in database. Run bills scraper first.")
            return

        # Find resume point
        start_index = 0
        if last_checkpoint:
            for i, bill in enumerate(bills):
                if bill['id'] == last_checkpoint:
                    start_index = i + 1
                    break

        # Step 2: Process each bill
        logger.info(f"Processing progress for {len(bills) - start_index} bills (starting from index {start_index})...")
        logger.info(f"(This will take a while - ~{CONFIG['rate_limit_seconds']} second per bill)")

        for i, bill_data in enumerate(bills[start_index:], start=start_index):
            if shutdown_requested:
                logger.info("Shutdown requested, saving progress...")
                session.commit()
                save_checkpoint(bill_data['id'])
                break

            bill_number = bill_data['number']

            logger.info(f"[{i+1}/{len(bills)}] Bill {bill_number} (Parl {bill_data['parliament']}-{bill_data['session']})")

            try:
                new_stages = insert_progress_for_bill(session, bill_data, stats)

                stats.total_bills_processed += 1

                if new_stages > 0:
                    stats.total_stages_inserted += new_stages
                    stats.bills_with_progress += 1
                    logger.info(f"    Added {new_stages} new progress stages")
                else:
                    logger.info(f"    No new progress stages")

                # Batch commit for performance
                if (i + 1) % CONFIG['batch_commit_size'] == 0:
                    session.commit()
                    save_checkpoint(bill_data['id'])
                    logger.info(f"Checkpoint saved at bill {i+1}")

                # Rate limiting
                time.sleep(CONFIG['rate_limit_seconds'])

            except Exception as e:
                session.rollback()
                stats.total_errors += 1
                logger.error(f"ERROR processing bill {bill_number}: {e}")
                continue

        # Final commit
        session.commit()
        clear_checkpoint()

        # Step 3: Print statistics
        stats.print_summary()

        # Get final progress count
        total_progress = session.query(BillProgress).count()
        logger.info(f"\nTotal progress records in database: {total_progress}")

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
