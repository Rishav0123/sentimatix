#!/usr/bin/env python3
"""
Script to check data continuity for index prices
Similar to check_data_continuity.py but for indices
"""

import yfinance as yf
from datetime import datetime, UTC, timedelta
import pandas as pd
from utilities.supabase_client import get_supabase_client
from utilities.index_operations import get_indices_with_symbols

# Initialize Supabase client
supabase = get_supabase_client()

def check_index_data_continuity(index_id: str, symbol: str, start_date: str, end_date: str):
    """Check data continuity for a specific index"""
    try:
        # Get data from database (index data is stored in stock_prices table with index_id as stock_id)
        response = (supabase.table('stock_prices')
                   .select('date')
                   .eq('stock_id', index_id)  # index_id is stored as stock_id
                   .gte('date', start_date)
                   .lte('date', end_date)
                   .order('date')
                   .execute())
        
        if not response.data:
            print(f"❌ {symbol}: No data found")
            return
        
        # Get trading days from yfinance for comparison
        index_ticker = yf.Ticker(symbol)
        df = index_ticker.history(start=start_date, end=end_date)
        trading_days = [date.date().isoformat() for date in df.index]
        
        # Get dates from database
        db_dates = [row['date'] for row in response.data]
        
        # Find missing dates
        missing_dates = set(trading_days) - set(db_dates)
        
        if missing_dates:
            print(f"⚠️  {symbol}: Missing {len(missing_dates)} dates: {sorted(missing_dates)}")
        else:
            print(f"✅ {symbol}: Complete data ({len(db_dates)} days)")
            
    except Exception as e:
        print(f"❌ {symbol}: Error checking data - {e}")

def main():
    """Check data continuity for all indices with symbols"""
    print("Checking data continuity for all indices...")
    print("=" * 60)
    
    # Get indices with symbols using utility function
    try:
        indices = get_indices_with_symbols()
        print(f"Found {len(indices)} indices with yfinance symbols")
        print("=" * 60)
    except Exception as e:
        print(f"Error fetching indices: {e}")
        return
    
    # Check each index
    start_date = "2025-10-14"  # Start from your earliest data
    end_date = "2025-11-01"    # End at current date
    
    print(f"Checking data from {start_date} to {end_date}")
    print("-" * 60)
    
    for index in indices:
        if index.get('yfin_symbol'):
            check_index_data_continuity(
                index['id'], 
                index['yfin_symbol'], 
                start_date, 
                end_date
            )
        else:
            print(f"⚠️  {index.get('index_name', 'Unknown')}: No yfinance symbol")
        
    print("-" * 60)
    print("✅ Check complete! All indices analyzed")

if __name__ == "__main__":
    main()