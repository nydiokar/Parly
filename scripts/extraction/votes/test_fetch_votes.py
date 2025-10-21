"""
TEST VERSION: Only process first 3 members to verify the scraper works.
"""

import sys
import os

# Add parent directories for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../'))

from scripts.extraction.votes.fetch_votes import (
    get_all_members_from_db,
    insert_votes_for_member,
    Session
)
import time


def main():
    """Test with just 3 members."""
    print("="*70)
    print("TEST: VOTES EXTRACTION (First 3 Members Only)")
    print("="*70)

    session = Session()

    try:
        # Get all members
        print("\nFetching all members from database...")
        members = get_all_members_from_db(session)
        print(f"Found {len(members)} members")

        # Test with first 3 only
        test_members = members[:3]
        print(f"\nTesting with first {len(test_members)} members:")
        for m in test_members:
            print(f"  - {m['name']} (ID: {m['id']})")

        # Process each test member
        total_new_votes = 0

        for i, member_data in enumerate(test_members, 1):
            member_name = member_data['name']

            print(f"\n[{i}/{len(test_members)}] {member_name}")

            try:
                new_votes = insert_votes_for_member(session, member_data)

                if new_votes > 0:
                    session.commit()
                    total_new_votes += new_votes
                    print(f"    [OK] Added {new_votes} new votes")
                else:
                    print(f"    [INFO] No new votes (already up to date)")

                # Rate limiting
                time.sleep(2)

            except Exception as e:
                session.rollback()
                print(f"    [ERROR] {e}")
                import traceback
                traceback.print_exc()
                continue

        # Summary
        print("\n" + "="*70)
        print("TEST COMPLETE")
        print("="*70)
        print(f"  Total new votes inserted: {total_new_votes}")

        if total_new_votes > 0:
            print("\n[SUCCESS] The scraper is working correctly!")
            print("  You can now run the full scraper:")
            print("  python scripts/extraction/votes/fetch_votes.py")
        else:
            print("\n[INFO] No votes were added.")
            print("  This could mean:")
            print("  - These members have no votes")
            print("  - Votes were already fetched previously")
            print("  - There was an issue with the XML parsing")

    except Exception as e:
        session.rollback()
        print(f"\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()


if __name__ == "__main__":
    main()
