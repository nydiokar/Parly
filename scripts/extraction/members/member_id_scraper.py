# File: scripts/extraction/member_id_scraper.py

import requests
from bs4 import BeautifulSoup
import re
import pandas as pd

class MemberIdScraper:
    def __init__(self):
        self.base_url = "https://www.ourcommons.ca/members/en/search?view=list"
        self.member_data = {}
    
    def scrape_member_ids(self):
        # Step 1: Get HTML content from the search page
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        response = requests.get(self.base_url, headers=headers)
        if response.status_code != 200:
            print(f"Failed to fetch member list page. Status Code: {response.status_code}")
            return

        print("Successfully fetched member list page.")
        
        soup = BeautifulSoup(response.content, 'html.parser')

        # Step 2: Find all links and print them to understand their structure
        member_links = soup.find_all('a', href=True)

        # Print the first 20 links to see what we're dealing with
        print("\nPrinting the first 20 links found on the page for inspection:")
        for link in member_links[:20]:
            print(link['href'])

        # Step 3: Filter links for unique member profiles only (ignoring constituency links)
        for link in member_links:
            href = link['href']
            # Debugging to see if the filter works correctly
            if "/Members/en/" in href and re.search(r"-\d+$", href):
                print(f"Potential member profile link found: {href}")
                # Use regex to capture member name and ID from the URL
                match = re.search(r"/Members/en/(.*)-(\d+)", href)
                if match:
                    member_name = match.group(1).replace('-', ' ')
                    member_id = match.group(2)
                    # Normalize name to title case
                    normalized_name = member_name.title()

                    # Using member ID as the unique key in a dictionary to ensure no duplicates
                    self.member_data[member_id] = {
                        'name': normalized_name,
                        'id': member_id,
                        'profile_url': f"https://www.ourcommons.ca{href}"
                    }

        # Debugging to confirm the number of unique members found
        print(f"Total unique members extracted: {len(self.member_data)}")

    def save_to_csv(self, filepath='data/member_ids.csv'):
        if not self.member_data:
            print("No member data found to save. Please check the extraction step.")
            return

        # Convert the dictionary values to a DataFrame
        df = pd.DataFrame(list(self.member_data.values()))
        
        # Save the data to a CSV file
        df.to_csv(filepath, index=False)
        print(f"Member IDs and names saved to {filepath}")

# Run the scraper
if __name__ == "__main__":
    scraper = MemberIdScraper()
    scraper.scrape_member_ids()
    scraper.save_to_csv()
