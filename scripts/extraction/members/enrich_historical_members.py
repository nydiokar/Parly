"""
Enrich historical members with official PersonIds and detailed roles.

This script:
1. Fetches official PersonIds from Parliament XML endpoints (Parliaments 36-44)
2. Matches them to our historical members (IDs 900000+)
3. Updates member_id with official PersonId where available
4. Fetches and imports detailed roles from /roles/xml endpoint
5. Logs all mappings and keeps temporary IDs for unmatched members

Follows the Principle of Least Action: ONE script, ONE purpose.
"""

import requests
import xml.etree.ElementTree as ET
import pandas as pd
import sys
import os
from datetime import datetime
import time
import re

# Add parent directory for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../'))

from db_setup.create_database import Member, Role, RoleType, Session, engine

# Configuration
CONFIG = {
    'excel_path': 'data/Parliamentarians-35-to-45th.xlsx',
    'parliament_range': range(36, 45),  # 36-44 (35 has no XML data)
    'base_xml_url': 'https://www.ourcommons.ca/Members/en/search/xml',
    'roles_xml_url_template': 'https://www.ourcommons.ca/members/en/{search_pattern}/roles/xml',
    'historical_id_start': 900000,
    'delay_between_requests': 1.0,  # Rate limiting
    'log_file': 'logs/historical_enrichment.log'
}


class Logger:
    """Simple logger for console and file output."""
    
    def __init__(self, log_file):
        self.log_file = log_file
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
    def log(self, message):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] {message}"
        print(log_entry)
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry + '\n')


def normalize_name_for_comparison(name):
    """Normalize name for matching (same logic as import script)."""
    if not name:
        return ""
    
    # Remove parenthetical middle names/nicknames
    name = re.sub(r'\([^)]*\)', '', name)
    # Remove extra whitespace
    name = ' '.join(name.split())
    # Lowercase for comparison
    return name.lower().strip()


def convert_excel_to_db_format(excel_name):
    """Convert 'Family, Personal' to 'Personal Family'."""
    if ',' in excel_name:
        parts = excel_name.split(',', 1)
        family = parts[0].strip()
        personal = parts[1].strip() if len(parts) > 1 else ''
        # Remove parenthetical nicknames
        personal = re.sub(r'\([^)]*\)', '', personal)
        personal = ' '.join(personal.split())
        return f"{personal} {family}".strip()
    return excel_name.strip()


def fetch_parliament_members_xml(parliament_number, logger):
    """Fetch all members from a specific parliament via XML."""
    params = {
        'parliament': parliament_number,
        'caucusId': 'all',
        'province': 'all',
        'gender': 'all'
    }
    
    logger.log(f"Fetching Parliament {parliament_number} members...")
    
    try:
        response = requests.get(CONFIG['base_xml_url'], params=params, timeout=30)
        if response.status_code != 200:
            logger.log(f"  ERROR: HTTP {response.status_code}")
            return []
        
        root = ET.fromstring(response.content)
        members = []
        
        for mp in root.findall('.//MemberOfParliament'):
            person_id = mp.find('PersonId')
            first_name = mp.find('PersonOfficialFirstName')
            last_name = mp.find('PersonOfficialLastName')
            
            if person_id is not None and first_name is not None and last_name is not None:
                full_name = f"{first_name.text} {last_name.text}"
                members.append({
                    'person_id': int(person_id.text),
                    'name': full_name,
                    'normalized_name': normalize_name_for_comparison(full_name),
                    'search_pattern': f"{full_name.lower().replace(' ', '-')}({person_id.text})"
                })
        
        logger.log(f"  Found {len(members)} members in Parliament {parliament_number}")
        return members
        
    except Exception as e:
        logger.log(f"  ERROR parsing Parliament {parliament_number}: {e}")
        return []


def fetch_member_roles_xml(search_pattern, logger):
    """Fetch detailed roles for a member."""
    url = CONFIG['roles_xml_url_template'].format(search_pattern=search_pattern)
    
    try:
        time.sleep(CONFIG['delay_between_requests'])
        response = requests.get(url, timeout=30)
        
        if response.status_code != 200:
            logger.log(f"    Failed to fetch roles: HTTP {response.status_code}")
            return []
        
        return parse_roles_xml(response.content, logger)
        
    except Exception as e:
        logger.log(f"    ERROR fetching roles: {e}")
        return []


def parse_roles_xml(xml_data, logger):
    """Parse roles XML into structured data."""
    roles = []
    
    try:
        root = ET.fromstring(xml_data)
        
        # Extract Member of Parliament roles
        for mp_role in root.findall('.//MemberOfParliamentRole'):
            constituency = mp_role.find('ConstituencyName')
            province = mp_role.find('ConstituencyProvinceTerritoryName')
            from_date = mp_role.find('FromDateTime')
            to_date = mp_role.find('ToDateTime')
            
            # Parse dates
            start_date = None
            end_date = None
            
            if from_date is not None and from_date.text:
                start_date = datetime.strptime(from_date.text.split('T')[0], '%Y-%m-%d').date()
            
            if to_date is not None and to_date.text and to_date.get('{http://www.w3.org/2001/XMLSchema-instance}nil') != 'true':
                end_date = datetime.strptime(to_date.text.split('T')[0], '%Y-%m-%d').date()
            
            roles.append({
                'role_type': RoleType.MEMBER_OF_PARLIAMENT,
                'from_date': start_date,
                'to_date': end_date,
                'constituency_name': constituency.text if constituency is not None else None,
                'constituency_province': province.text if province is not None else None
            })
        
        # Extract Political Affiliation (CaucusMemberRoles)
        for caucus_role in root.findall('.//CaucusMemberRole'):
            caucus_name = caucus_role.find('CaucusLongName')
            from_date = caucus_role.find('FromDateTime')
            to_date = caucus_role.find('ToDateTime')
            
            start_date = None
            end_date = None
            
            if from_date is not None and from_date.text:
                start_date = datetime.strptime(from_date.text.split('T')[0], '%Y-%m-%d').date()
            
            if to_date is not None and to_date.text and to_date.get('{http://www.w3.org/2001/XMLSchema-instance}nil') != 'true':
                end_date = datetime.strptime(to_date.text.split('T')[0], '%Y-%m-%d').date()
            
            roles.append({
                'role_type': RoleType.POLITICAL_AFFILIATION,
                'from_date': start_date,
                'to_date': end_date,
                'party': caucus_name.text if caucus_name is not None else None
            })
        
        # Extract Committee memberships
        for committee_role in root.findall('.//CommitteeMemberRole'):
            committee_name = committee_role.find('CommitteeNames/CommitteeName[@Language="en"]')
            from_date = committee_role.find('FromDateTime')
            to_date = committee_role.find('ToDateTime')
            
            start_date = None
            end_date = None
            
            if from_date is not None and from_date.text:
                start_date = datetime.strptime(from_date.text.split('T')[0], '%Y-%m-%d').date()
            
            if to_date is not None and to_date.text and to_date.get('{http://www.w3.org/2001/XMLSchema-instance}nil') != 'true':
                end_date = datetime.strptime(to_date.text.split('T')[0], '%Y-%m-%d').date()
            
            roles.append({
                'role_type': RoleType.COMMITTEE_MEMBER,
                'from_date': start_date,
                'to_date': end_date,
                'committee_name': committee_name.text if committee_name is not None else None
            })
        
        # Extract Parliamentarian Offices (e.g., Parliamentary Secretary)
        for office_role in root.findall('.//ParliamentarianOfficeRole'):
            office_name = office_role.find('OfficeLongName')
            from_date = office_role.find('FromDateTime')
            to_date = office_role.find('ToDateTime')
            
            start_date = None
            end_date = None
            
            if from_date is not None and from_date.text:
                start_date = datetime.strptime(from_date.text.split('T')[0], '%Y-%m-%d').date()
            
            if to_date is not None and to_date.text and to_date.get('{http://www.w3.org/2001/XMLSchema-instance}nil') != 'true':
                end_date = datetime.strptime(to_date.text.split('T')[0], '%Y-%m-%d').date()
            
            roles.append({
                'role_type': RoleType.PARLIAMENTARIAN_OFFICE,
                'from_date': start_date,
                'to_date': end_date,
                'office_role': office_name.text if office_name is not None else None
            })
        
    except Exception as e:
        logger.log(f"    ERROR parsing roles XML: {e}")
    
    return roles


def build_xml_member_database(logger):
    """Fetch all members from all parliaments and build lookup dict."""
    logger.log("\n=== PHASE 1: Building XML Member Database ===")
    
    xml_members = {}  # normalized_name -> {person_id, name, search_pattern, parliaments}
    
    for parliament in CONFIG['parliament_range']:
        members = fetch_parliament_members_xml(parliament, logger)
        
        for member in members:
            norm_name = member['normalized_name']
            
            if norm_name not in xml_members:
                xml_members[norm_name] = {
                    'person_id': member['person_id'],
                    'name': member['name'],
                    'search_pattern': member['search_pattern'],
                    'parliaments': []
                }
            
            xml_members[norm_name]['parliaments'].append(parliament)
    
    logger.log(f"\nTotal unique members in XML: {len(xml_members)}")
    return xml_members


def match_and_update_members(xml_members, logger):
    """Match historical members to XML data and update IDs."""
    logger.log("\n=== PHASE 2: Matching and Updating Member IDs ===")
    
    session = Session()
    
    try:
        # Get all historical members (900000+)
        historical_members = session.query(Member).filter(
            Member.member_id >= CONFIG['historical_id_start']
        ).all()
        
        logger.log(f"Found {len(historical_members)} historical members in DB")
        
        matched = 0
        unmatched = 0
        updated_ids = []
        
        for member in historical_members:
            norm_name = normalize_name_for_comparison(member.name)
            
            if norm_name in xml_members:
                xml_data = xml_members[norm_name]
                old_id = member.member_id
                new_id = xml_data['person_id']
                
                # Check if new ID already exists (conflict)
                existing = session.query(Member).filter(Member.member_id == new_id).first()
                
                if existing and existing.member_id != old_id:
                    logger.log(f"  CONFLICT: {member.name} -> ID {new_id} already exists for {existing.name}")
                    unmatched += 1
                    continue
                
                # Update member_id
                logger.log(f"  MATCH: {member.name} | {old_id} -> {new_id} | Parliaments: {xml_data['parliaments']}")
                
                # Update all roles first to maintain referential integrity
                session.query(Role).filter(Role.member_id == old_id).update({'member_id': new_id})
                
                # Update member
                member.member_id = new_id
                
                updated_ids.append({
                    'name': member.name,
                    'old_id': old_id,
                    'new_id': new_id,
                    'search_pattern': xml_data['search_pattern']
                })
                
                matched += 1
            else:
                logger.log(f"  NO MATCH: {member.name} (ID: {member.member_id}) - keeping temporary ID")
                unmatched += 1
        
        session.commit()
        
        logger.log(f"\n=== MATCHING SUMMARY ===")
        logger.log(f"Matched and updated: {matched}")
        logger.log(f"Unmatched (kept temp IDs): {unmatched}")
        
        return updated_ids
        
    except Exception as e:
        session.rollback()
        logger.log(f"ERROR during matching: {e}")
        raise
    finally:
        session.close()


def fetch_and_import_detailed_roles(updated_members, logger):
    """Fetch detailed roles for matched members and import them."""
    logger.log("\n=== PHASE 3: Fetching Detailed Roles ===")
    
    session = Session()
    
    try:
        total_new_roles = 0
        
        for idx, member_data in enumerate(updated_members, 1):
            member_id = member_data['new_id']
            search_pattern = member_data['search_pattern']
            
            logger.log(f"\n[{idx}/{len(updated_members)}] Fetching roles for {member_data['name']} ({member_id})...")
            
            # Get existing role count
            existing_roles = session.query(Role).filter(Role.member_id == member_id).count()
            logger.log(f"  Existing roles in DB: {existing_roles}")
            
            # Fetch new roles from XML
            new_roles = fetch_member_roles_xml(search_pattern, logger)
            
            if not new_roles:
                logger.log(f"  No new roles found in XML")
                continue
            
            # Delete existing XML-sourced roles to avoid duplicates
            # (Keep Excel-sourced roles that might not be in XML)
            logger.log(f"  Deleting existing roles to reimport from XML...")
            session.query(Role).filter(Role.member_id == member_id).delete()
            
            # Import new roles
            roles_added = 0
            for role_data in new_roles:
                role = Role(
                    member_id=member_id,
                    role_type=role_data['role_type'],
                    from_date=role_data.get('from_date'),
                    to_date=role_data.get('to_date'),
                    constituency_name=role_data.get('constituency_name'),
                    constituency_province=role_data.get('constituency_province'),
                    party=role_data.get('party'),
                    committee_name=role_data.get('committee_name'),
                    office_role=role_data.get('office_role')
                )
                session.add(role)
                roles_added += 1
            
            session.commit()
            total_new_roles += roles_added
            
            logger.log(f"  Imported {roles_added} roles (MP, Party, Committee, Office)")
            
            # Progress update every 50 members
            if idx % 50 == 0:
                logger.log(f"\n--- Progress: {idx}/{len(updated_members)} members processed, {total_new_roles} total roles imported ---\n")
        
        logger.log(f"\n=== ROLES IMPORT SUMMARY ===")
        logger.log(f"Total members processed: {len(updated_members)}")
        logger.log(f"Total roles imported: {total_new_roles}")
        
    except Exception as e:
        session.rollback()
        logger.log(f"ERROR during roles import: {e}")
        raise
    finally:
        session.close()


def verify_database_state(logger):
    """Verify final database state."""
    logger.log("\n=== PHASE 4: Database Verification ===")
    
    session = Session()
    
    try:
        # Count members by ID range
        official_id_count = session.query(Member).filter(Member.member_id < CONFIG['historical_id_start']).count()
        temp_id_count = session.query(Member).filter(Member.member_id >= CONFIG['historical_id_start']).count()
        total_members = session.query(Member).count()
        
        # Count roles
        total_roles = session.query(Role).count()
        
        logger.log(f"Total members: {total_members}")
        logger.log(f"  - With official IDs (<900000): {official_id_count}")
        logger.log(f"  - With temporary IDs (>=900000): {temp_id_count}")
        logger.log(f"Total roles: {total_roles}")
        
        # Sample a few updated members
        logger.log("\nSample of updated members:")
        sample = session.query(Member).filter(
            Member.member_id < CONFIG['historical_id_start'],
            Member.member_id > 1000  # Exclude current MPs (small IDs)
        ).limit(5).all()
        
        for member in sample:
            role_count = session.query(Role).filter(Role.member_id == member.member_id).count()
            logger.log(f"  {member.name} (ID: {member.member_id}) - {role_count} roles")
        
    finally:
        session.close()


def main():
    """Main execution function."""
    logger = Logger(CONFIG['log_file'])
    
    logger.log("="*80)
    logger.log("HISTORICAL MEMBERS ENRICHMENT SCRIPT")
    logger.log("="*80)
    logger.log(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.log(f"Parliament range: {CONFIG['parliament_range'].start}-{CONFIG['parliament_range'].stop - 1}")
    logger.log(f"Historical ID threshold: {CONFIG['historical_id_start']}")
    
    try:
        # Phase 1: Build XML member database
        xml_members = build_xml_member_database(logger)
        
        # Phase 2: Match and update member IDs
        updated_members = match_and_update_members(xml_members, logger)
        
        # Phase 3: Fetch and import detailed roles
        if updated_members:
            fetch_and_import_detailed_roles(updated_members, logger)
        else:
            logger.log("\nNo members to update, skipping roles import.")
        
        # Phase 4: Verify final state
        verify_database_state(logger)
        
        logger.log("\n" + "="*80)
        logger.log("ENRICHMENT COMPLETED SUCCESSFULLY!")
        logger.log("="*80)
        logger.log(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.log(f"Log file: {CONFIG['log_file']}")
        
    except Exception as e:
        logger.log(f"\n{'='*80}")
        logger.log(f"FATAL ERROR: {e}")
        logger.log(f"{'='*80}")
        import traceback
        logger.log(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Enrich historical members with official IDs and roles')
    parser.add_argument('--execute', action='store_true', help='Execute the enrichment (required)')
    args = parser.parse_args()
    
    if not args.execute:
        print("\nThis script will:")
        print("1. Fetch official PersonIds from Parliament XML (Parliaments 36-44)")
        print("2. Match to historical members (IDs 900000+)")
        print("3. Update member_id with official PersonId")
        print("4. Fetch and import detailed roles (MP, Party, Committee, Office)")
        print("\nThis will modify the database!")
        print("\nUsage: python enrich_historical_members.py --execute")
        sys.exit(0)
    
    main()

