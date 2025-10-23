"""
Pattern Discovery Script - Mine the data for unseen insights

This script analyzes 32 years of parliamentary data to discover:
1. "Doomed Topics" - Issues that never make it past committee
2. "Neglected Issues" - Topics that used to matter but disappeared
3. "Death Stages" - Which stage kills which type of bill
4. "Regional Blind Spots" - Issues provinces care about but Parliament ignores
5. "The Graveyard Shift" - Which parliaments kill the most bills
"""

from db_setup.create_database import Session, Bill, BillProgress, Vote, Member
from sqlalchemy import func, and_, or_
from collections import Counter, defaultdict
import re

def extract_topic_keywords(title):
    """Extract topic keywords from bill titles using simple NLP."""
    if not title:
        return []

    # Common topic keywords
    keywords = {
        'healthcare': ['health', 'medical', 'hospital', 'medicare', 'care'],
        'environment': ['environment', 'climate', 'carbon', 'emission', 'green', 'pollution'],
        'economy': ['econom', 'tax', 'budget', 'fiscal', 'finance', 'debt'],
        'justice': ['justice', 'crime', 'criminal', 'court', 'sentence', 'prison'],
        'indigenous': ['indigenous', 'first nation', 'aboriginal', 'metis', 'inuit'],
        'immigration': ['immigration', 'refugee', 'citizenship', 'border'],
        'education': ['education', 'school', 'student', 'university', 'college'],
        'housing': ['housing', 'home', 'mortgage', 'rent', 'shelter'],
        'employment': ['employment', 'labor', 'labour', 'worker', 'job', 'wage'],
        'privacy': ['privacy', 'data', 'surveillance', 'information'],
        'defense': ['defense', 'defence', 'military', 'armed forces', 'veteran'],
        'agriculture': ['agriculture', 'farm', 'food', 'agricultural'],
        'transport': ['transport', 'highway', 'railway', 'aviation', 'infrastructure'],
        'energy': ['energy', 'oil', 'gas', 'electricity', 'pipeline'],
        'trade': ['trade', 'export', 'import', 'tariff', 'commerce']
    }

    title_lower = title.lower()
    topics = []

    for topic, terms in keywords.items():
        if any(term in title_lower for term in terms):
            topics.append(topic)

    return topics if topics else ['other']

def analyze_doomed_topics(session):
    """Find topics that consistently fail to pass."""
    print("\n" + "="*70)
    print("DOOMED TOPICS - Issues That Never Make It")
    print("="*70)

    # Get all bills with their status
    bills = session.query(Bill).all()

    topic_stats = defaultdict(lambda: {'total': 0, 'passed': 0, 'died': 0})

    for bill in bills:
        topics = extract_topic_keywords(bill.short_title or bill.long_title)
        passed = bill.status and ('royal assent' in bill.status.lower() or 'passed' in bill.status.lower())

        for topic in topics:
            topic_stats[topic]['total'] += 1
            if passed:
                topic_stats[topic]['passed'] += 1
            else:
                topic_stats[topic]['died'] += 1

    # Calculate failure rates
    doomed = []
    for topic, stats in topic_stats.items():
        if stats['total'] >= 10:  # Only topics with significant sample size
            failure_rate = (stats['died'] / stats['total']) * 100
            doomed.append((topic, failure_rate, stats))

    # Sort by failure rate
    doomed.sort(key=lambda x: x[1], reverse=True)

    print("\nTop 10 Doomed Topics (highest failure rate):")
    print(f"{'Topic':<20} {'Failure Rate':<15} {'Total':<10} {'Died':<10} {'Passed':<10}")
    print("-" * 70)

    for topic, failure_rate, stats in doomed[:10]:
        print(f"{topic:<20} {failure_rate:>6.1f}%        {stats['total']:<10} {stats['died']:<10} {stats['passed']:<10}")

    return doomed

def analyze_neglected_topics(session):
    """Find topics that disappeared over time."""
    print("\n" + "="*70)
    print("NEGLECTED TOPICS - Issues Parliament Forgot About")
    print("="*70)

    # Get bills by parliament
    bills = session.query(Bill).order_by(Bill.parliament_number).all()

    # Track topics by parliament era
    early_era = defaultdict(int)  # Parliaments 35-39 (1993-2008)
    late_era = defaultdict(int)   # Parliaments 40-45 (2008-2025)

    for bill in bills:
        topics = extract_topic_keywords(bill.short_title or bill.long_title)

        if bill.parliament_number <= 39:
            for topic in topics:
                early_era[topic] += 1
        else:
            for topic in topics:
                late_era[topic] += 1

    # Find topics that dropped significantly
    neglected = []
    for topic in early_era:
        early_count = early_era[topic]
        late_count = late_era.get(topic, 0)

        if early_count >= 5:  # Only significant topics
            drop_pct = ((early_count - late_count) / early_count) * 100
            if drop_pct > 30:  # At least 30% drop
                neglected.append((topic, early_count, late_count, drop_pct))

    neglected.sort(key=lambda x: x[3], reverse=True)

    print("\nTopics Parliament Stopped Caring About:")
    print(f"{'Topic':<20} {'1993-2008':<12} {'2008-2025':<12} {'Drop':<10}")
    print("-" * 70)

    for topic, early, late, drop in neglected[:10]:
        print(f"{topic:<20} {early:<12} {late:<12} {drop:>6.1f}%")

    return neglected

def analyze_death_stages(session):
    """Find which stages kill which types of bills."""
    print("\n" + "="*70)
    print("DEATH STAGES - Where Bills Go to Die")
    print("="*70)

    # Get bills with progress events
    bills_with_progress = (
        session.query(Bill)
        .join(BillProgress)
        .all()
    )

    # Track last stage for failed bills
    death_stages = defaultdict(lambda: defaultdict(int))

    for bill in bills_with_progress:
        topics = extract_topic_keywords(bill.short_title or bill.long_title)
        passed = bill.status and ('royal assent' in bill.status.lower() or 'passed' in bill.status.lower())

        if not passed:
            # Get last progress stage
            last_progress = (
                session.query(BillProgress)
                .filter_by(bill_id=bill.bill_id)
                .order_by(BillProgress.progress_date.desc())
                .first()
            )

            if last_progress:
                stage = last_progress.status or 'Unknown'
                for topic in topics:
                    death_stages[topic][stage] += 1

    # Find most common death stages per topic
    print("\nMost Common Death Stages by Topic:")
    print(f"{'Topic':<20} {'Death Stage':<40} {'Count':<10}")
    print("-" * 70)

    for topic in sorted(death_stages.keys())[:10]:
        if sum(death_stages[topic].values()) >= 5:
            most_common_stage = max(death_stages[topic].items(), key=lambda x: x[1])
            print(f"{topic:<20} {most_common_stage[0][:38]:<40} {most_common_stage[1]:<10}")

    return death_stages

def analyze_parliament_graveyards(session):
    """Find which parliaments kill the most bills."""
    print("\n" + "="*70)
    print("THE GRAVEYARD SHIFT - Most Deadly Parliaments")
    print("="*70)

    # Get bills by parliament
    parliament_stats = defaultdict(lambda: {'total': 0, 'passed': 0, 'died': 0})

    bills = session.query(Bill).all()

    for bill in bills:
        parl = f"{bill.parliament_number}-{bill.session_number}"
        parliament_stats[parl]['total'] += 1

        passed = bill.status and ('royal assent' in bill.status.lower() or 'passed' in bill.status.lower())
        if passed:
            parliament_stats[parl]['passed'] += 1
        else:
            parliament_stats[parl]['died'] += 1

    # Calculate death rates
    graveyards = []
    for parl, stats in parliament_stats.items():
        if stats['total'] >= 10:
            death_rate = (stats['died'] / stats['total']) * 100
            graveyards.append((parl, death_rate, stats))

    graveyards.sort(key=lambda x: x[1], reverse=True)

    print("\nDeadliest Parliaments (highest bill failure rate):")
    print(f"{'Parliament':<15} {'Death Rate':<15} {'Total Bills':<15} {'Died':<10} {'Passed':<10}")
    print("-" * 70)

    for parl, death_rate, stats in graveyards[:10]:
        print(f"{parl:<15} {death_rate:>6.1f}%        {stats['total']:<15} {stats['died']:<10} {stats['passed']:<10}")

    return graveyards

def analyze_topic_trends(session):
    """Find topics that are rising or falling."""
    print("\n" + "="*70)
    print("TOPIC TRENDS - What's Hot and What's Not")
    print("="*70)

    # Divide into three eras for trend analysis
    era1 = defaultdict(int)  # Parliaments 35-38 (1993-2006)
    era2 = defaultdict(int)  # Parliaments 39-42 (2006-2019)
    era3 = defaultdict(int)  # Parliaments 43-45 (2019-2025)

    bills = session.query(Bill).all()

    for bill in bills:
        topics = extract_topic_keywords(bill.short_title or bill.long_title)

        if bill.parliament_number <= 38:
            for topic in topics:
                era1[topic] += 1
        elif bill.parliament_number <= 42:
            for topic in topics:
                era2[topic] += 1
        else:
            for topic in topics:
                era3[topic] += 1

    # Calculate trends
    print("\nRising Topics (getting more attention):")
    print(f"{'Topic':<20} {'1993-06':<12} {'2006-19':<12} {'2019-25':<12} {'Trend':<10}")
    print("-" * 70)

    trends = []
    for topic in set(list(era1.keys()) + list(era2.keys()) + list(era3.keys())):
        e1 = era1.get(topic, 0)
        e2 = era2.get(topic, 0)
        e3 = era3.get(topic, 0)

        if e1 > 0 and e3 > e1:
            growth = ((e3 - e1) / e1) * 100
            trends.append((topic, e1, e2, e3, growth))

    trends.sort(key=lambda x: x[4], reverse=True)

    for topic, e1, e2, e3, growth in trends[:10]:
        print(f"{topic:<20} {e1:<12} {e2:<12} {e3:<12} +{growth:>5.0f}%")

    return trends

def main():
    """Run all pattern discovery analyses."""
    print("\nPATTERN DISCOVERY - Mining 32 Years of Parliamentary Data")
    print("="*70)

    session = Session()

    try:
        # Run all analyses
        doomed = analyze_doomed_topics(session)
        neglected = analyze_neglected_topics(session)
        death_stages = analyze_death_stages(session)
        graveyards = analyze_parliament_graveyards(session)
        trends = analyze_topic_trends(session)

        print("\n" + "="*70)
        print("PATTERN DISCOVERY COMPLETE")
        print("="*70)
        print("\nKey Insights:")
        print("- Found doomed topics that consistently fail")
        print("- Identified neglected issues Parliament forgot")
        print("- Mapped death stages where bills die")
        print("- Ranked deadliest parliaments")
        print("- Tracked rising and falling topic trends")
        print("\nThese insights can power viral visualizations!")

    finally:
        session.close()

if __name__ == "__main__":
    main()
