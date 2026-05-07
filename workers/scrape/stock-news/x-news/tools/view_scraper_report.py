import os
import json
from supabase import create_client
from dotenv import load_dotenv
from datetime import datetime

def view_latest_reports():
    load_dotenv()
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_KEY')
    supabase = create_client(url, key)
    
    # Get the latest run_id from the reports
    try:
        latest_res = supabase.table('scraper_reports').select('run_id').order('timestamp', desc=True).limit(1).execute()
        if not latest_res.data:
            print("No scraper reports found in the database.")
            return
        
        latest_run_id = latest_res.data[0]['run_id']
        
        # Get all reports for this run_id
        reports_res = supabase.table('scraper_reports').select('*').eq('run_id', latest_run_id).execute()
        reports = reports_res.data
        
        # Aggregate all stocks found in these reports
        all_stocks = set()
        for r in reports:
            all_stocks.update(r['stock_counts'].keys())
            
        # Filter for top stocks or just show a reasonable number
        sorted_stocks = sorted(list(all_stocks))[:15] # Show first 15 for readability
        
        # Header
        header = f"{'Scraper':<15}"
        for stock in sorted_stocks:
            # Show only the prefix of the symbol
            short_stock = stock.split('.')[0]
            header += f" | {short_stock:<8}"
        
        print("\n" + "=" * len(header))
        print(f"SCRAPER RUN REPORT - Run ID: {latest_run_id}")
        print(f"Timestamp: {reports[0]['timestamp']}")
        print("=" * len(header))
        print(header)
        print("-" * len(header))
        
        for r in reports:
            row = f"{r['scraper_name']:<15}"
            counts = r['stock_counts']
            for stock in sorted_stocks:
                val = counts.get(stock, 0)
                row += f" | {val:<8}"
            print(row)
        print("=" * len(header) + "\n")
        
    except Exception as e:
        print(f"Error fetching reports: {e}")

if __name__ == "__main__":
    view_latest_reports()
