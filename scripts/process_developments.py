"""
Hourly Worker: Process Stock Developments
Runs every hour to identify and store key developments from recent news
"""

import sys
import os
from datetime import datetime
from pathlib import Path

# Add mcp directory to path for imports
mcp_path = str(Path(__file__).parent.parent / 'mcp')
sys.path.insert(0, mcp_path)

from tools.identify_developments import process_stock_developments
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent / 'mcp' / '.env'
load_dotenv(env_path)

# Initialize Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Missing SUPABASE_URL or SUPABASE_KEY in environment")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def get_active_stocks():
    """Get list of active stock symbols to process"""
    response = supabase.table('stocks') \
        .select('yfin_symbol') \
        .eq('is_active', True) \
        .execute()
    
    return [stock['yfin_symbol'].replace('.NS', '') for stock in response.data]


def process_all_stocks():
    """Process developments for all active stocks"""
    print(f"\n{'='*60}")
    print(f"Stock Developments Processor - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    stocks = get_active_stocks()
    print(f"Processing {len(stocks)} stocks...")
    
    total_developments = 0
    processed_stocks = 0
    
    for symbol in stocks:
        try:
            result = process_stock_developments(symbol)
            
            if result['developments_found'] > 0:
                processed_stocks += 1
                total_developments += result['developments_found']
                print(f"✓ {symbol}: {result['developments_found']} developments")
                
                # Print development details
                for dev in result['developments']:
                    print(f"    [{dev['category'].upper()}] {dev['title'][:60]}...")
            else:
                print(f"  {symbol}: No new developments")
                
        except Exception as e:
            print(f"✗ {symbol}: Error - {str(e)}")
    
    print(f"\n{'='*60}")
    print(f"Summary:")
    print(f"  Stocks processed: {len(stocks)}")
    print(f"  Stocks with developments: {processed_stocks}")
    print(f"  Total developments found: {total_developments}")
    print(f"{'='*60}\n")


if __name__ == '__main__':
    process_all_stocks()
