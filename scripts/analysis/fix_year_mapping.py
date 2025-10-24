#!/usr/bin/env python3
"""
Parliament to Calendar Year Mapping Utility

This script provides utilities to convert between Canadian Parliament numbers
and actual calendar years, which is needed for election year analysis and
time-based visualizations.

Parliament Sessions:
- Parliament 35: 1993-1997
- Parliament 36: 1997-2000
- Parliament 37: 2001-2004
- Parliament 38: 2004-2006
- Parliament 39: 2006-2008
- Parliament 40: 2008-2011
- Parliament 41: 2011-2015
- Parliament 42: 2015-2019
- Parliament 43: 2019-2022
- Parliament 44: 2022-2025
- Parliament 45: 2025-present
"""

from typing import Dict, List, Tuple, Optional
from datetime import datetime, date


# Parliament to year ranges mapping
PARLIAMENT_YEARS = {
    35: (1993, 1997),
    36: (1997, 2000),
    37: (2001, 2004),
    38: (2004, 2006),
    39: (2006, 2008),
    40: (2008, 2011),
    41: (2011, 2015),
    42: (2015, 2019),
    43: (2019, 2022),
    44: (2022, 2025),
    45: (2025, 2029),  # Estimated end date
}


def get_parliament_years(parliament: int) -> Tuple[int, int]:
    """
    Get the start and end years for a given parliament.

    Args:
        parliament: Parliament number (35-45)

    Returns:
        Tuple of (start_year, end_year)
    """
    if parliament not in PARLIAMENT_YEARS:
        raise ValueError(f"Unknown parliament: {parliament}. Valid range: 35-45")

    return PARLIAMENT_YEARS[parliament]


def get_parliament_for_year(year: int) -> int:
    """
    Get the parliament number for a given calendar year.

    Note: Some parliaments overlap on election years (e.g., Parliament 43: 2019-2022,
    Parliament 44: 2022-2025). In these cases, the year belongs to the parliament
    that starts in that year.

    Args:
        year: Calendar year (1993-2029)

    Returns:
        Parliament number
    """
    # Handle overlapping years by checking in reverse order
    # This ensures we get the parliament that STARTS in the given year
    for parliament in range(45, 34, -1):  # 45 down to 35
        start_year, end_year = PARLIAMENT_YEARS[parliament]
        if start_year <= year <= end_year:
            return parliament

    raise ValueError(f"Year {year} not covered by parliaments 35-45 (1993-2029)")


def is_election_year(year: int) -> bool:
    """
    Check if a year was an election year in Canada.

    Federal elections typically occur every 4 years, but can be earlier.
    Based on historical Canadian federal elections.

    Args:
        year: Calendar year

    Returns:
        True if it was an election year
    """
    election_years = {
        1993, 1997, 2000, 2004, 2006, 2008, 2011, 2015, 2019, 2022, 2025
    }
    return year in election_years


def get_years_in_parliament(parliament: int) -> List[int]:
    """
    Get all calendar years that fall within a parliament's term.

    Args:
        parliament: Parliament number

    Returns:
        List of years in chronological order
    """
    start_year, end_year = get_parliament_years(parliament)
    return list(range(start_year, end_year + 1))


def get_parliaments_for_year_range(start_year: int, end_year: int) -> List[int]:
    """
    Get all parliament numbers that cover a year range.

    Args:
        start_year: Start year (inclusive)
        end_year: End year (inclusive)

    Returns:
        List of parliament numbers in chronological order
    """
    parliaments = []
    for parliament in range(35, 46):  # 35 through 45
        parl_start, parl_end = get_parliament_years(parliament)
        # Check if parliament overlaps with the year range
        if not (parl_end < start_year or parl_start > end_year):
            parliaments.append(parliament)
    return parliaments


def convert_date_to_year(date_str: str) -> int:
    """
    Convert a date string to year for analysis purposes.

    Args:
        date_str: Date in format 'YYYY-MM-DD' or similar

    Returns:
        Calendar year as integer
    """
    try:
        # Try different date formats
        for fmt in ['%Y-%m-%d', '%Y/%m/%d', '%Y-%m-%d %H:%M:%S']:
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.year
            except ValueError:
                continue
        raise ValueError(f"Could not parse date: {date_str}")
    except Exception:
        # Fallback: extract year from string
        import re
        year_match = re.search(r'\b(19|20)\d{2}\b', str(date_str))
        if year_match:
            return int(year_match.group())
        raise ValueError(f"Could not extract year from: {date_str}")


# Utility functions for analysis
def get_election_years_in_range(start_year: int, end_year: int) -> List[int]:
    """
    Get all election years within a year range.

    Args:
        start_year: Start year
        end_year: End year

    Returns:
        List of election years
    """
    return [year for year in range(start_year, end_year + 1) if is_election_year(year)]


def get_parliament_summary() -> Dict:
    """
    Get a summary of all parliaments with their years and election info.

    Returns:
        Dictionary with parliament details
    """
    summary = {}
    for parliament in range(35, 46):
        start_year, end_year = get_parliament_years(parliament)
        years = get_years_in_parliament(parliament)
        election_years = [y for y in years if is_election_year(y)]

        summary[parliament] = {
            'years': years,
            'election_years': election_years,
            'start_year': start_year,
            'end_year': end_year,
            'duration_years': end_year - start_year + 1,
            'has_election': len(election_years) > 0
        }

    return summary


if __name__ == "__main__":
    # Example usage and testing
    print("Parliament Year Mapping Utility")
    print("=" * 40)

    # Show parliament summary
    summary = get_parliament_summary()
    for parliament, info in summary.items():
        election_str = f" (Election: {info['election_years']})" if info['election_years'] else ""
        print(f"Parliament {parliament}: {info['start_year']}-{info['end_year']}{election_str}")

    print("\nTesting functions:")
    print(f"Parliament 44 years: {get_years_in_parliament(44)}")
    print(f"Year 2022 is in Parliament: {get_parliament_for_year(2022)}")
    print(f"2022 was election year: {is_election_year(2022)}")
    print(f"Election years 2020-2025: {get_election_years_in_range(2020, 2025)}")
