import json
from datetime import datetime
from create_database import Member, Role, RoleType, Session

# Constants
JSON_PATH = "data/member_roles.json"

def parse_date(date_string):
    """Parse date from string to datetime object."""
    try:
        return datetime.strptime(date_string, '%A, %B %d, %Y').date() if date_string else None
    except ValueError:
        return None

def get_role_date(role_data):
    """Get the appropriate date field based on role type."""
    if role_data['role_type'] == 'Election Candidate':
        return role_data.get('date')
    return role_data.get('start_date')

def insert_roles_from_json(json_path):
    """Insert roles data from JSON file into the database."""
    session = Session()
    
    try:
        with open(json_path, mode='r', encoding='utf-8') as file:
            data = json.load(file)
            
            for member_data in data:
                member_id = int(member_data['member_id'])
                search_pattern = member_data['search_pattern']
                roles = member_data['roles']
                
                # Create or get the member
                member = session.query(Member).filter_by(member_id=member_id).first()
                if not member:
                    member = Member(member_id=member_id, name=search_pattern)
                    session.add(member)
                
                # Get MP roles only and sort by date
                mp_roles = [
                    role for role in roles 
                    if role['role_type'] == 'Member of Parliament' and role.get('start_date')
                ]
                
                if mp_roles:
                    # Sort MP roles by start_date to get the most recent one
                    mp_roles.sort(
                        key=lambda x: parse_date(x['start_date']) or datetime.min.date(), 
                        reverse=True
                    )
                    
                    # Update member's info from most recent MP role
                    most_recent_mp = mp_roles[0]
                    member.constituency = most_recent_mp.get('constituency')
                    member.province_name = most_recent_mp.get('province')
                
                # Get most recent Political Affiliation
                party_roles = [
                    role for role in roles 
                    if role['role_type'] == 'Political Affiliation' and role.get('start_date')
                ]
                
                if party_roles:
                    # Sort party roles by start_date to get the most recent one
                    party_roles.sort(
                        key=lambda x: parse_date(x['start_date']) or datetime.min.date(), 
                        reverse=True
                    )
                    
                    # Update member's party from most recent Political Affiliation
                    member.party = party_roles[0].get('affiliation')
                
                # Commit after updating member
                session.commit()
                
                # Insert all roles for the member
                for role_data in roles:
                    role_type_str = role_data['role_type'].replace(' ', '_').upper()
                    if role_type_str not in RoleType.__members__:
                        print(f"Unknown role type: {role_type_str}")
                        continue
                    
                    # Get the appropriate date based on role type
                    from_date = parse_date(get_role_date(role_data))
                    to_date = parse_date(role_data.get('end_date')) if role_data.get('end_date') else None
                    
                    role = Role(
                        member_id=member.member_id,
                        role_type=RoleType[role_type_str],
                        from_date=from_date,
                        to_date=to_date,
                        parliament_number=role_data.get('parliament_number'),
                        session_number=role_data.get('parliament_session'),
                        constituency_name=role_data.get('constituency') if 'constituency' in role_data else None,
                        constituency_province=role_data.get('province') if 'province' in role_data else None,
                        party=role_data.get('affiliation') if 'affiliation' in role_data else None,
                        committee_name=role_data.get('committee_name') if 'committee_name' in role_data else None,
                        affiliation_role_name=role_data.get('role_name') if 'role_name' in role_data else None,
                        organization_name=role_data.get('organization_name') if 'organization_name' in role_data else None,
                        office_role=role_data.get('office_role') if 'office_role' in role_data else None,
                        election_result=role_data.get('result') if role_type_str == 'ELECTION_CANDIDATE' else None
                    )
                    session.add(role)

            session.commit()
            print(f"Data from {json_path} has been inserted into the database successfully.")

    except FileNotFoundError:
        print(f"Error: JSON file {json_path} not found.")
    except Exception as e:
        session.rollback()
        print(f"An error occurred: {str(e)}")
        print(f"Error details: {type(e).__name__}")
    finally:
        session.close()

if __name__ == "__main__":
    insert_roles_from_json(JSON_PATH)