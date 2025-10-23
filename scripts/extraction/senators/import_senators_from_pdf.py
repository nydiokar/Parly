"""
Import senators from PDF file into database.

Parses the Senators-list.pdf file and imports all current senators
into the senators table.
"""

import sys
import os
from datetime import datetime
import re

# Add parent directories for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../'))

from db_setup.create_database import Senator, Session


def parse_senator_name(name_str):
    """
    Parse senator name, handling special cases.

    Args:
        name_str: Name string from PDF (e.g., "Adler, Charles S.")

    Returns:
        Formatted name (e.g., "Charles S. Adler")
    """
    # Handle "Last, First Middle" format
    if ',' in name_str:
        parts = name_str.split(',', 1)
        last_name = parts[0].strip()
        first_middle = parts[1].strip()
        return f"{first_middle} {last_name}"
    return name_str.strip()


def parse_appointed_by(appointed_str):
    """
    Extract prime minister name from appointment string.

    Args:
        appointed_str: String like "Trudeau, Justin (Lib.)" or "Harper, Stephen (C)"

    Returns:
        Formatted name (e.g., "Justin Trudeau")
    """
    # Remove party affiliation in parentheses
    name_part = re.sub(r'\s*\([^)]+\)$', '', appointed_str).strip()

    # Handle "Last, First" format
    if ',' in name_part:
        parts = name_part.split(',', 1)
        last_name = parts[0].strip()
        first_name = parts[1].strip()
        return f"{first_name} {last_name}"
    return name_part


def parse_date(date_str):
    """
    Parse date from PDF format (YYYY-MM-DD).

    Args:
        date_str: Date string like "2024-08-16"

    Returns:
        datetime.date object or None if parsing fails
    """
    try:
        return datetime.strptime(date_str.strip(), '%Y-%m-%d').date()
    except:
        return None


# Current senators data extracted from PDF
# Format: (Name, Affiliation, Province, Nomination Date, Retirement Date, Appointed By)
SENATORS_DATA = [
    ("Adler, Charles S.", "CSG", "Manitoba", "2024-08-16", "2029-08-25", "Trudeau, Justin (Lib.)"),
    ("Al Zaibak, Mohammad Khair", "CSG", "Ontario", "2024-01-28", "2026-08-09", "Trudeau, Justin (Lib.)"),
    ("Anderson, Dawn", "C", "Northwest Territories", "2018-12-12", "2042-04-14", "Trudeau, Justin (Lib.)"),
    ("Arnold, Dawn", "ISG", "New Brunswick", "2025-03-07", "2041-04-23", "Trudeau, Justin (Lib.)"),
    ("Arnot, David M.", "ISG", "Saskatchewan", "2021-07-29", "2027-04-16", "Trudeau, Justin (Lib.)"),
    ("Ataullahjan, Salma", "C", "Ontario", "2010-07-09", "2027-04-29", "Harper, Stephen (C)"),
    ("Aucoin, Réjean", "CSG", "Nova Scotia", "2023-10-31", "2030-07-04", "Trudeau, Justin (Lib.)"),
    ("Audette, Michèle", "PSG", "Quebec", "2021-07-29", "2046-07-20", "Trudeau, Justin (Lib.)"),
    ("Batters, Denise", "C", "Saskatchewan", "2013-01-25", "2045-06-18", "Harper, Stephen (C)"),
    ("Bernard, Wanda Thomas", "PSG", "Nova Scotia", "2016-11-10", "2028-08-01", "Trudeau, Justin (Lib.)"),
    ("Black, Robert", "CSG", "Ontario", "2018-02-15", "2037-03-27", "Trudeau, Justin (Lib.)"),
    ("Boehm, Peter M.", "ISG", "Ontario", "2018-10-03", "2029-04-26", "Trudeau, Justin (Lib.)"),
    ("Boniface, Gwen", "ISG", "Ontario", "2016-11-10", "2030-08-05", "Trudeau, Justin (Lib.)"),
    ("Boudreau, Victor", "ISG", "New Brunswick", "2024-06-28", "2045-05-03", "Trudeau, Justin (Lib.)"),
    ("Boyer, Yvonne", "ISG", "Ontario", "2018-03-15", "2028-10-25", "Trudeau, Justin (Lib.)"),
    ("Brazeau, Patrick", "Non-affiliated", "Quebec", "2009-01-08", "2049-11-11", "Harper, Stephen (C)"),
    ("Burey, Sharon", "CSG", "Ontario", "2022-11-21", "2032-12-04", "Trudeau, Justin (Lib.)"),
    ("Busson, Bev", "ISG", "British Columbia", "2018-09-24", "2026-08-23", "Trudeau, Justin (Lib.)"),
    ("Cardozo, Andrew", "PSG", "Ontario", "2022-11-21", "2031-03-21", "Trudeau, Justin (Lib.)"),
    ("Carignan, Claude", "C", "Quebec", "2009-08-27", "2039-12-04", "Harper, Stephen (C)"),
    ("Clement, Bernadette", "ISG", "Ontario", "2021-06-22", "2040-05-17", "Trudeau, Justin (Lib.)"),
    ("Cormier, René", "ISG", "New Brunswick", "2016-11-10", "2031-04-27", "Trudeau, Justin (Lib.)"),
    ("Coyle, Mary", "ISG", "Nova Scotia", "2017-12-04", "2029-11-05", "Trudeau, Justin (Lib.)"),
    ("Cuzner, Rodger", "PSG", "Nova Scotia", "2023-10-31", "2030-11-04", "Trudeau, Justin (Lib.)"),
    ("Dalphond, Pierre J.", "ISG", "Quebec", "2018-06-06", "2029-05-01", "Trudeau, Justin (Lib.)"),
    ("Dasko, Donna", "ISG", "Ontario", "2018-06-06", "2026-08-19", "Trudeau, Justin (Lib.)"),
    ("Deacon, Colin", "CSG", "Nova Scotia", "2018-06-15", "2034-11-01", "Trudeau, Justin (Lib.)"),
    ("Deacon, Marty", "ISG", "Ontario", "2018-02-15", "2033-04-23", "Trudeau, Justin (Lib.)"),
    ("Dean, Tony", "ISG", "Ontario", "2016-11-10", "2028-08-19", "Trudeau, Justin (Lib.)"),
    ("Dhillon, Baltej S.", "ISG", "British Columbia", "2025-02-07", "2041-11-13", "Trudeau, Justin (Lib.)"),
    ("Downe, Percy E.", "CSG", "Prince Edward Island", "2003-06-26", "2029-07-08", "Chrétien, Jean (Lib.)"),
    ("Duncan, Pat", "GRO", "Yukon", "2018-12-12", "2035-04-08", "Trudeau, Justin (Lib.)"),
    ("Forest, Éric", "ISG", "Quebec", "2016-11-21", "2027-04-06", "Trudeau, Justin (Lib.)"),
    ("Francis, Brian", "PSG", "Prince Edward Island", "2018-10-11", "2032-09-28", "Trudeau, Justin (Lib.)"),
    ("Fridhandler, Daryl S.", "PSG", "Alberta", "2024-08-30", "2031-10-09", "Trudeau, Justin (Lib.)"),
    ("Gagné, Raymonde", "Non-affiliated", "Manitoba", "2016-04-01", "2031-01-07", "Trudeau, Justin (Lib.)"),
    ("Galvez, Rosa", "ISG", "Quebec", "2016-12-06", "2036-06-21", "Trudeau, Justin (Lib.)"),
    ("Gerba, Amina", "PSG", "Quebec", "2021-07-29", "2036-03-14", "Trudeau, Justin (Lib.)"),
    ("Gignac, Clément", "CSG", "Quebec", "2021-07-29", "2030-05-07", "Trudeau, Justin (Lib.)"),
    ("Greenwood, Margo", "ISG", "British Columbia", "2022-11-10", "2028-09-02", "Trudeau, Justin (Lib.)"),
    ("Harder, Peter", "PSG", "Ontario", "2016-03-23", "2027-08-25", "Trudeau, Justin (Lib.)"),
    ("Hay, Katherine", "PSG", "Ontario", "2025-03-07", "2036-01-16", "Trudeau, Justin (Lib.)"),
    ("Hébert, Martine", "ISG", "Quebec", "2025-02-07", "2040-10-07", "Trudeau, Justin (Lib.)"),
    ("Henkel, Danièle", "PSG", "Quebec", "2025-02-14", "2031-01-16", "Trudeau, Justin (Lib.)"),
    ("Housakos, Leo", "C", "Quebec", "2009-01-08", "2043-01-10", "Harper, Stephen (C)"),
    ("Ince, Tony", "CSG", "Nova Scotia", "2025-03-07", "2032-12-16", "Trudeau, Justin (Lib.)"),
    ("Karetak-Lindell, Nancy", "ISG", "Nunavut", "2024-12-19", "2032-12-10", "Trudeau, Justin (Lib.)"),
    ("Kingston, Joan", "ISG", "New Brunswick", "2023-10-31", "2030-01-08", "Trudeau, Justin (Lib.)"),
    ("Klyne, Marty", "PSG", "Saskatchewan", "2018-09-24", "2032-03-06", "Trudeau, Justin (Lib.)"),
    ("Kutcher, Stan", "ISG", "Nova Scotia", "2018-12-12", "2026-12-16", "Trudeau, Justin (Lib.)"),
    ("LaBoucane-Benson, Patti", "GRO", "Alberta", "2018-10-03", "2044-02-20", "Trudeau, Justin (Lib.)"),
    ("Lewis, Todd", "CSG", "Saskatchewan", "2025-02-07", "2036-07-21", "Trudeau, Justin (Lib.)"),
    ("Loffreda, Tony", "ISG", "Quebec", "2019-07-22", "2037-08-14", "Trudeau, Justin (Lib.)"),
    ("MacAdam, Jane", "ISG", "Prince Edward Island", "2023-05-03", "2032-03-01", "Trudeau, Justin (Lib.)"),
    ("MacDonald, Michael L.", "C", "Nova Scotia", "2009-01-02", "2030-05-04", "Harper, Stephen (C)"),
    ("Manning, Fabian", "C", "Newfoundland and Labrador", "2011-05-25", "2039-05-21", "Harper, Stephen (C)"),
    ("Marshall, Elizabeth", "C", "Newfoundland and Labrador", "2010-01-29", "2026-09-07", "Harper, Stephen (C)"),
    ("Martin, Yonah", "C", "British Columbia", "2009-01-02", "2040-04-11", "Harper, Stephen (C)"),
    ("McBean, Marnie", "ISG", "Ontario", "2023-12-20", "2043-01-28", "Trudeau, Justin (Lib.)"),
    ("McCallum, Mary Jane", "C", "Manitoba", "2017-12-04", "2027-05-01", "Trudeau, Justin (Lib.)"),
    ("McNair, John M.", "ISG", "New Brunswick", "2023-10-31", "2032-06-03", "Trudeau, Justin (Lib.)"),
    ("McPhedran, Marilou", "Non-affiliated", "Manitoba", "2016-11-10", "2026-07-22", "Trudeau, Justin (Lib.)"),
    ("Miville-Dechêne, Julie", "PSG", "Quebec", "2018-06-20", "2034-07-10", "Trudeau, Justin (Lib.)"),
    ("Mohamed, Farah", "ISG", "Ontario", "2025-03-07", "2045-07-05", "Trudeau, Justin (Lib.)"),
    ("Moncion, Lucie", "ISG", "Ontario", "2016-11-10", "2033-10-25", "Trudeau, Justin (Lib.)"),
    ("Moodie, Rosemary", "ISG", "Ontario", "2018-12-12", "2031-11-24", "Trudeau, Justin (Lib.)"),
    ("Moreau, Pierre", "GRO", "Quebec", "2024-09-10", "2032-12-12", "Trudeau, Justin (Lib.)"),
    ("Muggli, Tracy", "PSG", "Saskatchewan", "2024-08-16", "2040-09-18", "Trudeau, Justin (Lib.)"),
    ("Osler, Flordeliz (Gigi)", "CSG", "Manitoba", "2022-09-26", "2043-09-09", "Trudeau, Justin (Lib.)"),
    ("Oudar, Manuelle", "ISG", "Quebec", "2024-02-13", "2038-07-05", "Trudeau, Justin (Lib.)"),
    ("Pate, Kim", "ISG", "Ontario", "2016-11-10", "2034-11-10", "Trudeau, Justin (Lib.)"),
    ("Patterson, Rebecca", "CSG", "Ontario", "2022-11-21", "2040-06-15", "Trudeau, Justin (Lib.)"),
    ("Petitclerc, Chantal", "ISG", "Quebec", "2016-04-01", "2044-12-15", "Trudeau, Justin (Lib.)"),
    ("Petten, Iris G.", "GRO", "Newfoundland and Labrador", "2023-05-03", "2034-02-05", "Trudeau, Justin (Lib.)"),
    ("Poirier, Rose-May", "C", "New Brunswick", "2010-02-28", "2029-03-02", "Harper, Stephen (C)"),
    ("Prosper, Paul (PJ)", "CSG", "Nova Scotia", "2023-07-06", "2039-11-04", "Trudeau, Justin (Lib.)"),
    ("Pupatello, Sandra", "GRO", "Ontario", "2025-03-07", "2037-10-06", "Trudeau, Justin (Lib.)"),
    ("Quinn, Jim", "CSG", "New Brunswick", "2021-06-22", "2032-01-25", "Trudeau, Justin (Lib.)"),
    ("Ravalia, Mohamed-Iqbal", "ISG", "Newfoundland and Labrador", "2018-06-01", "2032-08-15", "Trudeau, Justin (Lib.)"),
    ("Ringuette, Pierrette", "ISG", "New Brunswick", "2002-12-12", "2030-12-31", "Chrétien, Jean (Lib.)"),
    ("Robinson, Mary", "CSG", "Prince Edward Island", "2024-01-22", "2045-08-03", "Trudeau, Justin (Lib.)"),
    ("Ross, Krista", "CSG", "New Brunswick", "2023-10-31", "2042-09-30", "Trudeau, Justin (Lib.)"),
    ("Saint-Germain, Raymonde", "ISG", "Quebec", "2016-11-25", "2026-10-07", "Trudeau, Justin (Lib.)"),
    ("Senior, Paulette", "ISG", "Ontario", "2023-12-20", "2036-12-04", "Trudeau, Justin (Lib.)"),
    ("Simons, Paula", "ISG", "Alberta", "2018-10-03", "2039-09-07", "Trudeau, Justin (Lib.)"),
    ("Smith, Larry W.", "C", "Quebec", "2011-05-25", "2026-04-28", "Harper, Stephen (C)"),
    ("Sorensen, Karen", "ISG", "Alberta", "2021-07-29", "2034-05-20", "Trudeau, Justin (Lib.)"),
    ("Surette, Allister W.", "ISG", "Nova Scotia", "2024-12-19", "2036-09-21", "Trudeau, Justin (Lib.)"),
    ("Tannas, Scott", "CSG", "Alberta", "2013-03-25", "2037-02-25", "Harper, Stephen (C)"),
    ("Varone, Toni", "ISG", "Ontario", "2023-12-20", "2033-06-20", "Trudeau, Justin (Lib.)"),
    ("Verner, Josée", "CSG", "Quebec", "2011-06-13", "2034-12-30", "Harper, Stephen (C)"),
    ("Wallin, Pamela", "CSG", "Saskatchewan", "2009-01-02", "2028-04-10", "Harper, Stephen (C)"),
    ("Wells, David M.", "C", "Newfoundland and Labrador", "2013-01-25", "2037-02-28", "Harper, Stephen (C)"),
    ("Wells, Kristopher", "PSG", "Alberta", "2024-08-30", "2046-10-07", "Trudeau, Justin (Lib.)"),
    ("White, Judy A.", "PSG", "Newfoundland and Labrador", "2023-07-06", "2039-01-11", "Trudeau, Justin (Lib.)"),
    ("Wilson, Duncan", "PSG", "British Columbia", "2025-02-28", "2042-09-26", "Trudeau, Justin (Lib.)"),
    ("Woo, Yuen Pau", "ISG", "British Columbia", "2016-11-10", "2038-03-02", "Trudeau, Justin (Lib.)"),
    ("Youance, Suze", "ISG", "Quebec", "2024-09-25", "2045-08-11", "Trudeau, Justin (Lib.)"),
    ("Yussuff, Hassan", "ISG", "Ontario", "2021-06-22", "2031-12-15", "Trudeau, Justin (Lib.)"),
]


def import_senators():
    """Import all senators from SENATORS_DATA into database."""
    print("="*70)
    print("SENATORS IMPORT FROM PDF")
    print("="*70)

    session = Session()

    try:
        # Check existing senators
        existing_count = session.query(Senator).count()
        print(f"\nExisting senators in database: {existing_count}")

        # Import senators
        print(f"\nImporting {len(SENATORS_DATA)} senators from PDF...")

        imported = 0
        skipped = 0
        errors = 0

        for senator_data in SENATORS_DATA:
            name_raw, affiliation, province, nom_date, ret_date, appointed = senator_data

            try:
                # Parse data
                name = parse_senator_name(name_raw)
                nomination_date = parse_date(nom_date)
                retirement_date = parse_date(ret_date)
                appointed_by = parse_appointed_by(appointed)

                # Check if senator already exists
                existing = session.query(Senator).filter_by(name=name).first()
                if existing:
                    skipped += 1
                    print(f"  SKIP: {name} (already exists)")
                    continue

                # Create senator
                senator = Senator(
                    name=name,
                    affiliation=affiliation,
                    province=province,
                    nomination_date=nomination_date,
                    retirement_date=retirement_date,
                    appointed_by=appointed_by
                )

                session.add(senator)
                imported += 1
                print(f"  ✓ {name} ({province}, {affiliation})")

            except Exception as e:
                errors += 1
                print(f"  ERROR: {name_raw} - {e}")
                continue

        # Commit all changes
        session.commit()

        # Summary
        print("\n" + "="*70)
        print("IMPORT COMPLETE")
        print("="*70)
        print(f"  Senators imported: {imported}")
        print(f"  Senators skipped (duplicates): {skipped}")
        print(f"  Errors: {errors}")

        total_senators = session.query(Senator).count()
        print(f"\n  Total senators in database: {total_senators}")

    except Exception as e:
        session.rollback()
        print(f"\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()


if __name__ == "__main__":
    import_senators()
