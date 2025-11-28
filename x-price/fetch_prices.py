import yfinance as yf
from datetime import datetime, UTC, timedelta
import pandas as pd
import time
import sys
from pathlib import Path
from utilities.stock_operations import get_active_stocks
from utilities.price_operations import get_last_price_date, insert_price_data
from utilities.logging_utils import log_message

def get_active_stocks_with_logging():
    """Fetch active stocks with logging"""
    try:
        stocks = get_active_stocks()
        log_message(f"Found {len(stocks)} active stocks")
        
        # Log first few stocks for debugging
        if stocks:
            log_message(f"Sample stocks: {stocks[:3]}")
        
        return stocks
    except Exception as e:
        error_msg = f"Error fetching stocks: {e}"
        log_message(error_msg, "ERROR")
        return []

def fetch_stock_prices(stock_id: str, yfin_symbol: str):
    """Fetch stock prices from yfinance and store in Supabase
    
    Args:
        stock_id (str): ID of the stock in the database
        yfin_symbol (str): yfinance symbol (e.g., 'BAJFINANCE.NS')
    """
    try:
        log_message(f"Fetching data for {yfin_symbol}...")
        
        # Get the last date we have data for this stock
        try:
            last_date = get_last_price_date(stock_id)
            
            if last_date:
                # Start from the day after the last date
                start_date = last_date + timedelta(days=1)
                log_message(f"Last date in database: {last_date}, starting from: {start_date}")
            else:
                # No data exists, fetch from 30 days ago
                start_date = (datetime.now(UTC) - timedelta(days=30)).date()
                log_message(f"No existing data found, starting from: {start_date}")
                
        except Exception as e:
            log_message(f"Error checking last date for {yfin_symbol}: {e}", "WARNING")
            # Fallback to 7 days ago
            start_date = (datetime.now(UTC) - timedelta(days=7)).date()
            log_message(f"Using fallback start date: {start_date}")
        
        # Create a Ticker object
        stock = yf.Ticker(yfin_symbol)
        
        # Get today's date
        end_date = datetime.now(UTC).date()
        
        # Check if we need to fetch any data
        if start_date > end_date:
            log_message(f"No new data to fetch for {yfin_symbol} (start_date: {start_date} > end_date: {end_date})")
            return
        
        # Fetch history
        log_message(f"Fetching history from {start_date} to {end_date}")
        
        try:
            df = stock.history(start=start_date, end=end_date + timedelta(days=1))  # Add 1 day to include end_date
        except Exception as fetch_error:
            log_message(f"yfinance error for {yfin_symbol}: {fetch_error}", "ERROR")
            return
        
        if df.empty:
            log_message(f"No data received for {yfin_symbol} - symbol may be delisted or invalid", "WARNING")
            return
            
        log_message(f"Successfully fetched {len(df)} days of data for {yfin_symbol}")
        
        # Check if we have valid data
        if df.isnull().all().all():
            log_message(f"All data is null for {yfin_symbol}", "WARNING")
            return
        
        # Process each day's data
        successful_rows = 0
        failed_rows = 0
        
        for date, row in df.iterrows():
            try:
                # Check if the row has valid data
                if pd.isna(row['Close']) or row['Close'] <= 0:
                    log_message(f"Invalid price data for {yfin_symbol} on {date.date()}: Close={row['Close']}", "WARNING")
                    failed_rows += 1
                    continue
                
                # Prepare price data for database
                price_data = {
                    "stock_id": stock_id,
                    "date": date.date().isoformat(),
                    "open": float(row['Open']) if not pd.isna(row['Open']) else None,
                    "high": float(row['High']) if not pd.isna(row['High']) else None,
                    "low": float(row['Low']) if not pd.isna(row['Low']) else None,
                    "close": float(row['Close']) if not pd.isna(row['Close']) else None,
                    "volume": int(row['Volume']) if not pd.isna(row['Volume']) else 0,
                    "dividends": float(row['Dividends']) if not pd.isna(row['Dividends']) else 0.0,
                    "stock_splits": float(row['Stock Splits']) if not pd.isna(row['Stock Splits']) else 0.0,
                    "updated_at": datetime.now(UTC).isoformat()
                }
                
                try:
                    # Use upsert to handle duplicates based on primary key
                    success = insert_price_data(price_data)
                    
                    if success:
                        successful_rows += 1
                        log_message(f"Successfully stored price for {yfin_symbol} on {date.date()}")
                    else:
                        failed_rows += 1
                        log_message(f"Failed to store price for {yfin_symbol} on {date.date()}", "WARNING")
                        
                except Exception as e:
                    failed_rows += 1
                    log_message(f"Error storing price for {yfin_symbol} on {date.date()}: {e}", "ERROR")
            
            except Exception as e:
                failed_rows += 1
                log_message(f"Error processing row for {yfin_symbol} on {date.date()}: {e}", "ERROR")
                continue
        
        log_message(f"Completed processing {yfin_symbol}: {successful_rows} successful, {failed_rows} failed")
        
    except Exception as e:
        log_message(f"Unexpected error fetching data for {yfin_symbol}: {e}", "ERROR")

def backfill_missing_data(start_date_str: str, end_date_str: str):
    """Backfill missing data for a specific date range
    
    Args:
        start_date_str (str): Start date in YYYY-MM-DD format
        end_date_str (str): End date in YYYY-MM-DD format
    """
    try:
        start_date = datetime.fromisoformat(start_date_str).date()
        end_date = datetime.fromisoformat(end_date_str).date()
        
        log_message(f"Starting backfill from {start_date} to {end_date}")
        
        stocks = get_active_stocks_with_logging()
        if not stocks:
            log_message("No active stocks found", "WARNING")
            return
        
        successful_stocks = 0
        failed_stocks = 0
        
        for stock in stocks:
            if not stock.get('yfin_symbol'):
                continue
                
            try:
                log_message(f"\nBackfilling {stock['stock_name']} ({stock['yfin_symbol']})")
                
                # Create a Ticker object
                stock_ticker = yf.Ticker(stock['yfin_symbol'])
                
                # Fetch history for the specified range
                df = stock_ticker.history(start=start_date, end=end_date + timedelta(days=1))
                
                if df.empty:
                    log_message(f"No data received for {stock['yfin_symbol']} in date range", "WARNING")
                    continue
                
                successful_rows = 0
                failed_rows = 0
                
                for date, row in df.iterrows():
                    try:
                        if pd.isna(row['Close']) or row['Close'] <= 0:
                            continue
                        
                        price_data = {
                            "stock_id": stock['id'],
                            "date": date.date().isoformat(),
                            "open": float(row['Open']) if not pd.isna(row['Open']) else None,
                            "high": float(row['High']) if not pd.isna(row['High']) else None,
                            "low": float(row['Low']) if not pd.isna(row['Low']) else None,
                            "close": float(row['Close']) if not pd.isna(row['Close']) else None,
                            "volume": int(row['Volume']) if not pd.isna(row['Volume']) else 0,
                            "dividends": float(row['Dividends']) if not pd.isna(row['Dividends']) else 0.0,
                            "stock_splits": float(row['Stock Splits']) if not pd.isna(row['Stock Splits']) else 0.0,
                            "updated_at": datetime.now(UTC).isoformat()
                        }
                        
                        success = insert_price_data(price_data)
                        
                        if success:
                            successful_rows += 1
                        else:
                            failed_rows += 1
                            
                    except Exception as e:
                        failed_rows += 1
                        log_message(f"Error processing {stock['yfin_symbol']} on {date.date()}: {e}", "ERROR")
                
                log_message(f"Backfilled {stock['yfin_symbol']}: {successful_rows} successful, {failed_rows} failed")
                successful_stocks += 1
                
                # Small delay to avoid rate limiting
                time.sleep(0.5)
                
            except Exception as e:
                failed_stocks += 1
                log_message(f"Failed to backfill {stock['yfin_symbol']}: {e}", "ERROR")
        
        log_message(f"Backfill completed: {successful_stocks} stocks processed successfully, {failed_stocks} failed")
        
    except Exception as e:
        log_message(f"Error in backfill process: {e}", "ERROR")

def main():
    log_message("Starting price fetching process...")
    
    # Check if this is a backfill operation
    if len(sys.argv) == 3 and sys.argv[1] == '--backfill':
        # Usage: python fetch_prices.py --backfill 2025-10-18,2025-10-26
        date_range = sys.argv[2].split(',')
        if len(date_range) == 2:
            start_date, end_date = date_range
            backfill_missing_data(start_date.strip(), end_date.strip())
            return
        else:
            log_message("Invalid backfill format. Use: python fetch_prices.py --backfill YYYY-MM-DD,YYYY-MM-DD", "ERROR")
            return
    
    stocks = get_active_stocks_with_logging()
    if not stocks:
        log_message("No active stocks found", "WARNING")
        return
    
    start_time = datetime.now(UTC)
    successful_fetches = 0
    failed_fetches = 0
    skipped_stocks = 0
    
    for stock in stocks:
        # Validate stock data
        if not stock.get('yfin_symbol'):
            log_message(f"Skipping stock {stock.get('stock_name', 'unknown')} (ID: {stock.get('id', 'unknown')}) - no yfin_symbol found", "WARNING")
            skipped_stocks += 1
            continue
            
        log_message(f"\nProcessing {stock['stock_name']} ({stock['yfin_symbol']}) - ID: {stock['id']}")
        try:
            fetch_stock_prices(stock['id'], stock['yfin_symbol'])
            successful_fetches += 1
        except Exception as e:
            failed_fetches += 1
            log_message(f"Failed to process {stock['yfin_symbol']}: {e}", "ERROR")
        
        # Add a small delay between requests to avoid rate limiting
        time.sleep(1)
    
    end_time = datetime.now(UTC)
    duration = (end_time - start_time).total_seconds()
    log_message(f"Price fetching completed. Total time: {duration:.2f} seconds")
    log_message(f"Summary: {successful_fetches} successful, {failed_fetches} failed, {skipped_stocks} skipped out of {len(stocks)} total stocks")

if __name__ == "__main__":
    main()