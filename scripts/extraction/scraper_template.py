"""
Production-grade scraper template with best practices.

Use this template for all new scrapers (bills, bill_progress, etc.)
Implements all recommended best practices from SCRAPING_BEST_PRACTICES.md
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
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))

from db_setup.create_database import Session
# Import your specific models here


# ==================== CONFIGURATION ====================

CONFIG = {
    'timeout': 10,
    'rate_limit_seconds': 2,
    'max_retries': 3,
    'user_agent': 'ParlyDataCollector/1.0 (Educational Research; https://github.com/yourrepo)',
    'batch_commit_size': 10,  # Commit every N members for balance
    'checkpoint_file': 'data/scraper_checkpoint.txt'
}


# ==================== LOGGING SETUP ====================

def setup_logging(log_file='logs/scraper.log'):
    """Set up structured logging with file and console output."""
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.FileHandler(log_dir / log_file),
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

def save_checkpoint(identifier):
    """Save progress checkpoint."""
    checkpoint_path = Path(CONFIG['checkpoint_file'])
    checkpoint_path.parent.mkdir(exist_ok=True)

    with open(checkpoint_path, 'w') as f:
        f.write(f"{identifier}\n{datetime.now().isoformat()}")

    logger.debug(f"Checkpoint saved: {identifier}")


def load_checkpoint():
    """Load last checkpoint."""
    checkpoint_path = Path(CONFIG['checkpoint_file'])

    if not checkpoint_path.exists():
        return None

    try:
        with open(checkpoint_path, 'r') as f:
            identifier = f.readline().strip()
            timestamp = f.readline().strip()
            logger.info(f"Resuming from checkpoint: {identifier} (saved at {timestamp})")
            return identifier
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

def validate_data(data_dict, required_fields):
    """
    Validate data before insertion.

    Args:
        data_dict: Dictionary of data to validate
        required_fields: List of required field names

    Returns:
        True if valid, False otherwise
    """
    # Check required fields
    for field in required_fields:
        if field not in data_dict or data_dict[field] is None:
            logger.warning(f"Missing required field: {field}")
            return False

    # Add custom validation logic here
    # Example: parliament number range check
    if 'parliament_number' in data_dict:
        if data_dict['parliament_number'] < 35 or data_dict['parliament_number'] > 50:
            logger.warning(f"Invalid parliament number: {data_dict['parliament_number']}")
            return False

    return True


# ==================== STATISTICS TRACKING ====================

class ScraperStats:
    """Track scraper statistics."""

    def __init__(self):
        self.total_processed = 0
        self.total_fetched = 0
        self.total_inserted = 0
        self.total_skipped = 0
        self.total_errors = 0
        self.start_time = datetime.now()

    def print_summary(self):
        """Print final statistics."""
        elapsed = (datetime.now() - self.start_time).total_seconds()
        logger.info("="*70)
        logger.info("SCRAPER STATISTICS")
        logger.info("="*70)
        logger.info(f"  Total processed: {self.total_processed}")
        logger.info(f"  Total fetched: {self.total_fetched}")
        logger.info(f"  Total inserted: {self.total_inserted}")
        logger.info(f"  Total skipped: {self.total_skipped}")
        logger.info(f"  Total errors: {self.total_errors}")
        logger.info(f"  Elapsed time: {elapsed:.1f}s ({elapsed/60:.1f} minutes)")
        if self.total_processed > 0:
            logger.info(f"  Average time per item: {elapsed/self.total_processed:.2f}s")


# ==================== GRACEFUL SHUTDOWN ====================

shutdown_requested = False


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    global shutdown_requested
    logger.info("Shutdown signal received. Finishing current operation...")
    shutdown_requested = True


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


# ==================== MAIN SCRAPER LOGIC ====================

def scrape_item(session, item_data):
    """
    Scrape and insert data for a single item.

    THIS IS A TEMPLATE - IMPLEMENT YOUR SPECIFIC LOGIC HERE

    Args:
        session: SQLAlchemy session
        item_data: Dictionary with item information

    Returns:
        Number of records inserted
    """
    # 1. Fetch data with retry
    url = "YOUR_URL_HERE"
    xml_data = fetch_with_retry(url)

    if not xml_data:
        return 0

    # 2. Parse data
    try:
        # Your parsing logic here
        parsed_data = []  # Replace with actual parsing
        pass

    except Exception as e:
        logger.error(f"Parse error: {e}")
        return 0

    # 3. Validate data
    valid_data = [d for d in parsed_data if validate_data(d, ['required_field1', 'required_field2'])]

    # 4. Check for duplicates and insert
    inserted = 0
    for data in valid_data:
        # Your duplicate check logic here
        # Insert if not exists
        inserted += 1

    return inserted


def main():
    """Main scraper execution."""
    logger.info("="*70)
    logger.info("SCRAPER STARTING")
    logger.info("="*70)

    session = Session()
    stats = ScraperStats()

    try:
        # Load checkpoint (if resuming)
        last_checkpoint = load_checkpoint()

        # Get list of items to process
        items = []  # Replace with your data source

        # Find resume point
        start_index = 0
        if last_checkpoint:
            for i, item in enumerate(items):
                if str(item['id']) == last_checkpoint:
                    start_index = i + 1
                    break

        logger.info(f"Processing {len(items) - start_index} items (starting from index {start_index})")

        # Process each item
        for i, item in enumerate(items[start_index:], start=start_index):
            if shutdown_requested:
                logger.info("Shutdown requested, saving progress...")
                session.commit()
                save_checkpoint(str(item['id']))
                break

            logger.info(f"[{i+1}/{len(items)}] Processing {item['name']}")
            stats.total_processed += 1

            try:
                inserted = scrape_item(session, item)
                stats.total_inserted += inserted

                # Batch commit
                if (i + 1) % CONFIG['batch_commit_size'] == 0:
                    session.commit()
                    save_checkpoint(str(item['id']))
                    logger.info(f"Checkpoint saved at item {i+1}")

                # Rate limiting
                time.sleep(CONFIG['rate_limit_seconds'])

            except Exception as e:
                session.rollback()
                stats.total_errors += 1
                logger.error(f"Error processing {item['name']}: {e}")
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
