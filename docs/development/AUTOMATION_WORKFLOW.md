# Automation Workflow

## Overview

This document describes the automated data collection, maintenance, and monitoring procedures for the Parly Parliamentary Data API. The system is designed to automatically stay current with Canadian parliamentary data through scheduled jobs and real-time monitoring.

---

## Automated Data Collection

### Real-Time Bill Tracking

**Purpose**: Keep the database current with newly introduced legislation.

**Script**: `scripts/extraction/bills/fetch_recent_bills.py`

**Frequency**: Daily (recommended)

**What it does**:
- Fetches the 9 most recently introduced bills from Parliament API
- Adds new bills with complete metadata (sponsor, date, type, titles)
- Skips bills already in database
- Logs all activity for monitoring

**Performance**: ~1 second execution time

### Backfill Missing Data

**Purpose**: Fill gaps in historical bill data.

**Script**: `scripts/extraction/bills/fill_missing_bill_data.py`

**Frequency**: Weekly (recommended)

**What it does**:
- Concurrent processing with 3 threads
- Fetches sponsor names, introduction dates, and bill types for bills missing this data
- Processes ~6,000 bills in ~17 minutes
- Checkpoint system allows resuming interrupted runs

**Performance**: ~3 bills/second (9 bills/second total with concurrency)

---

## Scheduling Automation

### Windows Task Scheduler

1. **Open Task Scheduler**:
   ```powershell
   taskschd.msc
   ```

2. **Create New Task**:
   - Name: "Parly Daily Bills Update"
   - Security options: Run whether user is logged on or not
   - Configure for: Windows 10

3. **Triggers Tab**:
   - New Trigger → Daily
   - Start: 6:00 AM
   - Recur every: 1 days

4. **Actions Tab**:
   - New Action → Start a program
   - Program/script: `C:\Users\solastic\prj\Parly\venv\Scripts\python.exe`
   - Arguments: `scripts/extraction/bills/fetch_recent_bills.py`
   - Start in: `C:\Users\solastic\prj\Parly`

### Linux/Mac Cron Jobs

**Daily bill updates (6 AM daily)**:
```bash
0 6 * * * cd /path/to/parly && /path/to/venv/bin/python scripts/extraction/bills/fetch_recent_bills.py
```

**Weekly data backfill (Sundays 2 AM)**:
```bash
0 2 * * 0 cd /path/to/parly && /path/to/venv/bin/python scripts/extraction/bills/fill_missing_bill_data.py
```

### Python Automation Script

For more complex scheduling with error handling:

```python
# scripts/automation_scheduler.py
import schedule
import time
import subprocess
import logging

def run_recent_bills():
    """Run daily recent bills update."""
    try:
        result = subprocess.run([
            'python', 'scripts/extraction/bills/fetch_recent_bills.py'
        ], capture_output=True, text=True, timeout=300)

        if result.returncode == 0:
            logging.info("Daily bill update completed successfully")
        else:
            logging.error(f"Daily bill update failed: {result.stderr}")

    except subprocess.TimeoutExpired:
        logging.error("Daily bill update timed out")
    except Exception as e:
        logging.error(f"Daily bill update error: {e}")

def run_backfill():
    """Run weekly data backfill."""
    try:
        result = subprocess.run([
            'python', 'scripts/extraction/bills/fill_missing_bill_data.py'
        ], capture_output=True, text=True, timeout=3600)  # 1 hour timeout

        if result.returncode == 0:
            logging.info("Weekly backfill completed successfully")
        else:
            logging.error(f"Weekly backfill failed: {result.stderr}")

    except subprocess.TimeoutExpired:
        logging.error("Weekly backfill timed out")
    except Exception as e:
        logging.error(f"Weekly backfill error: {e}")

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.FileHandler('logs/automation.log'),
            logging.StreamHandler()
        ]
    )

    # Schedule jobs
    schedule.every().day.at("06:00").do(run_recent_bills)
    schedule.every().sunday.at("02:00").do(run_backfill)

    logging.info("Automation scheduler started")

    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute
```

---

## Data Completeness Monitoring

### Automated Health Checks

**Script**: `scripts/validate_data_integrity.py`

**Purpose**: Monitor data quality and completeness.

**Key Metrics to Track**:
```python
# Expected thresholds
MIN_SPONSOR_COMPLETENESS = 0.95  # 95%
MIN_DATE_COMPLETENESS = 0.95     # 95%
MIN_TYPE_COMPLETENESS = 0.95     # 95%

# Recent data checks
RECENT_BILLS_DAYS = 30
MIN_RECENT_BILLS_PER_WEEK = 5
```

**Alert Conditions**:
- Data completeness drops below 95%
- No new bills added in 3+ days
- Script failures or timeouts
- Database connection issues

### Dashboard Monitoring

Create a simple monitoring dashboard:

```python
# scripts/monitoring/dashboard.py
from db_setup.create_database import Session, Bill
from datetime import datetime, timedelta

def generate_report():
    """Generate data completeness report."""
    session = Session()

    # Overall stats
    total_bills = session.query(Bill).count()
    complete_bills = session.query(Bill).filter(
        Bill.sponsor_name.is_not(None),
        Bill.introduction_date.is_not(None),
        Bill.bill_type.is_not(None)
    ).count()

    # Recent activity (last 7 days)
    week_ago = datetime.now() - timedelta(days=7)
    recent_bills = session.query(Bill).filter(
        Bill.introduction_date >= week_ago
    ).count()

    session.close()

    completeness = complete_bills / total_bills * 100

    print("=== PARLY DATA MONITORING DASHBOARD ===")
    print(f"Total Bills: {total_bills}")
    print(f"Complete Bills: {complete_bills} ({completeness:.1f}%)")
    print(f"New Bills (7 days): {recent_bills}")

    # Health status
    if completeness >= 95.0 and recent_bills >= 5:
        print("🟢 STATUS: HEALTHY")
    elif completeness >= 90.0:
        print("🟡 STATUS: WARNING")
    else:
        print("🔴 STATUS: CRITICAL")

    return completeness >= 95.0

if __name__ == "__main__":
    generate_report()
```

---

## Backup and Recovery

### Automated Database Backups

**Daily Backup Script**:
```bash
# scripts/backup_database.sh
#!/bin/bash

BACKUP_DIR="/path/to/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/parliament_$DATE.db"

# Create backup
cp data/parliament.db "$BACKUP_FILE"

# Compress
gzip "$BACKUP_FILE"

# Clean old backups (keep last 30 days)
find "$BACKUP_DIR" -name "parliament_*.db.gz" -mtime +30 -delete

echo "Backup completed: ${BACKUP_FILE}.gz"
```

**Windows Backup**:
```powershell
# scripts/backup_database.ps1
$backupDir = "C:\Users\solastic\prj\Parly\backups"
$date = Get-Date -Format "yyyyMMdd_HHmmss"
$backupFile = "$backupDir\parliament_$date.db"

# Create backup directory if it doesn't exist
if (!(Test-Path $backupDir)) {
    New-Item -ItemType Directory -Path $backupDir
}

# Copy database
Copy-Item "data\parliament.db" $backupFile

# Compress (requires 7zip or similar)
& "C:\Program Files\7-Zip\7z.exe" a "$backupFile.gz" $backupFile

# Clean up uncompressed file
Remove-Item $backupFile

# Clean old backups (keep last 30)
Get-ChildItem "$backupDir\*.db.gz" |
    Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-30) } |
    Remove-Item

Write-Host "Backup completed: $backupFile.gz"
```

### Recovery Procedures

1. **Stop all running scripts**
2. **Restore from backup**:
   ```bash
   cp backups/parliament_20231024_060000.db.gz data/
   gunzip data/parliament_20231024_060000.db.gz
   mv data/parliament_20231024_060000.db data/parliament.db
   ```
3. **Verify integrity**:
   ```bash
   python scripts/validate_data_integrity.py
   ```
4. **Restart automation**

---

## Troubleshooting

### Common Issues

**1. Script hangs or times out**
- Check internet connection
- Verify Parliament API is accessible
- Check for database locks: `fuser data/parliament.db`

**2. No new bills found**
- Parliament API may be down
- Check logs for API errors
- Verify date/time settings

**3. Database corruption**
- Restore from backup
- Run integrity check: `sqlite3 data/parliament.db "PRAGMA integrity_check;"`

**4. Permission errors**
- Ensure scripts have write access to logs/ and data/ directories
- Check virtual environment activation

### Monitoring Logs

**Key log files to monitor**:
- `logs/fetch_recent_bills.log` - Daily updates
- `logs/fill_missing_bill_data.log` - Weekly backfills
- `logs/automation.log` - Scheduler activity

**Log rotation** (add to cron):
```bash
# Rotate logs weekly, keep 4 weeks
find logs/ -name "*.log" -mtime +28 -delete
```

---

## Performance Optimization

### Database Tuning

**SQLite optimizations**:
```sql
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
PRAGMA cache_size=100000;
PRAGMA temp_store=MEMORY;
```

### Network Optimization

**Connection pooling** (already implemented):
- Reuse HTTP connections
- Respect rate limits
- Handle timeouts gracefully

### Memory Management

**Batch processing** (already implemented):
- Process in chunks of 200 bills
- Commit regularly to free memory
- Use generators for large datasets

---

## Deployment Checklist

### Pre-deployment
- [ ] All scripts tested individually
- [ ] Database backup created
- [ ] Log directories exist with proper permissions
- [ ] Virtual environment activated
- [ ] API endpoints verified accessible

### Post-deployment
- [ ] First manual run successful
- [ ] Cron jobs scheduled correctly
- [ ] Monitoring dashboard working
- [ ] Alert system configured
- [ ] Backup script running

### Maintenance Schedule
- **Daily**: Verify automation ran, check logs
- **Weekly**: Full data integrity check
- **Monthly**: Performance review, backup verification
- **Quarterly**: Complete system audit

---

This automation system ensures the Parly API remains current with Canadian parliamentary data while minimizing manual intervention and maximizing reliability.
