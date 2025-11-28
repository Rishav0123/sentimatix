# Index Price Fetching System

This system provides similar functionality to the stock price fetching but for indices. Index data is stored in the same `stock_prices` table using the index ID as the `stock_id`.

## Files Created

### 1. `utilities/index_operations.py`
Utility functions for index database operations:
- `get_active_indices()` - Get all indices from database
- `get_indices_with_symbols()` - Get indices that have yfinance symbols  
- `get_index_by_id(index_id)` - Get specific index by ID
- `get_index_by_symbol(symbol)` - Get index by yfinance symbol
- `add_index(data)`, `update_index(id, data)` - CRUD operations
- `get_indices_by_country(country)` - Filter by country
- `get_indices_by_exchange(exchange)` - Filter by exchange
- `search_indices_by_keywords(keywords)` - Search by keywords

### 2. `fetch_index_prices.py`
Main daily index price fetcher:
- Fetches prices for all indices with yfinance symbols
- Uses incremental fetching (starts from last stored date)
- Stores data in `stock_prices` table with `index_id` as `stock_id`
- Supports backfill mode: `python fetch_index_prices.py --backfill 2025-10-01,2025-10-31`
- Uses utilities for database operations and logging

### 3. `check_index_data_continuity.py`
Data validation tool:
- Checks data completeness for all indices
- Compares database dates with yfinance trading days
- Reports missing dates for each index
- Similar to `check_data_continuity.py` but for indices

### 4. `optimized_index_backfill.py`
Advanced backfill tool:
- Gap detection and intelligent date range handling
- Batch operations for efficient data insertion
- Support for dry-run mode: `--dry-run`
- Index limit option: `--index-limit N`
- Comprehensive historical data backfilling

## Usage Examples

### Daily Index Price Fetching
```bash
python fetch_index_prices.py
```

### Backfill Specific Date Range
```bash
python fetch_index_prices.py --backfill 2025-10-01,2025-10-31
```

### Check Data Continuity
```bash
python check_index_data_continuity.py
```

### Comprehensive Backfill
```bash
# Dry run to see what would be filled
python optimized_index_backfill.py --dry-run

# Actually fill gaps for first 5 indices
python optimized_index_backfill.py --index-limit 5

# Full backfill
python optimized_index_backfill.py
```

## Database Schema

Index data is stored in the existing `stock_prices` table:
- `stock_id` contains the `index.id` (UUID)
- `date`, `open`, `high`, `low`, `close`, `volume` contain price data
- `dividends` and `stock_splits` are typically 0 for indices

## Index Table Structure

Based on your schema:
```sql
create table public.index (
  index_name varchar(100) not null,
  country varchar(50) not null,
  exchange varchar(50) null,
  currency varchar(10) null,
  sector_coverage varchar(100) null,
  keywords text[] null,
  created_at timestamp null default CURRENT_TIMESTAMP,
  id uuid not null default gen_random_uuid(),
  yfin_symbol varchar null,
  constraint index_pkey primary key (id)
);
```

## Integration with Existing System

- Reuses `utilities/price_operations.py` for price storage
- Reuses `utilities/logging_utils.py` for logging  
- Reuses `utilities/supabase_client.py` for database connections
- Uses same `.env` configuration for credentials
- Compatible with existing `stock_prices` table structure

## Current Index Coverage

Your database contains 12 indices with yfinance symbols:
- NIFTY IT (^CNXIT)
- SENSEX (^BSESN) 
- NIFTY Midcap 100 (NIFTY_MIDCAP_100.NS)
- NIFTY FMCG (^CNXFMCG)
- NIFTY 50 (^NSEI)
- NIFTY Auto (AUTOBEES.NS)
- NIFTY Bank (^NSEBANK)
- NIFTY Metal (^CNXMETAL)
- NIFTY Pharma (PHARMABEES.NS)
- Motilal Oswal Nifty Next 50 Index Reg Gr (0P0001IUFY.BO)
- NIFTY Energy (^CNXENERGY)
- Zerodha Nifty Smallcap 100 ETF (SML100CASE.NS)

All tested and working successfully! ✅