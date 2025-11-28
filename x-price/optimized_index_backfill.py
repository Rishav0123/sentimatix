#!/usr/bin/env python3
"""
Optimized backfill script for comprehensive historical index data
Uses batch operations and intelligent date range detection
Similar to optimized_backfill.py but for indices
"""

import yfinance as yf
from datetime import datetime, UTC, timedelta, date
import pandas as pd
import time
import os
from pathlib import Path
import sys
from typing import List, Set, Tuple, Optional
from utilities.supabase_client import get_supabase_client
from utilities.index_operations import get_indices_with_symbols
from utilities.price_operations import insert_price_data
from utilities.logging_utils import log_message

# Initialize Supabase client
supabase = get_supabase_client()

def get_date_gaps_for_index(index_id: str, start_date: date, end_date: date) -> List[Tuple[date, date]]:
    """
    Find date gaps for a specific index by comparing with trading days
    Returns list of (start_gap, end_gap) tuples
    """
    try:
        # Get all existing dates for this index (stored as stock_id in stock_prices table)
        response = (supabase.table('stock_prices')
                   .select('date')
                   .eq('stock_id', index_id)  # index_id is stored as stock_id
                   .gte('date', start_date.isoformat())
                   .lte('date', end_date.isoformat())
                   .order('date')
                   .execute())
        
        existing_dates = {row['date'] for row in response.data}
        
        # Generate all dates in the range
        current_date = start_date
        all_dates = []
        while current_date <= end_date:
            all_dates.append(current_date)
            current_date += timedelta(days=1)
        
        # Find gaps (consecutive missing dates)
        gaps = []
        gap_start = None
        
        for check_date in all_dates:
            date_str = check_date.isoformat()
            
            if date_str not in existing_dates:
                if gap_start is None:
                    gap_start = check_date
            else:
                if gap_start is not None:
                    gaps.append((gap_start, check_date - timedelta(days=1)))
                    gap_start = None
        
        # Handle gap at the end
        if gap_start is not None:
            gaps.append((gap_start, end_date))
        
        return gaps
        
    except Exception as e:
        log_message(f"Error finding gaps for index {index_id}: {e}", "ERROR")
        # Return full range as gap if we can't determine existing data
        return [(start_date, end_date)]

def batch_insert_index_prices(price_records: List[dict]) -> bool:
    """Insert multiple index price records in batch"""
    try:
        if not price_records:
            return True
        
        # Split into chunks to avoid payload size limits
        chunk_size = 1000
        for i in range(0, len(price_records), chunk_size):
            chunk = price_records[i:i + chunk_size]
            
            result = (supabase.table('stock_prices')
                     .upsert(chunk, on_conflict='stock_id,date')
                     .execute())
            
            if not result.data:
                log_message(f"No data returned for batch insert (chunk {i//chunk_size + 1})", "WARNING")
                return False
        
        return True
        
    except Exception as e:
        log_message(f"Error in batch insert: {e}", "ERROR")
        return False

def fetch_and_fill_index_gaps(index_id: str, yfin_symbol: str, index_name: str, 
                             gaps: List[Tuple[date, date]]) -> Tuple[int, int]:
    """
    Fetch index data for specific date gaps and fill them
    Returns (successful_records, failed_records)
    """
    total_success = 0
    total_failed = 0
    
    try:
        index_ticker = yf.Ticker(yfin_symbol)
        
        for gap_start, gap_end in gaps:
            log_message(f"Filling gap: {gap_start} to {gap_end}")
            
            try:
                # Fetch data for this gap
                df = index_ticker.history(start=gap_start, end=gap_end + timedelta(days=1))
                
                if df.empty:
                    log_message(f"No data available for gap {gap_start} to {gap_end}")
                    continue
                
                # Prepare batch records
                batch_records = []
                
                for date_index, row in df.iterrows():
                    try:
                        # Validate data
                        if pd.isna(row['Close']) or row['Close'] <= 0:
                            total_failed += 1
                            continue
                        
                        # Store index_id as stock_id in stock_prices table
                        price_data = {
                            "stock_id": index_id,  # This is actually the index_id
                            "date": date_index.date().isoformat(),
                            "open": float(row['Open']) if not pd.isna(row['Open']) else None,
                            "high": float(row['High']) if not pd.isna(row['High']) else None,
                            "low": float(row['Low']) if not pd.isna(row['Low']) else None,
                            "close": float(row['Close']) if not pd.isna(row['Close']) else None,
                            "volume": int(row['Volume']) if not pd.isna(row['Volume']) else 0,
                            "dividends": float(row['Dividends']) if not pd.isna(row['Dividends']) else 0.0,
                            "stock_splits": float(row['Stock Splits']) if not pd.isna(row['Stock Splits']) else 0.0,
                            "updated_at": datetime.now(UTC).isoformat()
                        }
                        
                        batch_records.append(price_data)
                        
                    except Exception as e:
                        log_message(f"Error preparing record for {date_index.date()}: {e}", "ERROR")
                        total_failed += 1
                
                # Insert batch
                if batch_records:
                    if batch_insert_index_prices(batch_records):
                        total_success += len(batch_records)
                        log_message(f"Successfully inserted {len(batch_records)} records for gap")
                    else:
                        total_failed += len(batch_records)
                        log_message(f"Failed to insert {len(batch_records)} records for gap", "ERROR")
                
                # Rate limiting between gaps
                time.sleep(0.5)
                
            except Exception as e:
                log_message(f"Error processing gap {gap_start} to {gap_end}: {e}", "ERROR")
                total_failed += 1
        
        return total_success, total_failed
        
    except Exception as e:
        log_message(f"Error in fetch_and_fill_index_gaps for {yfin_symbol}: {e}", "ERROR")
        return 0, 1

def process_index_optimized(index_id: str, yfin_symbol: str, index_name: str) -> bool:
    """Process a single index with optimized gap detection and filling"""
    try:
        log_message(f"\n{'='*60}")
        log_message(f"Processing: {index_name} ({yfin_symbol})")
        
        # Determine date range
        # Get index's first available date
        index_ticker = yf.Ticker(yfin_symbol)
        
        # Try to get the earliest possible data
        early_test = index_ticker.history(start=date(2000, 1, 1), end=date(2000, 12, 31))
        if not early_test.empty:
            # Index has very early data, get full history
            full_history = index_ticker.history(period="max")
            if not full_history.empty:
                actual_start = full_history.index[0].date()
                actual_end = full_history.index[-1].date()
            else:
                log_message(f"Could not determine date range for {yfin_symbol}", "ERROR")
                return False
        else:
            # Index might be newer, try from 2020
            recent_history = index_ticker.history(start=date(2020, 1, 1))
            if not recent_history.empty:
                actual_start = recent_history.index[0].date()
                actual_end = recent_history.index[-1].date()
            else:
                log_message(f"No data available for {yfin_symbol}", "WARNING")
                return False
        
        # Use the later of 2020-01-01 or actual start date
        start_date = max(date(2020, 1, 1), actual_start)
        end_date = min(datetime.now(UTC).date(), actual_end)
        
        log_message(f"Date range: {start_date} to {end_date}")
        
        if start_date > end_date:
            log_message(f"Invalid date range for {yfin_symbol}")
            return False
        
        # Find gaps in existing data
        gaps = get_date_gaps_for_index(index_id, start_date, end_date)
        
        if not gaps:
            log_message(f"No gaps found for {yfin_symbol} - data is complete")
            return True
        
        log_message(f"Found {len(gaps)} gaps to fill")
        for i, (gap_start, gap_end) in enumerate(gaps[:5], 1):  # Show first 5 gaps
            gap_days = (gap_end - gap_start).days + 1
            log_message(f"  Gap {i}: {gap_start} to {gap_end} ({gap_days} days)")
        
        if len(gaps) > 5:
            total_gap_days = sum((gap_end - gap_start).days + 1 for gap_start, gap_end in gaps)
            log_message(f"  ... and {len(gaps) - 5} more gaps (total: {total_gap_days} days)")
        
        # Fill gaps
        success_count, fail_count = fetch_and_fill_index_gaps(index_id, yfin_symbol, index_name, gaps)
        
        log_message(f"Completed {yfin_symbol}: {success_count} records added, {fail_count} failed")
        
        return success_count > 0 or fail_count == 0
        
    except Exception as e:
        log_message(f"Error processing {yfin_symbol}: {e}", "ERROR")
        return False

def main():
    """Main function for optimized index backfill"""
    log_message("Starting OPTIMIZED index backfill")
    log_message("Features: gap detection, batch inserts, intelligent date ranges")
    
    # Parse command line arguments
    dry_run = '--dry-run' in sys.argv
    index_limit = None
    
    if '--help' in sys.argv or '-h' in sys.argv:
        print("Usage: python optimized_index_backfill.py [options]")
        print("Options:")
        print("  --dry-run         Show gaps without filling them")
        print("  --index-limit N   Process only first N indices")
        print("  --help, -h        Show this help")
        return
    
    if '--index-limit' in sys.argv:
        try:
            limit_index = sys.argv.index('--index-limit')
            index_limit = int(sys.argv[limit_index + 1])
            log_message(f"Limited to {index_limit} indices")
        except (IndexError, ValueError):
            log_message("Invalid --index-limit value", "ERROR")
            return
    
    if dry_run:
        log_message("DRY RUN MODE - Will show gaps but not fill them")
    
    # Get indices
    indices = get_indices_with_symbols()
    if not indices:
        log_message("No indices with symbols found", "ERROR")
        return
    
    log_message(f"Found {len(indices)} indices with yfinance symbols")
    
    if index_limit:
        indices = indices[:index_limit]
    
    # Process indices
    start_time = datetime.now(UTC)
    successful = 0
    failed = 0
    
    for i, index in enumerate(indices, 1):
        if not index.get('yfin_symbol'):
            log_message(f"Skipping {index.get('index_name', 'unknown')} - no symbol", "WARNING")
            failed += 1
            continue
        
        log_message(f"\n[{i}/{len(indices)}] Starting {index['index_name']}")
        
        if dry_run:
            # For dry run, just detect gaps
            try:
                index_ticker = yf.Ticker(index['yfin_symbol'])
                history = index_ticker.history(period="max")
                if not history.empty:
                    actual_start = history.index[0].date()
                    start_date = max(date(2020, 1, 1), actual_start)
                    end_date = datetime.now(UTC).date()
                    
                    gaps = get_date_gaps_for_index(index['id'], start_date, end_date)
                    total_gap_days = sum((ge - gs).days + 1 for gs, ge in gaps)
                    log_message(f"Would fill {len(gaps)} gaps ({total_gap_days} days)")
                    successful += 1
                else:
                    log_message(f"No data available for {index['yfin_symbol']}")
                    failed += 1
            except Exception as e:
                log_message(f"Error in dry run for {index['yfin_symbol']}: {e}", "ERROR")
                failed += 1
        else:
            # Actually process
            if process_index_optimized(index['id'], index['yfin_symbol'], index['index_name']):
                successful += 1
            else:
                failed += 1
        
        # Progress updates
        if i % 5 == 0:
            elapsed = (datetime.now(UTC) - start_time).total_seconds()
            rate = i / elapsed * 60 if elapsed > 0 else 0
            log_message(f"Progress: {i}/{len(indices)} indices ({rate:.1f} indices/min)")
    
    # Final summary
    end_time = datetime.now(UTC)
    duration = (end_time - start_time).total_seconds()
    
    log_message(f"\n{'='*60}")
    log_message("OPTIMIZED INDEX BACKFILL COMPLETE")
    log_message(f"Duration: {duration:.1f}s ({duration/60:.1f} min)")
    log_message(f"Results: {successful} successful, {failed} failed")
    log_message(f"Rate: {len(indices)/duration*60:.1f} indices/minute")
    
    if dry_run:
        log_message("This was a DRY RUN - run without --dry-run to fill gaps")

if __name__ == "__main__":
    main()