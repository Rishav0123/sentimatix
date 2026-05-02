import os
import json
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

def check_overlap():
    # Load our new mapping
    with open('final_mapping_100.json', 'r') as f:
        mapped = json.load(f)
    
    # Get symbols from mapping
    symbols = [m['Symbol'] for m in mapped]
    
    # Fetch current DB state for these symbols
    response = supabase.table('stocks').select('yfin_symbol, mc_link_1, mc_link_2').in_('yfin_symbol', symbols).execute()
    db_stocks = {x['yfin_symbol']: x for x in response.data}
    
    already_proper = 0
    updated_needed = 0
    missing_in_db = 0
    
    for m in mapped:
        symbol = m['Symbol']
        if symbol in db_stocks:
            cur = db_stocks[symbol]
            # A link is "proper" if it doesn't end with .NS (our placeholder)
            is_placeholder = cur['mc_link_1'].endswith('.NS')
            
            if not is_placeholder:
                already_proper += 1
            elif m['MC1']: # If it's a placeholder and we found a match
                updated_needed += 1
        else:
            missing_in_db += 1
            
    print(f"Total in Batch: {len(mapped)}")
    print(f"Already had proper links: {already_proper}")
    print(f"Placeholder links (need update): {updated_needed}")
    print(f"No match found in our script: {len(mapped) - already_proper - updated_needed}")

if __name__ == "__main__":
    check_overlap()
