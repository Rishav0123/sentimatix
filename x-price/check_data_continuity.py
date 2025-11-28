#!/usr/bin/env python3
"""
Script to check data continuity for stock prices
"""

import yfinance as yf
from datetime import datetime, UTC, timedelta
import pandas as pd
from utilities.supabase_client import get_supabase_client
from utilities.stock_operations import get_active_stocks

# Initialize Supabase client
supabase = get_supabase_client()

def check_stock_data_continuity(stock_id: str, symbol: str, start_date: str, end_date: str):
    """Check data continuity for a specific stock"""
    try:
        # Get data from database
        response = (supabase.table('stock_prices')
                   .select('date')
                   .eq('stock_id', stock_id)
                   .gte('date', start_date)
                   .lte('date', end_date)
                   .order('date')
                   .execute())
        
        if not response.data:
            print(f"❌ {symbol}: No data found")
            return
        
        # Get trading days from yfinance for comparison
        stock = yf.Ticker(symbol)
        df = stock.history(start=start_date, end=end_date)
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
    """Check data continuity for all active stocks"""
    print("Checking data continuity for all active stocks...")
    print("=" * 60)
    
    # Get active stocks using utility function
    try:
        stocks = get_active_stocks()
        print(f"Found {len(stocks)} active stocks")
        print("=" * 60)
    except Exception as e:
        print(f"Error fetching stocks: {e}")
        return
    
    # Check each stock (showing first 10 as example)
    start_date = "2025-10-14"  # Start from your earliest data
    end_date = "2025-11-01"    # End at current date
    
    print(f"Checking data from {start_date} to {end_date}")
    print("-" * 60)
    
    for i, stock in enumerate(stocks):  # Check all stocks
        check_stock_data_continuity(stock['id'], stock['yfin_symbol'], start_date, end_date)
        
    print("-" * 60)
    print("✅ Check complete! All stocks analyzed")

if __name__ == "__main__":
    main()