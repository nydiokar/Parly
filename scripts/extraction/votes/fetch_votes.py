"""
Incremental votes extractor for Canadian Parliament.

Follows the PROVEN pattern from update_members_simple.py:
1. Fetch all members from database (with their search patterns)
2. For each member, fetch their votes XML
3. Parse votes and check against existing votes in database
4. Insert only new votes (incremental, duplicate-safe)
5. Commit per member for reliability
"""

import requests
import xml.etree.ElementTree as ET
import sys
import os
import time
from datetime import datetime

# Add parent directories for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../'))

from db_setup.create_database import Member, Vote, Session
from db_setup.url_templates import URL_TEMPLATES


def fetch_member_votes_xml(search_pattern):
    """
    Fetch votes XML for a member using their search pattern.

    Args:
        search_pattern: Format like "justin-trudeau(25645)"

    Returns:
        XML content as bytes, or None if failed
    """
    url = URL_TEMPLATES['member_votes'].format(search_pattern=search_pattern)

    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.content
        else:
            print(f"    WARNING: HTTP {response.status_code} for {search_pattern}")
            return None
    except Exception as e:
        print(f"    ERROR: {e}")
        return None


def parse_votes_xml(xml_data, member_id):
    """
    Parse votes XML and return list of vote dictionaries.

    Args:
        xml_data: Raw XML bytes from ourcommons.ca
        member_id: The member's ID for linking votes

    Returns:
        List of vote dictionaries ready for database insertion
    """
    try:
        root = ET.fromstring(xml_data)
        votes = []

        for member_vote in root.findall('MemberVote'):
            # Extract all fields (using .text and handling None)
            parliament_num = member_vote.find('ParliamentNumber')
            session_num = member_vote.find('SessionNumber')
            decision_date = member_vote.find('DecisionEventDateTime')
            subject = member_vote.find('DecisionDivisionSubject')
            result = member_vote.find('DecisionResultName')
            vote_value = member_vote.find('VoteValueName')

            # Skip if missing critical fields
            if not all([parliament_num is not None, session_num is not None,
                       decision_date is not None, vote_value is not None]):
                continue

            # Parse date (format: 2022-03-15T19:30:00)
            try:
                vote_date = datetime.fromisoformat(decision_date.text.split('T')[0]).date()
            except:
                continue  # Skip votes with invalid dates

            # Get subject text (can be long, split into topic and full subject)
            subject_text = subject.text if subject is not None else "Unknown"
            vote_topic = subject_text[:255] if len(subject_text) > 255 else subject_text

            vote_dict = {
                'member_id': member_id,
                'parliament_number': int(parliament_num.text),
                'session_number': int(session_num.text),
                'vote_date': vote_date,
                'vote_topic': vote_topic,
                'subject': subject_text,
                'vote_result': result.text if result is not None else "Unknown",
                'member_vote': vote_value.text
            }

            votes.append(vote_dict)

        return votes

    except Exception as e:
        print(f"    ERROR parsing XML: {e}")
        return []


def get_all_members_from_db(session):
    """
    Get all members from database with their search patterns.

    Returns:
        List of dicts: [{'id': 123, 'name': 'John Doe', 'search_pattern': 'john-doe(123)'}, ...]
    """
    members = []

    for member in session.query(Member).all():
        # Build search pattern (name-lowercase with dashes + id)
        name_lower = member.name.lower().replace(' ', '-')
        search_pattern = f"{name_lower}({member.member_id})"

        members.append({
            'id': member.member_id,
            'name': member.name,
            'search_pattern': search_pattern
        })

    return members


def get_existing_vote_signatures(session, member_id):
    """
    Get set of vote signatures already in database for this member.

    Signature format: (parliament_number, session_number, vote_date, vote_topic)
    This uniquely identifies a vote for duplicate checking.
    """
    signatures = set()

    votes = session.query(Vote).filter_by(member_id=member_id).all()
    for vote in votes:
        sig = (vote.parliament_number, vote.session_number,
               vote.vote_date, vote.vote_topic)
        signatures.add(sig)

    return signatures


def insert_votes_for_member(session, member_data):
    """
    Fetch and insert votes for a single member (incremental, duplicate-safe).

    Args:
        session: SQLAlchemy session
        member_data: Dict with 'id', 'name', 'search_pattern'

    Returns:
        Number of new votes inserted
    """
    member_id = member_data['id']
    member_name = member_data['name']
    search_pattern = member_data['search_pattern']

    # Fetch votes XML
    xml_data = fetch_member_votes_xml(search_pattern)
    if not xml_data:
        return 0

    # Parse votes
    votes_data = parse_votes_xml(xml_data, member_id)
    if not votes_data:
        return 0

    # Get existing votes to avoid duplicates
    existing_sigs = get_existing_vote_signatures(session, member_id)

    # Insert only new votes
    new_votes = 0
    for vote_dict in votes_data:
        # Create signature for duplicate check
        sig = (vote_dict['parliament_number'], vote_dict['session_number'],
               vote_dict['vote_date'], vote_dict['vote_topic'])

        if sig not in existing_sigs:
            vote = Vote(**vote_dict)
            session.add(vote)
            new_votes += 1

    return new_votes


def main():
    """Main execution: fetch votes for all members incrementally."""
    print("="*70)
    print("INCREMENTAL VOTES EXTRACTION")
    print("="*70)

    session = Session()

    try:
        # Step 1: Get all members from database
        print("\nFetching all members from database...")
        members = get_all_members_from_db(session)
        print(f"Found {len(members)} members")

        if not members:
            print("ERROR: No members in database. Run member scrapers first.")
            return

        # Step 2: Process each member
        print(f"\nProcessing votes for {len(members)} members...")
        print("(This will take a while - ~2 seconds per member)")

        total_new_votes = 0
        members_with_votes = 0
        errors = 0

        for i, member_data in enumerate(members, 1):
            member_name = member_data['name']

            print(f"\n[{i}/{len(members)}] {member_name}")

            try:
                new_votes = insert_votes_for_member(session, member_data)

                if new_votes > 0:
                    session.commit()  # Commit per member for safety
                    total_new_votes += new_votes
                    members_with_votes += 1
                    print(f"    Added {new_votes} new votes")
                else:
                    print(f"    No new votes (already up to date)")

                # Rate limiting: 2 seconds between requests
                time.sleep(2)

            except Exception as e:
                session.rollback()
                errors += 1
                print(f"    ERROR: {e}")
                continue

        # Step 3: Summary
        print("\n" + "="*70)
        print("EXTRACTION COMPLETE")
        print("="*70)
        print(f"  Members processed: {len(members)}")
        print(f"  Members with new votes: {members_with_votes}")
        print(f"  Total new votes inserted: {total_new_votes}")
        print(f"  Errors: {errors}")

        # Get final vote count
        total_votes = session.query(Vote).count()
        print(f"\n  Total votes in database: {total_votes}")

    except Exception as e:
        session.rollback()
        print(f"\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()


if __name__ == "__main__":
    main()
