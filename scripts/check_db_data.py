
import os
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def check_market_data():
    print("--- Database Data Check ---")
    
    # 1. Latest date in stock_prices
    date_query = supabase.table('stock_prices').select('date').order('date', desc=True).limit(1).execute()
    if not date_query.data:
        print("No stock prices found.")
        return
    
    latest_date = date_query.data[0]['date']
    print(f"Latest data date: {latest_date}")
    
    # 2. Total Volume for latest date
    volume_query = supabase.table('stock_prices').select('volume').eq('date', latest_date).execute()
    total_volume = sum(float(item['volume']) for item in volume_query.data if item['volume'])
    print(f"Total Market Volume on {latest_date}: {total_volume}")
    
    # 3. Sector Performance (Average change_percent per sector)
    # Get all stocks with their sectors
    stocks_query = supabase.table('stocks').select('id, sector').execute()
    sector_map = {item['id']: item['sector'] for item in stocks_query.data}
    
    prices_query = supabase.table('stock_prices').select('stock_id, change_percent').eq('date', latest_date).execute()
    
    sector_perf = {}
    for price in prices_query.data:
        stock_id = price['stock_id']
        change = float(price.get('change_percent', 0) or 0)
        sector = sector_map.get(stock_id, 'Unknown')
        
        if sector not in sector_perf:
            sector_perf[sector] = {'total_change': 0, 'count': 0}
        
        sector_perf[sector]['total_change'] += change
        sector_perf[sector]['count'] += 1
    
    print("\nSector Performance:")
    for sector, data in sector_perf.items():
        avg = data['total_change'] / data['count']
        print(f"- {sector}: {avg:.2f}% ({data['count']} stocks)")
        
    # 4. Check Index table for VIX
    print("\n--- Indices Check ---")
    indices_query = supabase.table('index').select('*').execute()
    for idx in indices_query.data:
        print(f"- {idx['index_name']} ({idx['yfin_symbol']})")

    # 5. Market Composition
    print("\n--- Stocks Table Sample ---")
    stocks_sample = supabase.table('stocks').select('*').limit(1).execute()
    if stocks_sample.data:
        print(f"Columns: {list(stocks_sample.data[0].keys())}")
    
    # Check if we have volume/price info to estimate cap if needed
    # (Actually we need to use real data, so if no cap, we might have to mock that part or find another table)
    # Check if there's a 'market_cap' in any price table
    prices_sample = supabase.table('stock_prices').select('*').limit(1).execute()
    print(f"\nStock Prices Columns: {list(prices_sample.data[0].keys())}")

if __name__ == "__main__":
    check_market_data()
