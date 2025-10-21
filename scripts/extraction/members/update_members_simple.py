"""
Simple incremental member updater.

Uses the PROVEN working pattern:
1. Fetch member list XML from parliament website
2. Compare against database
3. Use existing scrape_roles.py logic for missing members
4. Insert directly to database
"""

import requests
import xml.etree.ElementTree as ET
import sys
import os
import time

# Add parent directory for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from db_setup.create_database import Member, Role, RoleType, Session
from scripts.extraction.scrape_roles import fetch_member_roles_xml, parse_roles_xml


def fetch_current_member_list_xml():
    """Fetch current member list from XML endpoint."""
    url = "https://www.ourcommons.ca/Members/en/search/xml"
    print(f"Fetching member list from: {url}")

    response = requests.get(url)
    if response.status_code != 200:
        print(f"Failed to fetch. Status: {response.status_code}")
        return []

    try:
        root = ET.fromstring(response.content)
        members = []

        # Find all members in XML
        for mp in root.findall('.//MemberOfParliament'):
            person_id = mp.find('PersonId')
            first_name = mp.find('PersonOfficialFirstName')
            last_name = mp.find('PersonOfficialLastName')

            if person_id is not None:
                member_id = int(person_id.text)

                # Build name and search pattern
                if first_name is not None and last_name is not None:
                    full_name = f"{first_name.text} {last_name.text}"
                    name_lower = full_name.lower().replace(' ', '-')
                    search_pattern = f"{name_lower}({member_id})"

                    members.append({
                        'id': member_id,
                        'name': full_name,
                        'search_pattern': search_pattern
                    })

        print(f"Found {len(members)} members")
        return members

    except Exception as e:
        print(f"Error parsing XML: {e}")
        return []


def get_db_member_ids(session):
    """Get set of member IDs already in database."""
    ids = set()
    for (member_id,) in session.query(Member.member_id).all():
        ids.add(member_id)
    print(f"Database has {len(ids)} members")
    return ids


def insert_member_and_roles(session, member_data):
    """Insert a new member and their roles into database."""
    member_id = member_data['id']
    member_name = member_data['name']
    search_pattern = member_data['search_pattern']

    print(f"\n  Processing: {member_name} (ID: {member_id})")

    # Create member record
    member = Member(member_id=member_id, name=member_name)
    session.add(member)

    # Fetch roles XML (using proven working function)
    xml_data = fetch_member_roles_xml(search_pattern)
    if not xml_data:
        print(f"  WARNING: Failed to fetch roles XML")
        return 0

    # Parse roles (using proven working function)
    parsed_name, roles_data = parse_roles_xml(xml_data)

    if not roles_data:
        print(f"  WARNING: No roles found")
        return 0

    # Convert role dicts to Role objects and insert
    roles_added = 0
    for role_dict in roles_data:
        # Map role type string to enum
        role_type_str = role_dict['role_type'].replace(' ', '_').upper()
        if role_type_str not in RoleType.__members__:
            continue

        # Parse dates
        from datetime import datetime
        def parse_date(date_str):
            if not date_str:
                return None
            try:
                return datetime.fromisoformat(date_str).date() if date_str else None
            except:
                return None

        from_date = parse_date(role_dict.get('start_date') or role_dict.get('date'))
        to_date = parse_date(role_dict.get('end_date')) if role_dict.get('end_date') else None

        # Create Role object
        role = Role(
            member_id=member_id,
            role_type=RoleType[role_type_str],
            from_date=from_date,
            to_date=to_date,
            parliament_number=role_dict.get('parliament_number'),
            session_number=role_dict.get('parliament_session'),
            constituency_name=role_dict.get('constituency'),
            constituency_province=role_dict.get('province'),
            party=role_dict.get('affiliation'),
            committee_name=role_dict.get('committee_name'),
            affiliation_role_name=role_dict.get('role_name'),
            organization_name=role_dict.get('organization_name'),
            office_role=role_dict.get('office_role'),
            election_result=role_dict.get('result')
        )

        # Check for duplicates
        existing = session.query(Role).filter_by(
            member_id=member_id,
            role_type=role.role_type,
            from_date=from_date,
            parliament_number=role_dict.get('parliament_number'),
            session_number=role_dict.get('parliament_session')
        ).first()

        if not existing:
            session.add(role)
            roles_added += 1

    # Update member info from roles
    mp_roles = [r for r in roles_data if r['role_type'] == 'Member of Parliament' and r.get('start_date')]
    if mp_roles:
        mp_roles.sort(key=lambda x: x.get('start_date', ''), reverse=True)
        latest = mp_roles[0]
        member.constituency = latest.get('constituency')
        member.province_name = latest.get('province')

    party_roles = [r for r in roles_data if r['role_type'] == 'Political Affiliation' and r.get('start_date')]
    if party_roles:
        party_roles.sort(key=lambda x: x.get('start_date', ''), reverse=True)
        member.party = party_roles[0].get('affiliation')

    print(f"  Added {roles_added} roles")
    return roles_added


def main():
    print("="*60)
    print("INCREMENTAL MEMBER UPDATE")
    print("="*60)

    session = Session()

    try:
        # Step 1: Get current members from website
        website_members = fetch_current_member_list_xml()
        if not website_members:
            print("ERROR: Failed to fetch members from website")
            return

        # Step 2: Get existing members from database
        db_member_ids = get_db_member_ids(session)

        # Step 3: Find missing members
        website_ids = {m['id'] for m in website_members}
        missing_ids = website_ids - db_member_ids

        print(f"\nComparison:")
        print(f"  Website: {len(website_ids)} members")
        print(f"  Database: {len(db_member_ids)} members")
        print(f"  Missing: {len(missing_ids)} members")

        if not missing_ids:
            print("\nDatabase is up to date!")
            return

        # Step 4: Process missing members
        print(f"\nAdding {len(missing_ids)} new members...")

        new_members = 0
        new_roles = 0

        for member_data in website_members:
            if member_data['id'] in missing_ids:
                roles_added = insert_member_and_roles(session, member_data)
                if roles_added > 0:
                    new_members += 1
                    new_roles += roles_added
                    session.commit()  # Commit after each member

        print("\n" + "="*60)
        print("UPDATE COMPLETE")
        print("="*60)
        print(f"  New members: {new_members}")
        print(f"  New roles: {new_roles}")
        print(f"  Total in DB: {len(db_member_ids) + new_members}")

    except Exception as e:
        session.rollback()
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()


if __name__ == "__main__":
    main()
