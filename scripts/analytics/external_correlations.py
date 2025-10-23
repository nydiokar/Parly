"""
External Correlations - Connect Parliament Data to Outside World

What if we correlate parliamentary activity with:
- Economic crises (2008 crash, COVID)
- Scandals (SNC-Lavalin, WE Charity, etc.)
- Olympic years (do they slack off?)
- Cannabis legalization timeline
- Major news events
- Prime Minister approval ratings
- Housing prices
- Gas prices
- Stock market crashes

Find the unexpected connections!
"""

from db_setup.create_database import Session, Bill, Vote, Member
from sqlalchemy import func, extract
from collections import defaultdict
from datetime import datetime

# External event timelines
ECONOMIC_CRISES = {
    2008: "Financial Crisis",
    2020: "COVID-19 Pandemic",
    2001: "Dot-com Bubble Burst"
}

MAJOR_SCANDALS = {
    2019: "SNC-Lavalin Scandal",
    2020: "WE Charity Scandal",
    2011: "Robocall Scandal",
    2006: "Sponsorship Scandal Trial",
    2004: "Sponsorship Scandal Broke"
}

OLYMPIC_YEARS = [2010, 2014, 2018, 2022, 2024]  # Winter Olympics (Canada cares more)
WORLD_CUP_YEARS = [1994, 1998, 2002, 2006, 2010, 2014, 2018, 2022]

CANNABIS_TIMELINE = {
    2001: "First medical marijuana regulations",
    2015: "Trudeau promises legalization",
    2017: "Bill C-45 introduced",
    2018: "Cannabis legalized Oct 17"
}

PM_CHANGES = {
    1993: "Chrétien takes office",
    2003: "Martin takes office",
    2006: "Harper takes office",
    2015: "Trudeau takes office"
}

def analyze_crisis_productivity(session):
    """Do they work less during crises?"""
    print("\n" + "="*70)
    print("CRISIS PRODUCTIVITY - Do They Panic or Freeze?")
    print("="*70)

    # Get bills by year
    bills_by_year = defaultdict(int)
    for bill in session.query(Bill).all():
        # Rough year estimation from parliament
        year = 1993 + (bill.parliament_number - 35) * 3
        if 1993 <= year <= 2025:
            bills_by_year[year] += 1

    print("\nBills introduced during major crises:")
    print(f"{'Year':<10} {'Event':<30} {'Bills':<10} {'Change':<15}")
    print("-" * 70)

    for year, event in sorted(ECONOMIC_CRISES.items()):
        bills = bills_by_year.get(year, 0)
        prev_year_bills = bills_by_year.get(year-1, 0)

        if prev_year_bills > 0:
            change = ((bills - prev_year_bills) / prev_year_bills) * 100
            print(f"{year:<10} {event:<30} {bills:<10} {change:+.0f}%")
        else:
            print(f"{year:<10} {event:<30} {bills:<10} N/A")

    # Check if crisis years are statistically different
    crisis_years_bills = [bills_by_year.get(y, 0) for y in ECONOMIC_CRISES.keys()]
    normal_years_bills = [b for y, b in bills_by_year.items() if y not in ECONOMIC_CRISES]

    if crisis_years_bills and normal_years_bills:
        avg_crisis = sum(crisis_years_bills) / len(crisis_years_bills)
        avg_normal = sum(normal_years_bills) / len(normal_years_bills)

        print(f"\nAverage bills in crisis years: {avg_crisis:.0f}")
        print(f"Average bills in normal years: {avg_normal:.0f}")
        print(f"Difference: {((avg_crisis - avg_normal) / avg_normal * 100):+.0f}%")

def analyze_scandal_deflection(session):
    """Do they introduce more bills during scandals to deflect?"""
    print("\n" + "="*70)
    print("SCANDAL DEFLECTION - Legislative Smoke Screens")
    print("="*70)

    bills_by_year = defaultdict(int)
    for bill in session.query(Bill).all():
        year = 1993 + (bill.parliament_number - 35) * 3
        if 1993 <= year <= 2025:
            bills_by_year[year] += 1

    print("\nBills introduced during major scandals:")
    print(f"{'Year':<10} {'Scandal':<35} {'Bills':<10} {'vs. Avg':<15}")
    print("-" * 85)

    all_bills = [b for b in bills_by_year.values() if b > 0]
    avg_bills = sum(all_bills) / len(all_bills) if all_bills else 0

    for year, scandal in sorted(MAJOR_SCANDALS.items()):
        bills = bills_by_year.get(year, 0)
        vs_avg = ((bills - avg_bills) / avg_bills * 100) if avg_bills > 0 else 0

        print(f"{year:<10} {scandal:<35} {bills:<10} {vs_avg:+.0f}%")

def analyze_olympic_distraction(session):
    """Do they slack off during Olympics?"""
    print("\n" + "="*70)
    print("OLYMPIC DISTRACTION - Do They Watch Sports Instead of Working?")
    print("="*70)

    bills_by_year = defaultdict(int)
    votes_by_year = defaultdict(int)

    for bill in session.query(Bill).all():
        year = 1993 + (bill.parliament_number - 35) * 3
        if 1993 <= year <= 2025:
            bills_by_year[year] += 1

    # Rough vote year estimation
    for vote in session.query(Vote).all():
        if vote.vote_date:
            year = vote.vote_date.year
            votes_by_year[year] += 1

    print("\nProductivity during Olympic years:")
    print(f"{'Year':<10} {'Bills':<10} {'Votes':<10} {'Total Work':<15}")
    print("-" * 50)

    olympic_work = []
    for year in OLYMPIC_YEARS:
        bills = bills_by_year.get(year, 0)
        votes = votes_by_year.get(year, 0)
        total = bills + (votes / 100)  # Normalize votes
        olympic_work.append(total)
        print(f"{year:<10} {bills:<10} {votes:<10} {total:<15.1f}")

    # Compare to non-Olympic years
    non_olympic_work = []
    for year in range(2000, 2025):
        if year not in OLYMPIC_YEARS:
            bills = bills_by_year.get(year, 0)
            votes = votes_by_year.get(year, 0)
            total = bills + (votes / 100)
            if total > 0:
                non_olympic_work.append(total)

    if olympic_work and non_olympic_work:
        avg_olympic = sum(olympic_work) / len(olympic_work)
        avg_non = sum(non_olympic_work) / len(non_olympic_work)

        print(f"\nAverage work during Olympics: {avg_olympic:.1f}")
        print(f"Average work other years: {avg_non:.1f}")
        print(f"Difference: {((avg_olympic - avg_non) / avg_non * 100):+.0f}%")

def analyze_cannabis_obsession(session):
    """Track cannabis-related bills over time"""
    print("\n" + "="*70)
    print("CANNABIS OBSESSION - From Zero to Legal")
    print("="*70)

    cannabis_bills = []

    for bill in session.query(Bill).all():
        title = (bill.short_title or bill.long_title or "").lower()

        if any(word in title for word in ['cannabis', 'marijuana', 'marihuana', 'drug']):
            year = 1993 + (bill.parliament_number - 35) * 3
            cannabis_bills.append((year, bill.bill_number, bill.short_title or bill.long_title))

    # Group by year
    by_year = defaultdict(list)
    for year, num, title in cannabis_bills:
        by_year[year].append((num, title))

    print("\nCannabis-related bills over time:")
    print(f"{'Year':<10} {'Count':<10} {'Key Event':<40}")
    print("-" * 70)

    for year in sorted(by_year.keys()):
        count = len(by_year[year])
        event = CANNABIS_TIMELINE.get(year, "")
        print(f"{year:<10} {count:<10} {event:<40}")

    print(f"\nTotal cannabis-related bills: {len(cannabis_bills)}")

def analyze_pm_honeymoon(session):
    """Do new PMs introduce more bills in their first year?"""
    print("\n" + "="*70)
    print("PM HONEYMOON - First Year Energy vs. Burnout")
    print("="*70)

    bills_by_year = defaultdict(int)
    for bill in session.query(Bill).all():
        year = 1993 + (bill.parliament_number - 35) * 3
        if 1993 <= year <= 2025:
            bills_by_year[year] += 1

    print("\nNew PM first year vs. their average:")
    print(f"{'PM':<20} {'First Year':<15} {'Bills':<10} {'Later Avg':<15} {'Difference':<15}")
    print("-" * 80)

    for year, pm in PM_CHANGES.items():
        first_year_bills = bills_by_year.get(year, 0)

        # Calculate average for their subsequent years (rough estimate)
        subsequent_bills = []
        for y in range(year + 1, year + 4):  # Next 3 years
            if y in bills_by_year:
                subsequent_bills.append(bills_by_year[y])

        if subsequent_bills:
            later_avg = sum(subsequent_bills) / len(subsequent_bills)
            diff = ((first_year_bills - later_avg) / later_avg * 100) if later_avg > 0 else 0
            print(f"{pm[:19]:<20} {year:<15} {first_year_bills:<10} {later_avg:<15.0f} {diff:+.0f}%")
        else:
            print(f"{pm[:19]:<20} {year:<15} {first_year_bills:<10} {'N/A':<15} {'N/A':<15}")

def analyze_day_of_week_patterns(session):
    """Do they vote more on certain days?"""
    print("\n" + "="*70)
    print("WEEKLY PATTERNS - Do They Take Fridays Off?")
    print("="*70)

    votes_by_dow = defaultdict(int)
    bills_by_dow = defaultdict(int)

    day_names = {0: "Monday", 1: "Tuesday", 2: "Wednesday", 3: "Thursday",
                 4: "Friday", 5: "Saturday", 6: "Sunday"}

    # Count votes by day of week
    for vote in session.query(Vote).filter(Vote.vote_date.isnot(None)).all():
        dow = vote.vote_date.weekday()
        votes_by_dow[dow] += 1

    print("\nVotes by day of week:")
    print(f"{'Day':<15} {'Votes':<15} {'% of Total':<15}")
    print("-" * 50)

    total_votes = sum(votes_by_dow.values())
    for dow in range(7):
        votes = votes_by_dow.get(dow, 0)
        pct = (votes / total_votes * 100) if total_votes > 0 else 0
        print(f"{day_names[dow]:<15} {votes:<15} {pct:.1f}%")

def analyze_month_patterns(session):
    """Which months are they most active?"""
    print("\n" + "="*70)
    print("SEASONAL PATTERNS - Summer Break Evidence")
    print("="*70)

    votes_by_month = defaultdict(int)

    month_names = {1: "January", 2: "February", 3: "March", 4: "April",
                   5: "May", 6: "June", 7: "July", 8: "August",
                   9: "September", 10: "October", 11: "November", 12: "December"}

    for vote in session.query(Vote).filter(Vote.vote_date.isnot(None)).all():
        month = vote.vote_date.month
        votes_by_month[month] += 1

    print("\nVotes by month:")
    print(f"{'Month':<15} {'Votes':<15} {'% of Total':<15}")
    print("-" * 50)

    total_votes = sum(votes_by_month.values())
    for month in range(1, 13):
        votes = votes_by_month.get(month, 0)
        pct = (votes / total_votes * 100) if total_votes > 0 else 0
        print(f"{month_names[month]:<15} {votes:<15} {pct:.1f}%")

    # Highlight summer break
    summer_votes = sum(votes_by_month.get(m, 0) for m in [7, 8])
    summer_pct = (summer_votes / total_votes * 100) if total_votes > 0 else 0
    print(f"\nJuly + August combined: {summer_votes} votes ({summer_pct:.1f}%)")

def main():
    """Run all external correlation analyses"""
    print("\nEXTERNAL CORRELATIONS - Parliament vs. The Real World")
    print("="*70)
    print("Connecting parliamentary data to outside events...")
    print("="*70)

    session = Session()

    try:
        analyze_crisis_productivity(session)
        analyze_scandal_deflection(session)
        analyze_olympic_distraction(session)
        analyze_cannabis_obsession(session)
        analyze_pm_honeymoon(session)
        analyze_day_of_week_patterns(session)
        analyze_month_patterns(session)

        print("\n" + "="*70)
        print("EXTERNAL CORRELATIONS COMPLETE")
        print("="*70)
        print("\nThese connections could be WILD viral content!")

    finally:
        session.close()

if __name__ == "__main__":
    main()
