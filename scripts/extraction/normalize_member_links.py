import pandas as pd

class MemberDataConverter:
    def __init__(self, input_file='data/all_links.txt', output_file='data/member_ids.csv'):
        self.input_file = input_file
        self.output_file = output_file
        self.member_data = []

    def convert_and_normalize(self):
        try:
            # Step 1: Read all lines from the input text file
            with open(self.input_file, 'r') as file:
                all_lines = file.readlines()

            print(f"Total members read from file: {len(all_lines)}")

            # Step 2: Process each line to extract relevant data
            for line in all_lines:
                line = line.strip()

                if "/members/en/" in line:
                    # Extract just the last part after /members/en/
                    parts = line.split('/members/en/')[-1]
                    
                    # Split on the last hyphen before the parenthesis
                    member_name = parts[:parts.find('(')]
                    member_id = parts[parts.find('(')+1:parts.find(')')]

                    # Normalize the name (capitalize each word)
                    normalized_name = member_name.replace('-', ' ').title()

                    # Create search pattern without the /members/en/ prefix
                    search_pattern = f"{member_name}({member_id})"

                    self.member_data.append({
                        'name': normalized_name,
                        'id': member_id,
                        'search_pattern': search_pattern
                    })

                    # Debug: Print successfully processed member info
                    print(f"Processed: Name={normalized_name}, ID={member_id}, Search Pattern={search_pattern}")
                else:
                    # Debug: Print if line does not match expected pattern
                    print(f"Line does not match expected pattern: {line}")

            # Debugging: Confirm the number of members processed
            print(f"Total members processed: {len(self.member_data)}")

        except FileNotFoundError:
            print(f"Error: File {self.input_file} not found.")
        except Exception as e:
            print(f"An error occurred: {e}")

    def save_to_csv(self):
        if not self.member_data:
            print("No member data found to save. Please check the extraction step.")
            return

        # Convert the list of dictionaries to a DataFrame
        df = pd.DataFrame(self.member_data)
        
        # Save the data to a CSV file
        df.to_csv(self.output_file, index=False)
        print(f"Member data saved to {self.output_file}")

# Run the converter
if __name__ == "__main__":
    converter = MemberDataConverter()
    converter.convert_and_normalize()
    converter.save_to_csv()
