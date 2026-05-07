import json
import os
from supabase import create_client, Client
from dotenv import load_dotenv
from tqdm import tqdm

# Load environment variables
load_dotenv()
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

def get_supabase_client():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def update_database():
    supabase = get_supabase_client()
    
    # Load mapping
    with open('final_mapping_100.json', 'r') as f:
        mapping = json.load(f)
    
    print("Updating database with matched stocks...")
    update_count = 0
    
    for stock in tqdm(mapping):
        if stock['Status'] == 'Matched' and stock['MC1'] and stock['MC2']:
            try:
                # Update mc_link_1 and mc_link_2
                # Note: We only update if it currently has a placeholder or is NULL
                # (Optional safety check)
                supabase.table('stocks').update({
                    'mc_link_1': stock['MC1'],
                    'mc_link_2': stock['MC2']
                }).eq('yfin_symbol', stock['Symbol']).execute()
                update_count += 1
            except Exception as e:
                print(f"Error updating {stock['Symbol']}: {e}")
                
    print(f"\nSuccessfully updated {update_count} stocks in Supabase.")

if __name__ == "__main__":
    # WARNING: This script modifies the database. 
    # Only run after reviewing the mapping_preview.json
    confirm = input("Are you sure you want to update the database for these 100 stocks? (yes/no): ")
    if confirm.lower() == 'yes':
        update_database()
    else:
        print("Update cancelled.")
