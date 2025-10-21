#!/usr/bin/env python3
"""
DATABASE INSPECTOR
==================
WHAT IT DOES: Lists all database tables and checks parliamentary_associations table
USAGE: python scripts/inspect_database.py
OUTPUT: Table list with record counts, parliamentary_associations status
"""

import sqlite3

conn = sqlite3.connect('data/parliament.db')
cursor = conn.cursor()

# Check all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print('All tables:', [t[0] for t in tables])

# Check parliamentary_associations specifically
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='parliamentary_associations'")
result = cursor.fetchone()
if result:
    cursor.execute('SELECT COUNT(*) FROM parliamentary_associations')
    count = cursor.fetchone()[0]
    print(f'parliamentary_associations table exists with {count} records')
else:
    print('parliamentary_associations table does not exist')

conn.close()
