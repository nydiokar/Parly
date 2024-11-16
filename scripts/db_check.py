import sqlite3
import json
from datetime import datetime

# Constants
DB_PATH = 'data/parliament.db'
JSON_PATH = 'data/member_roles.json'

def parse_date(date_string):
    """Parse date from string to datetime object."""
    try:
        return datetime.strptime(date_string, '%A, %B %d, %Y').date() if date_string else None
    except ValueError:
        return None

def compare_databases():
    """Compare JSON data with SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Get total counts from database
        cursor.execute("SELECT COUNT(*) FROM roles")
        total_db_roles = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT member_id) FROM roles")
        total_db_members = cursor.fetchone()[0]
        
        # Get role type counts from database
        cursor.execute("""
            SELECT role_type, COUNT(*) as count 
            FROM roles 
            GROUP BY role_type 
            ORDER BY count DESC
        """)
        db_role_types = cursor.fetchall()

        # Load JSON file and get counts
        with open(JSON_PATH, 'r') as file:
            json_data = json.load(file)
        
        total_json_members = len(json_data)
        total_json_roles = sum(len(member['roles']) for member in json_data)
        
        # Count role types in JSON
        json_role_types = {}
        for member in json_data:
            for role in member['roles']:
                role_type = role['role_type'].replace(' ', '_').upper()
                json_role_types[role_type] = json_role_types.get(role_type, 0) + 1

        # Print summary
        print("\nDatabase Summary:")
        print(f"Total Members in DB: {total_db_members}")
        print(f"Total Roles in DB: {total_db_roles}")
        print("\nRole Types in DB:")
        for role_type, count in db_role_types:
            print(f"  {role_type}: {count}")
        
        print("\nJSON Summary:")
        print(f"Total Members in JSON: {total_json_members}")
        print(f"Total Roles in JSON: {total_json_roles}")
        print("\nRole Types in JSON:")
        for role_type, count in sorted(json_role_types.items(), key=lambda x: x[1], reverse=True):
            print(f"  {role_type}: {count}")
        
        # Calculate match percentage
        match_percentage = min(total_db_roles, total_json_roles) / max(total_db_roles, total_json_roles) * 100
        
        print(f"\nMatch Percentage: {match_percentage:.2f}%")

    except Exception as e:
        print(f"An error occurred: {str(e)}")
    finally:
        conn.close()

if __name__ == "__main__":
    compare_databases()