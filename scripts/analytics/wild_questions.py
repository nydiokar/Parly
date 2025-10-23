"""
Wild Questions - Mining data with human curiosity, not analyst logic

Questions a human would actually want to know:
- Who votes drunk? (late night votes)
- Do they work harder before elections?
- Which MPs are secretly friends? (cross-party voting)
- Do they copy each other's homework? (similar bill titles)
- Weekend warriors or Monday slackers?
- Which MPs sponsor bills they vote against?
- The laziest parliament ever?
- Bills that almost made it (died at last stage)
- MPs who changed their entire political identity
"""

from db_setup.create_database import Session, Bill, Vote, Member, Role
from sqlalchemy import func, and_, or_, distinct
from collections import Counter, defaultdict
from datetime import datetime
import re

def find_late_night_votes(session):
    """Do they vote differently late at night? (Proxy: end of session urgency)"""
    print("\n" + "="*70)
    print("LATE NIGHT CHAOS - Last-Minute Voting Patterns")
    print("="*70)

    # Get votes by date, look for clustering at end of sessions
    votes_by_date = session.query(
        func.date(Vote.vote_date).label('date'),
        func.count(Vote.vote_id).label('count')
    ).group_by(func.date(Vote.vote_date)).order_by(func.count(Vote.vote_id).desc()).limit(20).all()

    print("\nBusiest voting days (marathon sessions):")
    print(f"{'Date':<20} {'Votes Cast':<15}")
    print("-" * 70)

    for date, count in votes_by_date:
        print(f"{str(date):<20} {count:>10}")

    return votes_by_date

def find_election_panic(session):
    """Do they actually work harder before elections?"""
    print("\n" + "="*70)
    print("ELECTION PANIC - Do They Work Harder When Jobs Are On The Line?")
    print("="*70)

    # Known election years: 1997, 2000, 2004, 2006, 2008, 2011, 2015, 2019, 2021
    election_years = [1997, 2000, 2004, 2006, 2008, 2011, 2015, 2019, 2021]

    bills_by_year = defaultdict(int)
    for bill in session.query(Bill).all():
        # Estimate year from parliament number (rough approximation)
        year = 1993 + (bill.parliament_number - 35) * 3
        bills_by_year[year] += 1

    print("\nBills introduced in election years vs. regular years:")
    print(f"{'Year Type':<25} {'Avg Bills':<15}")
    print("-" * 70)

    election_years_bills = [bills_by_year.get(y, 0) for y in election_years if y in bills_by_year]
    regular_years_bills = [count for year, count in bills_by_year.items() if year not in election_years]

    if election_years_bills and regular_years_bills:
        avg_election = sum(election_years_bills) / len(election_years_bills)
        avg_regular = sum(regular_years_bills) / len(regular_years_bills)

        print(f"{'Election Years':<25} {avg_election:>10.1f}")
        print(f"{'Regular Years':<25} {avg_regular:>10.1f}")
        print(f"\nDifference: {((avg_election - avg_regular) / avg_regular * 100):+.1f}%")

def find_unlikely_friendships(session):
    """Which MPs from different parties vote together most?"""
    print("\n" + "="*70)
    print("UNLIKELY FRIENDSHIPS - Cross-Party Voting Buddies")
    print("="*70)

    # Get voting patterns
    members_with_votes = (
        session.query(Member.member_id, Member.name, Member.party)
        .join(Vote)
        .group_by(Member.member_id)
        .having(func.count(Vote.vote_id) > 50)  # At least 50 votes
        .limit(100)  # Sample to keep it fast
        .all()
    )

    print(f"\nAnalyzing {len(members_with_votes)} active MPs...")

    # Compare voting patterns between different parties
    # (Simplified - just count same votes on same topics)
    similarities = []

    for i, (id1, name1, party1) in enumerate(members_with_votes[:20]):  # Sample
        for id2, name2, party2 in members_with_votes[i+1:20]:
            if party1 != party2 and party1 and party2:  # Different parties
                # Get common votes
                common_votes = session.query(Vote).filter(
                    and_(
                        Vote.member_id == id1,
                        Vote.vote_topic.in_(
                            session.query(Vote.vote_topic).filter(Vote.member_id == id2)
                        )
                    )
                ).count()

                if common_votes > 10:
                    similarities.append((name1, party1, name2, party2, common_votes))

    similarities.sort(key=lambda x: x[4], reverse=True)

    print("\nTop cross-party voting pairs:")
    print(f"{'MP 1':<25} {'Party':<15} {'MP 2':<25} {'Party':<15} {'Common Votes':<15}")
    print("-" * 100)

    for name1, party1, name2, party2, common in similarities[:5]:
        print(f"{name1[:24]:<25} {party1[:14]:<15} {name2[:24]:<25} {party2[:14]:<15} {common:<15}")

def find_bill_copycats(session):
    """Do MPs copy each other's bills? Similar titles/topics"""
    print("\n" + "="*70)
    print("COPYCAT BILLS - Who's Copying Homework?")
    print("="*70)

    # Find bills with very similar titles
    bills = session.query(Bill.bill_number, Bill.short_title, Member.name, Bill.parliament_number).join(
        Member, Bill.sponsor_id == Member.member_id, isouter=True
    ).filter(Bill.short_title.isnot(None)).all()

    # Simple similarity: shared significant words
    def get_keywords(title):
        if not title:
            return set()
        words = title.lower().split()
        # Remove common words
        stopwords = {'an', 'act', 'to', 'the', 'and', 'of', 'for', 'in', 'on', 'at', 'amend'}
        return set(w for w in words if len(w) > 4 and w not in stopwords)

    similar_pairs = []
    for i, (num1, title1, sponsor1, parl1) in enumerate(bills[:200]):
        keywords1 = get_keywords(title1)
        if len(keywords1) < 2:
            continue

        for num2, title2, sponsor2, parl2 in bills[i+1:200]:
            keywords2 = get_keywords(title2)
            if len(keywords2) < 2:
                continue

            overlap = keywords1 & keywords2
            if len(overlap) >= 2 and num1 != num2:  # At least 2 shared keywords
                similar_pairs.append((num1, title1[:40], sponsor1, num2, title2[:40], sponsor2, overlap))

    print(f"\nFound {len(similar_pairs)} suspiciously similar bills:")
    print(f"{'Bill 1':<15} {'Sponsor 1':<20} {'Bill 2':<15} {'Sponsor 2':<20} {'Shared Words':<30}")
    print("-" * 100)

    for num1, title1, sponsor1, num2, title2, sponsor2, overlap in similar_pairs[:10]:
        sponsor1_name = sponsor1[:19] if sponsor1 else "Unknown"
        sponsor2_name = sponsor2[:19] if sponsor2 else "Unknown"
        print(f"{num1:<15} {sponsor1_name:<20} {num2:<15} {sponsor2_name:<20} {str(list(overlap)[:28]):<30}")

def find_heartbreak_bills(session):
    """Bills that almost made it - died at the last stage"""
    print("\n" + "="*70)
    print("HEARTBREAK BILLS - So Close, Yet So Far")
    print("="*70)

    # Get bills that failed but had multiple progress stages
    from db_setup.create_database import BillProgress

    heartbreaks = []

    bills = session.query(Bill).all()
    for bill in bills:
        passed = bill.status and ('royal assent' in bill.status.lower() or 'passed' in bill.status.lower())

        if not passed:
            # Count progress stages
            progress_count = session.query(BillProgress).filter_by(bill_id=bill.bill_id).count()

            if progress_count >= 5:  # Made it through multiple stages
                last_stage = session.query(BillProgress).filter_by(
                    bill_id=bill.bill_id
                ).order_by(BillProgress.progress_date.desc()).first()

                heartbreaks.append((
                    bill.bill_number,
                    bill.short_title,
                    progress_count,
                    last_stage.status if last_stage else 'Unknown'
                ))

    heartbreaks.sort(key=lambda x: x[2], reverse=True)

    print("\nBills that went furthest before dying:")
    print(f"{'Bill Number':<15} {'Title':<45} {'Stages':<10} {'Died At':<30}")
    print("-" * 100)

    for num, title, stages, died_at in heartbreaks[:15]:
        title_short = title[:44] if title else "Untitled"
        died_short = died_at[:29] if died_at else "Unknown"
        print(f"{num:<15} {title_short:<45} {stages:<10} {died_short:<30}")

def find_identity_switchers(session):
    """MPs who completely changed their political identity"""
    print("\n" + "="*70)
    print("IDENTITY CRISIS - MPs Who Completely Changed")
    print("="*70)

    # Find MPs who changed parties
    switchers = []

    members = session.query(Member).all()
    for member in members:
        roles = session.query(Role).filter_by(
            member_id=member.member_id,
            role_type='POLITICAL_AFFILIATION'
        ).order_by(Role.from_date).all()

        if len(roles) >= 2:
            parties = [r.party for r in roles if r.party]
            if len(set(parties)) > 1:  # Changed parties
                switchers.append((
                    member.name,
                    ' -> '.join(parties),
                    len(set(parties))
                ))

    switchers.sort(key=lambda x: x[2], reverse=True)

    print("\nMPs who changed parties (top identity switchers):")
    print(f"{'MP Name':<35} {'Party Journey':<50} {'Parties':<10}")
    print("-" * 100)

    for name, journey, count in switchers[:15]:
        print(f"{name[:34]:<35} {journey[:49]:<50} {count:<10}")

def find_laziest_parliaments(session):
    """Which parliaments barely did anything?"""
    print("\n" + "="*70)
    print("THE LAZY ONES - Parliaments That Barely Worked")
    print("="*70)

    parliament_work = defaultdict(lambda: {'bills': 0, 'votes': 0, 'duration': 0})

    # Bills per parliament
    for bill in session.query(Bill).all():
        parl = f"{bill.parliament_number}-{bill.session_number}"
        parliament_work[parl]['bills'] += 1

    # Votes per parliament
    for vote in session.query(Vote.parliament_number, Vote.session_number).distinct().all():
        if vote.parliament_number and vote.session_number:
            parl = f"{vote.parliament_number}-{vote.session_number}"
            vote_count = session.query(Vote).filter_by(
                parliament_number=vote.parliament_number,
                session_number=vote.session_number
            ).count()
            parliament_work[parl]['votes'] = vote_count

    # Calculate laziness score (inverse of work)
    laziness = []
    for parl, work in parliament_work.items():
        if work['bills'] > 0:
            # Lower score = more lazy
            productivity = work['bills'] + (work['votes'] / 100)
            laziness.append((parl, work['bills'], work['votes'], productivity))

    laziness.sort(key=lambda x: x[3])  # Sort by productivity (ascending = laziest)

    print("\nLaziest parliaments (lowest productivity):")
    print(f"{'Parliament':<15} {'Bills':<12} {'Votes':<12} {'Productivity Score':<20}")
    print("-" * 70)

    for parl, bills, votes, score in laziness[:10]:
        print(f"{parl:<15} {bills:<12} {votes:<12} {score:<20.1f}")

def main():
    """Ask wild questions nobody thought to ask"""
    print("\nWILD QUESTIONS - Mining With Human Curiosity")
    print("="*70)
    print("Not analytics. Not dashboards. Just... weird questions.")
    print("="*70)

    session = Session()

    try:
        find_late_night_votes(session)
        find_election_panic(session)
        find_unlikely_friendships(session)
        find_bill_copycats(session)
        find_heartbreak_bills(session)
        find_identity_switchers(session)
        find_laziest_parliaments(session)

        print("\n" + "="*70)
        print("WILD QUESTIONS COMPLETE")
        print("="*70)
        print("\nThese are the stories humans actually care about!")

    finally:
        session.close()

if __name__ == "__main__":
    main()
