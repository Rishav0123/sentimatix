import json
import os
from supabase import create_client, Client
from dotenv import load_dotenv
from tqdm import tqdm

# Load environment variables
load_dotenv()
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

def import_stocks(json_file='nse_stocks_formatted.json'):
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("Error: SUPABASE_URL and SUPABASE_KEY must be set in .env")
        return

    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # Load formatted stocks
    with open(json_file, 'r') as f:
        stocks_to_import = json.load(f)
    
    print(f"Loaded {len(stocks_to_import)} stocks from {json_file}")
    
    # Fetch existing symbols to avoid duplicates
    print("Fetching existing stocks from database...")
    existing_stocks = supabase.table('stocks').select('yfin_symbol').execute()
    existing_symbols = {s['yfin_symbol'] for s in existing_stocks.data}
    print(f"Found {len(existing_symbols)} stocks already in database.")
    
    # Filter out existing stocks and prepare for batch insert
    new_stocks = []
    for stock in stocks_to_import:
        if stock['yfin_symbol'] not in existing_symbols:
            # Clean up fields for DB (remove idx, isin, listing_date as they aren't in the schema yet)
            db_stock = {
                'yfin_symbol': stock['yfin_symbol'],
                'stock_name': stock['stock_name'],
                'exchange': stock['exchange'],
                'is_active': False, # Force false as requested
                'country': stock['country'],
                'type': stock['type'],
                'keyword_lst': stock['keyword_lst'],
                'sector': stock['sector'],
                'sentiment_30d': stock['sentiment_30d'],
                'sentiment_7d': stock['sentiment_7d'],
                'mc_link_1': stock['mc_link_1'] if stock['mc_link_1'] else stock['yfin_symbol'],
                'mc_link_2': stock['mc_link_2'] if stock['mc_link_2'] else stock['yfin_symbol'].lower().replace('.ns', '')
            }
            new_stocks.append(db_stock)
    
    if not new_stocks:
        print("No new stocks to import.")
        return
    
    print(f"Ready to import {len(new_stocks)} new stocks...")
    
    # Batch insert in chunks of 100
    chunk_size = 100
    for i in tqdm(range(0, len(new_stocks), chunk_size)):
        chunk = new_stocks[i:i + chunk_size]
        try:
            supabase.table('stocks').insert(chunk).execute()
        except Exception as e:
            print(f"\nError inserting chunk {i//chunk_size}: {e}")
            # Continue to next chunk or handle error
    
    print(f"\nSuccessfully imported {len(new_stocks)} stocks with is_active=False.")

if __name__ == "__main__":
    import_stocks()
