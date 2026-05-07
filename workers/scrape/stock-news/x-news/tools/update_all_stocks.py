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
    with open('full_mapping_directory.json', 'r') as f:
        mapping = json.load(f)
    
    print(f"Updating database with {sum(1 for x in mapping if x['Status'] in ['Matched', 'Verify'])} matched stocks...")
    update_count = 0
    
    # Filter only matched/verified ones
    matched_stocks = [s for s in mapping if s['Status'] in ['Matched', 'Verify'] and s['MC1'] and s['MC2']]
    
    for stock in tqdm(matched_stocks):
        try:
            # Update mc_link_1 and mc_link_2
            # We explicitly update the placeholders
            supabase.table('stocks').update({
                'mc_link_1': stock['MC1'],
                'mc_link_2': stock['MC2'],
                'is_active': False # Keep inactive as requested for new stocks
            }).eq('yfin_symbol', stock['Symbol']).execute()
            update_count += 1
        except Exception as e:
            print(f"Error updating {stock['Symbol']}: {e}")
                
    print(f"\nSuccessfully updated {update_count} stocks in Supabase.")

if __name__ == "__main__":
    update_database()
