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
                    session.commit()
                    
                # Insert roles for the member
                for role_data in roles:
                    role_type_str = role_data['role_type'].replace(' ', '_').upper()
                    if role_type_str not in RoleType.__members__:
                        print(f"Unknown role type: {role_type_str}")
                        continue
                    
                    role = Role(
                        member_id=member.member_id,
                        role_type=RoleType[role_type_str],
                        from_date=parse_date(role_data.get('start_date')),
                        to_date=parse_date(role_data.get('end_date')),
                        parliament_number=role_data.get('parliament_number'),
                        session_number=role_data.get('parliament_session'),
                        constituency_name=role_data.get('constituency') if 'constituency' in role_data else None,
                        constituency_province=role_data.get('province') if 'province' in role_data else None,
                        caucus_name=role_data.get('affiliation') if 'affiliation' in role_data else None,
                        committee_name=role_data.get('committee_name') if 'committee_name' in role_data else None,
                        affiliation_role_name=role_data.get('role_name') if 'role_name' in role_data else None,
                        organization_name=role_data.get('organization_name') if 'organization_name' in role_data else None,
                        association_role_type=role_data.get('association_role_type') if 'association_role_type' in role_data else None,
                        office_role=role_data.get('office_role') if 'office_role' in role_data else None
                    )
                    session.add(role)

            # Commit all changes
            session.commit()
            print(f"Data from {json_path} has been inserted into the database successfully.")

    except FileNotFoundError:
        print(f"Error: JSON file {json_path} not found.")
    except Exception as e:
        session.rollback()
        print(f"An error occurred: {str(e)}")
    finally:
        session.close()

if __name__ == "__main__":
    insert_roles_from_json(JSON_PATH)