"""
Fill missing bill data from alternative sources.

When XML scraping fails (87% of bills), we can extract data from:
1. Bill progress JSON (sponsors, dates, bill types)
2. Bills sponsored XML
3. Other raw data sources

This script fills in:
- sponsor_name (from SponsorPersonName)
- introduction_date (from first reading dates)
- bill_type (from BillDocumentTypeName)
"""

import json
import sys
import os
import time
import logging
import requests
import threading
import queue
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

# Add parent directories for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../'))

from db_setup.create_database import Bill, Session

# ==================== CONFIGURATION ====================

CONFIG = {
    'timeout': 10,
    'rate_limit_seconds': 0.5,  # Reduced for concurrent requests
    'max_retries': 3,
    'user_agent': 'ParlyDataCollector/1.0 (Educational Research; Parliamentary Data API)',
    'batch_commit_size': 200,  # Increased batch size
    'checkpoint_file': 'data/bill_fill_checkpoint.txt',
    'max_concurrent_requests': 3,  # Number of concurrent threads
    'request_queue_size': 10  # Queue size for rate limiting
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
            logging.FileHandler(log_dir / 'fill_missing_bill_data.log'),
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
                # Bill data doesn't exist
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

# ==================== API DATA FETCHING ====================

def fetch_bill_data_from_api(bill):
    """
    Fetch bill data directly from Parliament JSON API.

    Uses the same endpoint as documented in url_templates.py:
    "all_bills": "https://www.parl.ca/legisinfo/en/bill/{parliament}-{session}/{bill_type}-{bill_number}/json"

    Args:
        bill: Bill object

    Returns:
        Dict with bill data from API, or None if not found
    """
    try:
        # Parse bill number (e.g., "C-214" -> "C", "214")
        if '-' not in bill.bill_number:
            logger.info(f"Invalid bill number format: {bill.bill_number}")
            return None

        bill_type, bill_num = bill.bill_number.split('-', 1)

        # Build API URL using the template from url_templates.py
        url = f"https://www.parl.ca/legisinfo/en/bill/{bill.parliament_number}-{bill.session_number}/{bill_type}-{bill_num}/json"
        logger.info(f"Fetching from URL: {url}")

        content = fetch_with_retry(url)
        if not content:
            return None

        # Parse JSON response
        try:
            data = json.loads(content.decode('utf-8'))

            # The API returns a list with one bill object
            if isinstance(data, list) and len(data) > 0:
                return data[0]  # Return the first (and only) bill object
            elif isinstance(data, dict):
                return data
            else:
                logger.debug(f"Unexpected JSON structure for bill {bill.bill_number}")
                return None

        except json.JSONDecodeError as e:
            logger.debug(f"JSON decode error for bill {bill.bill_number}: {e}")
            return None

    except Exception as e:
        logger.info(f"Error fetching data for bill {bill.bill_number}: {e}")
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

# ==================== CORE LOGIC ====================

def update_bill_from_progress_data(session, bill, progress_data):
    """
    Update bill with data from progress JSON.

    Args:
        session: SQLAlchemy session
        bill: Bill object
        progress_data: Dict with bill data from JSON

    Returns:
        True if bill was updated, False otherwise
    """
    updated = False

    # Extract sponsor name
    if not bill.sponsor_name:
        sponsor_name = extract_sponsor_name(progress_data)
        if sponsor_name:
            logger.info(f"    Found sponsor: {sponsor_name}")
            bill.sponsor_name = sponsor_name
            updated = True

    # Extract introduction date
    if not bill.introduction_date:
        intro_date = extract_introduction_date(progress_data)
        if intro_date:
            logger.info(f"    Found date: {intro_date}")
            bill.introduction_date = intro_date
            updated = True

    # Extract bill type
    if not bill.bill_type:
        bill_type = extract_bill_type(progress_data)
        if bill_type:
            logger.info(f"    Found type: {bill_type}")
            bill.bill_type = bill_type
            updated = True

    if not updated:
        logger.info(f"    Bill already has all data: sponsor={bill.sponsor_name}, date={bill.introduction_date}, type={bill.bill_type}")

    return updated

def process_bill_worker(bill_queue, result_queue, session_factory):
    """
    Worker function for concurrent bill processing.
    Each worker has its own database session.
    """
    session = session_factory()

    while True:
        try:
            bill = bill_queue.get(timeout=1)
            if bill is None:  # Sentinel value to stop worker
                break

            bill_id = bill.bill_id
            bill_number = bill.bill_number
            parliament = bill.parliament_number
            session_num = bill.session_number

            logger.info(f"Processing {bill_number} (Parl {parliament}-{session_num})")

            # Fetch data from API
            api_data = fetch_bill_data_from_api(bill)

            if api_data:
                # Update bill with data
                updated = update_bill_from_progress_data(session, bill, api_data)
                result_queue.put((bill_id, updated, api_data is not None))
            else:
                result_queue.put((bill_id, False, False))

            bill_queue.task_done()

        except queue.Empty:
            continue
        except Exception as e:
            logger.error(f"Worker error processing bill: {e}")
            result_queue.put((None, False, False))
            continue

    session.close()

def main():
    """Main execution: fill missing bill data from Parliament API with concurrent processing."""
    logger.info("="*70)
    logger.info("FILL MISSING BILL DATA FROM API (CONCURRENT)")
    logger.info("="*70)

    start_time = datetime.now()

    try:
        # Create main session for querying bills
        main_session = Session()

        # Load checkpoint
        last_checkpoint = load_checkpoint()

        # Get bills missing any XML-derived fields
        query = main_session.query(Bill).filter(
            (Bill.summary.is_(None)) |
            (Bill.sponsor_name.is_(None)) |
            (Bill.bill_type.is_(None)) |
            (Bill.introduction_date.is_(None))
        )

        if last_checkpoint:
            query = query.filter(Bill.bill_id >= last_checkpoint)

        bills = query.order_by(Bill.parliament_number.desc(), Bill.session_number.desc()).all()

        logger.info(f"Found {len(bills)} bills with missing data to process")

        if not bills:
            logger.info("No bills to process - all bills have complete data!")
            return

        logger.info(f"Processing with {CONFIG['max_concurrent_requests']} concurrent threads...")
        logger.info(f"Estimated time: ~{len(bills) * CONFIG['rate_limit_seconds'] / CONFIG['max_concurrent_requests'] / 60:.1f} minutes")

        # Create queues for inter-thread communication
        bill_queue = queue.Queue(maxsize=CONFIG['request_queue_size'])
        result_queue = queue.Queue()

        # Create session factory for workers
        def session_factory():
            return Session()

        # Start worker threads
        workers = []
        for i in range(CONFIG['max_concurrent_requests']):
            t = threading.Thread(
                target=process_bill_worker,
                args=(bill_queue, result_queue, session_factory),
                name=f"BillWorker-{i+1}"
            )
            t.daemon = True
            t.start()
            workers.append(t)

        # Feed bills to workers
        stats = {'processed': 0, 'updated': 0, 'errors': 0, 'api_calls': 0}

        for bill in bills:
            bill_queue.put(bill)
            stats['api_calls'] += 1

        # Add sentinel values to stop workers
        for _ in range(CONFIG['max_concurrent_requests']):
            bill_queue.put(None)

        # Process results and commit in batches
        batch_updates = []
        last_commit_time = time.time()

        while stats['processed'] < len(bills):
            try:
                result = result_queue.get(timeout=1)
                bill_id, was_updated, had_data = result

                if bill_id is not None:
                    stats['processed'] += 1
                    if was_updated:
                        stats['updated'] += 1
                        batch_updates.append(bill_id)

                # Batch commit every N bills or every 30 seconds
                should_commit = (
                    len(batch_updates) >= CONFIG['batch_commit_size'] or
                    time.time() - last_commit_time > 30
                )

                if should_commit and batch_updates:
                    try:
                        # Commit all pending updates
                        main_session.commit()
                        if batch_updates:
                            save_checkpoint(max(batch_updates))
                            logger.info(f"Committed {len(batch_updates)} updates, checkpoint at bill {max(batch_updates)}")
                        batch_updates = []
                        last_commit_time = time.time()
                    except Exception as e:
                        main_session.rollback()
                        logger.error(f"Commit error: {e}")
                        stats['errors'] += 1

                # Progress logging
                if stats['processed'] % 50 == 0:
                    elapsed = (datetime.now() - start_time).total_seconds()
                    rate = stats['processed'] / elapsed if elapsed > 0 else 0
                    logger.info(f"Progress: {stats['processed']}/{len(bills)} bills ({rate:.1f}/sec), {stats['updated']} updated")

            except queue.Empty:
                continue

        # Final commit
        if batch_updates:
            try:
                main_session.commit()
                logger.info(f"Final commit: {len(batch_updates)} updates")
            except Exception as e:
                main_session.rollback()
                logger.error(f"Final commit error: {e}")

        clear_checkpoint()

        # Wait for workers to finish
        for t in workers:
            t.join(timeout=5)

        # Print final statistics
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info("="*70)
        logger.info("COMPLETION STATISTICS")
        logger.info("="*70)
        logger.info(f"  Bills processed: {stats['processed']}")
        logger.info(f"  API calls made: {stats['api_calls']}")
        logger.info(f"  Bills updated: {stats['updated']}")
        logger.info(f"  Errors: {stats['errors']}")
        logger.info(f"  Elapsed time: {elapsed:.1f}s ({elapsed/60:.1f} minutes)")
        if stats['processed'] > 0:
            logger.info(f"  Average time per bill: {elapsed/stats['processed']:.2f}s")
            logger.info(f"  Processing rate: {stats['processed']/elapsed:.1f} bills/sec")
        logger.info(f"  Success rate: {stats['updated'] / max(stats['processed'], 1) * 100:.1f}%")

    except Exception as e:
        logger.error(f"FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()

    finally:
        main_session.close()

if __name__ == "__main__":
    main()
