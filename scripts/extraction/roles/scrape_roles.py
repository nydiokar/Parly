import requests
import xml.etree.ElementTree as ET
import csv
import json
import time


# Constants
CSV_PATH = "data/member_ids.csv"
OUTPUT_PATH = "data/member_roles.json"

def fetch_member_roles_xml(search_pattern):
    """Fetch XML data for a member's roles from the public URL."""
    url = f"https://www.ourcommons.ca/members/en/{search_pattern}/roles/xml"
    print(f"Fetching URL: {url}")
    time.sleep(1)
    response = requests.get(url)
    if response.status_code == 200:
        return response.content
    else:
        print(f"Failed to fetch data for member {search_pattern}, Status code: {response.status_code}")
        return None

def parse_roles_xml(xml_data):
    """Parse the fetched XML data to extract roles information and member name."""
    roles = []
    member_name = None

    try:
        root = ET.fromstring(xml_data)

        # Extract member name from first MemberOfParliamentRole
        mp_roles = root.findall('.//MemberOfParliamentRole')
        if mp_roles:
            first_mp = mp_roles[0]
            first_name = first_mp.find('PersonOfficialFirstName')
            last_name = first_mp.find('PersonOfficialLastName')
            if first_name is not None and last_name is not None:
                member_name = f"{first_name.text} {last_name.text}"

        # Extract Member of Parliament roles
        for mp_role in mp_roles:
            constituency = mp_role.find('ConstituencyName')
            province = mp_role.find('ConstituencyProvinceTerritoryName')
            from_date = mp_role.find('FromDateTime')
            to_date = mp_role.find('ToDateTime')

            role = {
                "role_type": "Member of Parliament",
                "constituency": constituency.text if constituency is not None else None,
                "province": province.text if province is not None else None,
                "start_date": from_date.text.split('T')[0] if from_date is not None else None,
                "end_date": to_date.text.split('T')[0] if to_date is not None and to_date.get('{http://www.w3.org/2001/XMLSchema-instance}nil') != 'true' else ""
            }
            roles.append(role)

        # Extract Political Affiliation (CaucusMemberRoles)
        caucus_roles = root.findall('.//CaucusMemberRole')
        for caucus_role in caucus_roles:
            caucus_name = caucus_role.find('CaucusShortName')
            from_date = caucus_role.find('FromDateTime')
            to_date = caucus_role.find('ToDateTime')
            parliament_num = caucus_role.find('ParliamentNumber')

            role = {
                "role_type": "Political Affiliation",
                "parliament_number": parliament_num.text if parliament_num is not None else None,
                "affiliation": caucus_name.text if caucus_name is not None else None,
                "start_date": from_date.text.split('T')[0] if from_date is not None else None,
                "end_date": to_date.text.split('T')[0] if to_date is not None and to_date.get('{http://www.w3.org/2001/XMLSchema-instance}nil') != 'true' else ""
            }
            roles.append(role)

        # Extract Committee roles
        committee_roles = root.findall('.//CommitteeMemberRole')
        for committee_role in committee_roles:
            parliament_num = committee_role.find('ParliamentNumber')
            session_num = committee_role.find('SessionNumber')
            affiliation_role = committee_role.find('AffiliationRoleName')
            committee_name = committee_role.find('CommitteeName')
            from_date = committee_role.find('FromDateTime')
            to_date = committee_role.find('ToDateTime')

            # Construct parliament_session string
            parliament_session = None
            if parliament_num is not None and session_num is not None:
                parliament_session = f"{parliament_num.text}-{session_num.text}"

            role = {
                "role_type": "Committee Member",
                "parliament_session": parliament_session,
                "role_name": affiliation_role.text if affiliation_role is not None else None,
                "committee_name": committee_name.text if committee_name is not None else None,
                "start_date": from_date.text.split('T')[0] if from_date is not None else None,
                "end_date": to_date.text.split('T')[0] if to_date is not None and to_date.get('{http://www.w3.org/2001/XMLSchema-instance}nil') != 'true' else ""
            }
            roles.append(role)

        # Extract Parliamentary Associations and Interparliamentary Groups
        association_roles = root.findall('.//ParliamentaryAssociationsandInterparliamentaryGroupRole')
        for assoc_role in association_roles:
            role_type_elem = assoc_role.find('AssociationMemberRoleType')
            title_elem = assoc_role.find('Title')
            org_elem = assoc_role.find('Organization')

            role = {
                "role_type": "Parliamentary Association",
                "role_name": role_type_elem.text if role_type_elem is not None else None,
                "organization_name": org_elem.text if org_elem is not None else None,
                "start_date": None,  # XML doesn't have dates for associations
                "end_date": ""
            }
            roles.append(role)

        # Extract Election Candidate roles
        election_roles = root.findall('.//ElectionCandidateRole')
        for election_role in election_roles:
            election_type = election_role.find('ElectionEventTypeName')
            election_date = election_role.find('ElectionEndDate')
            constituency = election_role.find('ConstituencyName')
            province = election_role.find('ConstituencyProvinceTerritoryName')
            party = election_role.find('PoliticalPartyName')
            result = election_role.find('ResolvedElectionResultTypeName')

            role = {
                "role_type": "Election Candidate",
                "date": election_date.text.split('T')[0] if election_date is not None else None,
                "election_type": election_type.text if election_type is not None else None,
                "constituency": constituency.text if constituency is not None else None,
                "province": province.text if province is not None else None,
                "party": party.text if party is not None else None,
                "result": result.text if result is not None else None
            }
            roles.append(role)

        # Extract Parliamentary Position/Office roles
        position_roles = root.findall('.//ParliamentaryPositionRole')
        for position_role in position_roles:
            parliament_num = position_role.find('ParliamentNumber')
            office_role = position_role.find('PositionName')
            from_date = position_role.find('FromDateTime')
            to_date = position_role.find('ToDateTime')

            role = {
                "role_type": "Parliamentarian Office",
                "parliament_number": parliament_num.text if parliament_num is not None else None,
                "office_role": office_role.text if office_role is not None else None,
                "start_date": from_date.text.split('T')[0] if from_date is not None else None,
                "end_date": to_date.text.split('T')[0] if to_date is not None and to_date.get('{http://www.w3.org/2001/XMLSchema-instance}nil') != 'true' else ""
            }
            roles.append(role)

    except ET.ParseError as e:
        print(f"Error parsing XML: {e}")
        return None, []

    return member_name, roles

def main():
    """Fetch and parse roles for all members from the CSV file."""
    try:
        all_roles = []
        with open(CSV_PATH, mode='r', encoding='utf-8') as csv_file:
            csv_reader = csv.DictReader(csv_file)
            for row in csv_reader:
                search_pattern = row['search_pattern']
                member_id = row['id']
                csv_member_name = row['name']  # Fallback name from CSV

                # Step 1: Fetch XML data for the member's roles
                xml_data = fetch_member_roles_xml(search_pattern)
                if not xml_data:
                    continue

                # Step 2: Parse roles from XML and extract member name
                member_name, roles = parse_roles_xml(xml_data)

                # Use CSV name as fallback if XML didn't have name
                if not member_name:
                    member_name = csv_member_name
                    print(f"Warning: Using CSV name for member {member_id}")

                if roles:
                    all_roles.append({
                        "member_id": member_id,
                        "member_name": member_name,  # Now includes actual name!
                        "search_pattern": search_pattern,
                        "roles": roles
                    })
                else:
                    print(f"No roles found for {member_name} ({member_id})")

        # Step 3: Write roles to a JSON file
        with open(OUTPUT_PATH, mode='w', encoding='utf-8') as output_file:
            json.dump(all_roles, output_file, indent=2, ensure_ascii=False)
        print(f"\nRoles data has been written to {OUTPUT_PATH}")
        print(f"Total members processed: {len(all_roles)}")

    except FileNotFoundError:
        print("Error: member_ids.csv file not found in data directory")
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
