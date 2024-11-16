import requests
import xml.etree.ElementTree as ET
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
import time
from db_setup.url_templates import URL_TEMPLATES
    
#use db_setup.all_bills for all bills data - it;s json
#CLASSES needed?

# Configurations
MAX_THREADS = 5  # Number of concurrent threads to control request volume
TIMEOUT = 10  # Timeout in seconds for each request

# Utility functions for secure and efficient fetching

def safe_request(url):
    """
    Make a request with a retry mechanism to avoid transient failures.
    """
    retries = 3
    for i in range(retries):
        try:
            response = requests.get(url, timeout=TIMEOUT)
            if response.status_code == 200:
                return response.content
            else:
                print(f"Failed with status code: {response.status_code} on attempt {i+1}")
        except requests.RequestException as e:
            print(f"Error occurred: {e}, retrying ({i+1}/{retries})")
            time.sleep(2 ** i)  # Exponential backoff
    return None

# Fetch member votes

def fetch_member_votes(member_id):
    url = URL_TEMPLATES['member_votes'].format(search_pattern=f"ziad-aboultaif({member_id})")
    xml_data = safe_request(url)
    if xml_data is None:
        return None
    return parse_votes(xml_data)

# Parse member votes from XML

def parse_votes(xml_data):
    root = ET.fromstring(xml_data)
    votes = []
    for member_vote in root.findall('MemberVote'):
        vote = {
            'ParliamentNumber': member_vote.find('ParliamentNumber').text,
            'SessionNumber': member_vote.find('SessionNumber').text,
            'DecisionEventDateTime': member_vote.find('DecisionEventDateTime').text,
            'DecisionDivisionNumber': member_vote.find('DecisionDivisionNumber').text,
            'DecisionDivisionSubject': member_vote.find('DecisionDivisionSubject').text,
            'DecisionResultName': member_vote.find('DecisionResultName').text,
            'DecisionDivisionNumberOfYeas': member_vote.find('DecisionDivisionNumberOfYeas').text,
            'DecisionDivisionNumberOfNays': member_vote.find('DecisionDivisionNumberOfNays').text,
            'DecisionDivisionNumberOfPaired': member_vote.find('DecisionDivisionNumberOfPaired').text,
            'VoteValueName': member_vote.find('VoteValueName').text,
            'IsVoteYea': member_vote.find('IsVoteYea').text,
            'IsVoteNay': member_vote.find('IsVoteNay').text,
            'IsVotePaired': member_vote.find('IsVotePaired').text,
        }
        votes.append(vote)
    return votes

# Fetch detailed vote information

def fetch_vote_details(vote_id):
    url = URL_TEMPLATES['vote_details'].format(vote_id=vote_id) ## WHAT IS THIS vote_details? 
    xml_data = safe_request(url)
    if xml_data is None:
        return None
    return parse_vote_details(xml_data)

# Parse detailed vote information from XML

def parse_vote_details(xml_data):
    root = ET.fromstring(xml_data)
    details = []
    for member in root.findall('Vote/Member'):  # Adjust based on actual XML structure
        detail = {
            'MemberName': member.find('MemberName').text,
            'PoliticalAffiliation': member.find('PoliticalAffiliation').text, #IS IT NEEDED?
            'MemberVote': member.find('VoteValue').text,
            'Paired': member.find('Paired').text,
        }
        details.append(detail)
    return details

# Combine the data

def gather_all_data(member_id):
    # Fetch member votes first
    member_votes = fetch_member_votes(member_id)
    if not member_votes:
        print("No votes found for member.")
        return None

    combined_data = []
    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        futures = []
        for vote in member_votes:
            vote_id = vote['DecisionDivisionNumber']
            futures.append(executor.submit(fetch_vote_details, vote_id))
        for future in tqdm(futures, desc="Fetching detailed votes"):
            details = future.result()
            if details:
                combined_data.extend(details)
    return combined_data

# Main execution

def main():
    member_id = 89156  # Example member ID
    combined_data = gather_all_data(member_id)
    if combined_data:
        # Convert to DataFrame for better representation and analysis 
        df = pd.DataFrame(combined_data)
        print(df.head()) #PRETTYPRINT? 

if __name__ == "__main__":
    main()
