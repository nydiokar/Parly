#!/usr/bin/env python3
"""
Vote Type Classification Utility

Classifies votes as 'budget' vs 'policy' based on vote topics/descriptions.
This is crucial for:

1. Activity heatmaps (exclude budget votes for clarity)
2. Budget analysis (identify spending-related votes)
3. Understanding parliamentary work patterns

Classification Logic:
- Budget votes: Contain keywords related to estimates, concurrence, supplementary estimates
- Policy votes: All other votes (bills, motions, etc.)
"""

import re
from typing import List, Dict, Set
from pathlib import Path
import sqlite3
from datetime import datetime


# Budget-related keywords (case-insensitive)
BUDGET_KEYWORDS = {
    # Direct budget terms
    'estimate', 'estimates', 'supplementary estimate', 'supplementary estimates',
    'interim estimate', 'interim estimates',

    # Concurrence votes
    'concurrence', 'concurrence in committee',

    # Supply and spending
    'supply', 'ways and means',

    # Appropriations
    'appropriation', 'appropriations',

    # Budget bills
    'budget', 'budget implementation', 'economic statement',

    # Financial terms
    'appropriation bill', 'supply bill', 'money bill',

    # Government spending
    'main estimates', 'supplementary estimates', 'interim supply',

    # Opposition motions that are budget-related
    'opposed the motion'  # Often used in budget contexts
}

# Additional patterns for budget detection
BUDGET_PATTERNS = [
    r'estimates?\s+\d{4}[-–]\d{2}',  # "Estimates 2023-24"
    r'supplementary\s+[a-z]+\s+estimates',  # "Supplementary A Estimates"
    r'interim\s+estimates',  # "Interim Estimates"
    r'appropriation\s+act',  # "Appropriation Act"
    r'concurrence\s+in.*committee',  # "Concurrence in Committee of the Whole"
]


def is_budget_vote(vote_topic: str) -> bool:
    """
    Classify a vote as budget-related or policy-related.

    Args:
        vote_topic: The vote description/topic

    Returns:
        True if budget-related, False if policy-related
    """
    if not vote_topic or not isinstance(vote_topic, str):
        return False

    # Convert to lowercase for case-insensitive matching
    topic_lower = vote_topic.lower().strip()

    # Check for direct keyword matches
    for keyword in BUDGET_KEYWORDS:
        if keyword.lower() in topic_lower:
            return True

    # Check for pattern matches
    for pattern in BUDGET_PATTERNS:
        if re.search(pattern, topic_lower, re.IGNORECASE):
            return True

    return False


def classify_vote_topics(vote_topics: List[str]) -> Dict[str, List[str]]:
    """
    Classify a list of vote topics into budget and policy categories.

    Args:
        vote_topics: List of vote topic strings

    Returns:
        Dictionary with 'budget' and 'policy' lists
    """
    budget_votes = []
    policy_votes = []

    for topic in vote_topics:
        if is_budget_vote(topic):
            budget_votes.append(topic)
        else:
            policy_votes.append(topic)

    return {
        'budget': budget_votes,
        'policy': policy_votes
    }


def analyze_votes_from_database(db_path: str = "data/parliament.db", limit: int = None) -> Dict:
    """
    Analyze vote classifications from the database.

    Args:
        db_path: Path to SQLite database
        limit: Optional limit on number of votes to analyze

    Returns:
        Analysis results dictionary
    """
    if not Path(db_path).exists():
        raise FileNotFoundError(f"Database not found: {db_path}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get vote topics
    query = "SELECT vote_id, vote_topic FROM votes"
    if limit:
        query += f" LIMIT {limit}"

    cursor.execute(query)
    votes = cursor.fetchall()

    # Classify votes
    budget_count = 0
    policy_count = 0
    budget_samples = []
    policy_samples = []

    for vote_id, topic in votes:
        if is_budget_vote(topic):
            budget_count += 1
            if len(budget_samples) < 10:  # Keep 10 samples
                budget_samples.append((vote_id, topic))
        else:
            policy_count += 1
            if len(policy_samples) < 10:  # Keep 10 samples
                policy_samples.append((vote_id, topic))

    conn.close()

    total_votes = budget_count + policy_count

    return {
        'total_votes': total_votes,
        'budget_votes': budget_count,
        'policy_votes': policy_count,
        'budget_percentage': (budget_count / total_votes * 100) if total_votes > 0 else 0,
        'policy_percentage': (policy_count / total_votes * 100) if total_votes > 0 else 0,
        'budget_samples': budget_samples,
        'policy_samples': policy_samples
    }


def get_vote_type_stats_by_date(db_path: str = "data/parliament.db") -> Dict:
    """
    Get vote type statistics by date for activity heatmap analysis.

    Returns vote counts per day, separated by budget/policy types.
    """
    if not Path(db_path).exists():
        raise FileNotFoundError(f"Database not found: {db_path}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get votes with dates
    query = """
    SELECT
        date(vote_date) as vote_day,
        vote_topic,
        COUNT(*) as vote_count
    FROM votes
    WHERE vote_date IS NOT NULL
    GROUP BY date(vote_date), vote_topic
    ORDER BY vote_day
    """

    cursor.execute(query)
    results = cursor.fetchall()
    conn.close()

    # Process results
    daily_stats = {}
    budget_days = set()
    policy_days = set()

    for vote_day, topic, count in results:
        if vote_day not in daily_stats:
            daily_stats[vote_day] = {'budget': 0, 'policy': 0, 'total': 0}

        if is_budget_vote(topic):
            daily_stats[vote_day]['budget'] += count
            budget_days.add(vote_day)
        else:
            daily_stats[vote_day]['policy'] += count
            policy_days.add(vote_day)

        daily_stats[vote_day]['total'] += count

    return {
        'daily_stats': daily_stats,
        'budget_days': sorted(list(budget_days)),
        'policy_days': sorted(list(policy_days)),
        'total_budget_days': len(budget_days),
        'total_policy_days': len(policy_days)
    }


def print_analysis_report(analysis: Dict):
    """
    Print a formatted analysis report.

    Args:
        analysis: Analysis results from analyze_votes_from_database
    """
    print("Vote Type Classification Analysis")
    print("=" * 50)
    print(f"Total votes analyzed: {analysis['total_votes']:,}")
    print(f"Budget votes: {analysis['budget_votes']:,} ({analysis['budget_percentage']:.1f}%)")
    print(f"Policy votes: {analysis['policy_votes']:,} ({analysis['policy_percentage']:.1f}%)")
    print()

    print("Budget Vote Samples:")
    print("-" * 25)
    for vote_id, topic in analysis['budget_samples'][:5]:  # Show first 5
        print(f"  {vote_id}: {topic[:80]}{'...' if len(topic) > 80 else ''}")
    print()

    print("Policy Vote Samples:")
    print("-" * 25)
    for vote_id, topic in analysis['policy_samples'][:5]:  # Show first 5
        print(f"  {vote_id}: {topic[:80]}{'...' if len(topic) > 80 else ''}")


if __name__ == "__main__":
    # Example usage and testing
    print("Vote Type Classification Utility")
    print("=" * 40)

    # Test with sample vote topics
    test_topics = [
        "Concurrence in Committee of the Whole on Supplementary Estimates (A)",
        "Second reading of Bill C-123, An Act to amend the Income Tax Act",
        "Opposed the motion",
        "Main Estimates 2023-24",
        "Motion to adjourn",
        "Interim Estimates",
        "Third reading of Bill S-456, An Act respecting something",
        "Ways and Means No. 2",
        "Opposition motion: That the House condemn the government's handling of X",
        "Appropriation Act No. 1, 2023-24"
    ]

    print("Testing classification:")
    for topic in test_topics:
        vote_type = "BUDGET" if is_budget_vote(topic) else "POLICY"
        print(f"  {vote_type}: {topic}")

    print()

    # Analyze database if it exists
    try:
        analysis = analyze_votes_from_database(limit=1000)  # Analyze first 1000 votes
        print_analysis_report(analysis)

        print()
        print("Daily Statistics Summary:")
        print("-" * 30)
        daily_stats = get_vote_type_stats_by_date()
        print(f"Days with budget votes: {daily_stats['total_budget_days']}")
        print(f"Days with policy votes: {daily_stats['total_policy_days']}")

        # Show sample daily stats
        sample_days = list(daily_stats['daily_stats'].keys())[:3]
        for day in sample_days:
            stats = daily_stats['daily_stats'][day]
            print(f"  {day}: {stats['budget']} budget, {stats['policy']} policy votes")

    except FileNotFoundError:
        print("Database not found - skipping database analysis")
        print("To analyze your database, ensure data/parliament.db exists")
