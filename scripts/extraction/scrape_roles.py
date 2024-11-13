import requests
from bs4 import BeautifulSoup
import csv
import json
import time


# Constants
CSV_PATH = "data/member_ids.csv"
OUTPUT_PATH = "data/member_roles.json"

def fetch_member_roles_page(search_pattern):
    """Fetch HTML data for a member's roles from the public URL."""
    url = f"https://www.ourcommons.ca/members/en/{search_pattern}/roles"
    print(f"Fetching URL: {url}")
    time.sleep(1)
    response = requests.get(url)
    if response.status_code == 200:
        return response.content
    else:
        print(f"Failed to fetch data for member {search_pattern}, Status code: {response.status_code}")
        return None

def parse_roles(html_data):
    """Parse the fetched HTML data to extract roles information."""
    roles = []
    soup = BeautifulSoup(html_data, 'html.parser')

    # Extract Member of Parliament roles
    mp_section_header = soup.find('h2', string='Member of Parliament')
    if mp_section_header:
        mp_section = mp_section_header.find_next('table')
        if mp_section:
            rows = mp_section.find_all('tr')
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 4:
                    constituency = cells[0].get_text(strip=True)
                    province = cells[1].get_text(strip=True)
                    start_date = cells[2].get_text(strip=True)
                    end_date = cells[3].get_text(strip=True) if len(cells) > 3 else None

                    roles.append({
                        "role_type": "Member of Parliament",
                        "constituency": constituency,
                        "province": province,
                        "start_date": start_date,
                        "end_date": end_date
                    })

    # Extract Political Affiliation roles
    affiliation_section_header = soup.find('h2', string='Political Affiliation')
    if affiliation_section_header:
        affiliation_section = affiliation_section_header.find_next('table')
        if affiliation_section:
            rows = affiliation_section.find_all('tr')
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 3:
                    parliament_number = cells[0].get_text(strip=True)
                    affiliation = cells[1].get_text(strip=True)
                    start_date = cells[2].get_text(strip=True)
                    end_date = cells[3].get_text(strip=True) if len(cells) > 3 else None

                    roles.append({
                        "role_type": "Political Affiliation",
                        "parliament_number": parliament_number,
                        "affiliation": affiliation,
                        "start_date": start_date,
                        "end_date": end_date
                    })

    # Extract Committee roles
    committee_section_header = soup.find('h2', string='Committees')
    if committee_section_header:
        committee_section = committee_section_header.find_next('table')
        if committee_section:
            rows = committee_section.find_all('tr')
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 5:
                    parliament_session = cells[0].get_text(strip=True)
                    role_name = cells[1].get_text(strip=True)
                    committee_name = cells[2].get_text(strip=True)
                    start_date = cells[3].get_text(strip=True)
                    end_date = cells[4].get_text(strip=True) if len(cells) > 4 else None

                    roles.append({
                        "role_type": "Committee Member",
                        "parliament_session": parliament_session,
                        "role_name": role_name,
                        "committee_name": committee_name,
                        "start_date": start_date,
                        "end_date": end_date
                    })

    # Extract Parliamentary Associations and Interparliamentary Groups roles
    parliamentary_section_header = soup.find('h2', string='Parliamentary Associations and Interparliamentary Groups')
    if parliamentary_section_header:
        parliamentary_section = parliamentary_section_header.find_next('table')
        if parliamentary_section:
            rows = parliamentary_section.find_all('tr')
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 5:
                    parliament_number = cells[0].get_text(strip=True)
                    role_name = cells[1].get_text(strip=True)
                    organization_name = cells[2].get_text(strip=True)
                    start_date = cells[3].get_text(strip=True)
                    end_date = cells[4].get_text(strip=True) if len(cells) > 4 else None

                    roles.append({
                        "role_type": "Parliamentary Association",
                        "parliament_number": parliament_number,
                        "role_name": role_name,
                        "organization_name": organization_name,
                        "start_date": start_date,
                        "end_date": end_date
                    })

    # Extract Election Candidate roles
    election_section_header = soup.find('h2', string='Election Candidate')
    if election_section_header:
        election_section = election_section_header.find_next('table')
        if election_section:
            rows = election_section.find_all('tr')
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 4:
                    date = cells[0].get_text(strip=True)
                    election_type = cells[1].get_text(strip=True)
                    constituency = cells[2].get_text(strip=True)
                    province = cells[3].get_text(strip=True)
                    result = cells[4].get_text(strip=True) if len(cells) > 4 else None

                    roles.append({
                        "role_type": "Election Candidate",
                        "date": date,
                        "election_type": election_type,
                        "constituency": constituency,
                        "province": province,
                        "result": result
                    })

    # Extract Offices and Roles as a Parliamentarian
    office_roles_section_header = soup.find('h2', string='Offices and Roles as a Parliamentarian')
    if office_roles_section_header:
        office_roles_section = office_roles_section_header.find_next('table')
        if office_roles_section:
            rows = office_roles_section.find_all('tr')
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 4:
                    parliament_number = cells[0].get_text(strip=True)
                    office_role = cells[1].get_text(strip=True)
                    start_date = cells[2].get_text(strip=True)
                    end_date = cells[3].get_text(strip=True) if len(cells) > 3 else None

                    roles.append({
                        "role_type": "Parliamentarian Office",
                        "parliament_number": parliament_number,
                        "office_role": office_role,
                        "start_date": start_date,
                        "end_date": end_date
                    })

    # Debug: If no roles were found, indicate this
    if not roles:
        print("No roles found in the HTML data.")
    return roles

def main():
    """Fetch and parse roles for all members from the CSV file."""
    try:
        all_roles = []
        with open(CSV_PATH, mode='r') as csv_file:
            csv_reader = csv.DictReader(csv_file)
            for row in csv_reader:
                search_pattern = row['search_pattern']
                member_id = row['id']

                # Step 1: Fetch HTML data for the member's roles
                html_data = fetch_member_roles_page(search_pattern)
                if not html_data:
                    continue

                # Step 2: Parse roles from HTML
                roles = parse_roles(html_data)
                if roles:
                    all_roles.append({
                        "member_id": member_id,
                        "search_pattern": search_pattern,
                        "roles": roles
                    })

        # Step 3: Write roles to a JSON file
        with open(OUTPUT_PATH, mode='w', encoding='utf-8') as output_file:
            json.dump(all_roles, output_file, indent=2, ensure_ascii=False)
        print(f"Roles data has been written to {OUTPUT_PATH}")

    except FileNotFoundError:
        print("Error: member_ids.csv file not found in data directory")
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")

if __name__ == "__main__":
    main()
