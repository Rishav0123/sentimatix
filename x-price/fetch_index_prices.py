#!/usr/bin/env python3
"""
Index price fetcher script
Fetches index prices from yfinance and stores them in the stock_prices table
Similar to fetch_prices.py but for indices
"""

import yfinance as yf
from datetime import datetime, UTC, timedelta
import pandas as pd
import time
import sys
from pathlib import Path
from utilities.index_operations import get_indices_with_symbols
from utilities.price_operations import get_last_price_date, insert_price_data
from utilities.logging_utils import log_message

def get_active_indices_with_logging():
    """Fetch indices with symbols with logging"""
    try:
        indices = get_indices_with_symbols()
        log_message(f"Found {len(indices)} indices with yfinance symbols")
        
        # Log first few indices for debugging
        if indices:
            sample_indices = [{k: v for k, v in idx.items() if k in ['index_name', 'yfin_symbol', 'country']} 
                             for idx in indices[:3]]
            log_message(f"Sample indices: {sample_indices}")
        
        return indices
    except Exception as e:
        error_msg = f"Error fetching indices: {e}"
        log_message(error_msg, "ERROR")
        return []

def fetch_index_prices(index_id: str, yfin_symbol: str):
    """Fetch index prices from yfinance and store in stock_prices table
    
    Args:
        index_id (str): ID of the index in the database (will be stored as stock_id)
        yfin_symbol (str): yfinance symbol (e.g., '^NSEI', '^BSESN')
    """
    try:
        log_message(f"Fetching data for {yfin_symbol}...")
        
        # Get the last date we have data for this index
        # Note: We use index_id as stock_id in the stock_prices table
        try:
            last_date = get_last_price_date(index_id)
            
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
        index_ticker = yf.Ticker(yfin_symbol)
        
        # Get today's date
        end_date = datetime.now(UTC).date()
        
        # Check if we need to fetch any data
        if start_date > end_date:
            log_message(f"No new data to fetch for {yfin_symbol} (start_date: {start_date} > end_date: {end_date})")
            return
        
        # Fetch history
        log_message(f"Fetching history from {start_date} to {end_date}")
        
        try:
            df = index_ticker.history(start=start_date, end=end_date + timedelta(days=1))  # Add 1 day to include end_date
        except Exception as fetch_error:
            log_message(f"yfinance error for {yfin_symbol}: {fetch_error}", "ERROR")
            return
        
        if df.empty:
            log_message(f"No data received for {yfin_symbol} - symbol may be invalid or no trading data available", "WARNING")
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
                # Note: We store index_id as stock_id in the stock_prices table
                price_data = {
                    "stock_id": index_id,  # This is actually the index_id
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
                    # Use upsert to handle duplicates based on primary key (stock_id, date)
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

def backfill_missing_index_data(start_date_str: str, end_date_str: str):
    """Backfill missing index data for a specific date range
    
    Args:
        start_date_str (str): Start date in YYYY-MM-DD format
        end_date_str (str): End date in YYYY-MM-DD format
    """
    try:
        start_date = datetime.fromisoformat(start_date_str).date()
        end_date = datetime.fromisoformat(end_date_str).date()
        
        log_message(f"Starting index backfill from {start_date} to {end_date}")
        
        indices = get_active_indices_with_logging()
        if not indices:
            log_message("No indices with symbols found", "WARNING")
            return
        
        successful_indices = 0
        failed_indices = 0
        
        for index in indices:
            if not index.get('yfin_symbol'):
                continue
                
            try:
                log_message(f"\nBackfilling {index['index_name']} ({index['yfin_symbol']})")
                
                # Create a Ticker object
                index_ticker = yf.Ticker(index['yfin_symbol'])
                
                # Fetch history for the specified range
                df = index_ticker.history(start=start_date, end=end_date + timedelta(days=1))
                
                if df.empty:
                    log_message(f"No data received for {index['yfin_symbol']} in date range", "WARNING")
                    continue
                
                successful_rows = 0
                failed_rows = 0
                
                for date, row in df.iterrows():
                    try:
                        if pd.isna(row['Close']) or row['Close'] <= 0:
                            continue
                        
                        # Store index_id as stock_id in stock_prices table
                        price_data = {
                            "stock_id": index['id'],  # This is actually the index_id
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
                        log_message(f"Error processing {index['yfin_symbol']} on {date.date()}: {e}", "ERROR")
                
                log_message(f"Backfilled {index['yfin_symbol']}: {successful_rows} successful, {failed_rows} failed")
                successful_indices += 1
                
                # Small delay to avoid rate limiting
                time.sleep(0.5)
                
            except Exception as e:
                failed_indices += 1
                log_message(f"Failed to backfill {index['yfin_symbol']}: {e}", "ERROR")
        
        log_message(f"Index backfill completed: {successful_indices} indices processed successfully, {failed_indices} failed")
        
    except Exception as e:
        log_message(f"Error in index backfill process: {e}", "ERROR")

def main():
    log_message("Starting index price fetching process...")
    
    # Check if this is a backfill operation
    if len(sys.argv) == 3 and sys.argv[1] == '--backfill':
        # Usage: python fetch_index_prices.py --backfill 2025-10-18,2025-10-26
        date_range = sys.argv[2].split(',')
        if len(date_range) == 2:
            start_date, end_date = date_range
            backfill_missing_index_data(start_date.strip(), end_date.strip())
            return
        else:
            log_message("Invalid backfill format. Use: python fetch_index_prices.py --backfill YYYY-MM-DD,YYYY-MM-DD", "ERROR")
            return
    
    indices = get_active_indices_with_logging()
    if not indices:
        log_message("No indices with symbols found", "WARNING")
        return
    
    start_time = datetime.now(UTC)
    successful_fetches = 0
    failed_fetches = 0
    skipped_indices = 0
    
    for index in indices:
        # Validate index data
        if not index.get('yfin_symbol'):
            log_message(f"Skipping index {index.get('index_name', 'unknown')} (ID: {index.get('id', 'unknown')}) - no yfin_symbol found", "WARNING")
            skipped_indices += 1
            continue
            
        log_message(f"\nProcessing {index['index_name']} ({index['yfin_symbol']}) - ID: {index['id']}")
        try:
            fetch_index_prices(index['id'], index['yfin_symbol'])
            successful_fetches += 1
        except Exception as e:
            failed_fetches += 1
            log_message(f"Failed to process {index['yfin_symbol']}: {e}", "ERROR")
        
        # Add a small delay between requests to avoid rate limiting
        time.sleep(1)
    
    end_time = datetime.now(UTC)
    duration = (end_time - start_time).total_seconds()
    log_message(f"Index price fetching completed. Total time: {duration:.2f} seconds")
    log_message(f"Summary: {successful_fetches} successful, {failed_fetches} failed, {skipped_indices} skipped out of {len(indices)} total indices")

if __name__ == "__main__":
    main()