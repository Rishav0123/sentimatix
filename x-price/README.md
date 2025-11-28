# Stock Price Fetcher System

A modular system for fetching and managing stock price data from Yahoo Finance and storing it in Supabase.

## 🏗️ Project Structure

```
├── .env                          # Environment variables (Supabase credentials)
├── requirements.txt              # Python dependencies
├── fetch_prices.py              # Original script (legacy)
├── fetch_prices_new.py          # New main entry point (backward compatible)
├── price_fetcher.py             # Incremental price fetching
├── backfill_prices.py           # Historical data backfilling
├── data_continuity_check.py     # Data validation and gap detection
├── validate_symbols.py          # Symbol validity checker
├── check_data_continuity.py     # Old continuity checker (legacy)
├── logs/                        # Log files
└── utilities/                   # Modular utilities
    ├── __init__.py
    ├── supabase_client.py       # Supabase connection management
    ├── stock_operations.py      # Stock CRUD operations
    ├── price_operations.py      # Price data operations
    ├── yfinance_utils.py        # Yahoo Finance utilities
    └── logging_utils.py         # Logging functions
```

## 🚀 Quick Start

### 1. Setup Environment

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment variables
# Edit .env file with your Supabase credentials
```

### 2. Environment Variables

Create a `.env` file in the root directory:

```env
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
```

### 3. Basic Usage

```bash
# Fetch latest prices (incremental)
python price_fetcher.py

# Backfill historical data
python backfill_prices.py 2025-10-14 2025-10-17

# Check data continuity
python data_continuity_check.py 2025-10-14 2025-11-01

# Validate stock symbols
python validate_symbols.py

# Backward compatibility (old interface)
python fetch_prices_new.py
python fetch_prices_new.py --backfill 2025-10-14,2025-10-17
```

## 📚 Scripts Documentation

### price_fetcher.py
**Purpose**: Incremental price data fetching
- Checks last date in database for each stock
- Fetches only new data to avoid duplicates
- Smart error handling and logging
- Rate limiting to respect API limits

```bash
python price_fetcher.py
```

### backfill_prices.py
**Purpose**: Fill historical data gaps
- Fetches data for specific date ranges
- Useful for filling gaps in historical data
- Supports any date range

```bash
python backfill_prices.py 2025-10-14 2025-10-17
```

### data_continuity_check.py
**Purpose**: Validate data completeness
- Compares database dates with trading days
- Identifies missing data gaps
- Supports checking specific stock counts

```bash
# Check all stocks
python data_continuity_check.py 2025-10-14 2025-11-01

# Check first 10 stocks only
python data_continuity_check.py 2025-10-14 2025-11-01 10
```

### validate_symbols.py
**Purpose**: Check symbol validity
- Validates yfinance symbols
- Can deactivate invalid stocks
- Prevents API errors

```bash
# Validate all symbols
python validate_symbols.py

# Validate specific symbol
python validate_symbols.py BAJFINANCE.NS
```

## 🔧 Utilities Documentation

### utilities/supabase_client.py
- Manages Supabase connection
- Loads credentials from environment
- Provides global client instance

### utilities/stock_operations.py
- `get_active_stocks()`: Fetch all active stocks
- `get_stock_by_id()`: Get stock by ID
- `get_stock_by_symbol()`: Get stock by symbol
- `update_stock_status()`: Activate/deactivate stocks

### utilities/price_operations.py
- `get_last_price_date()`: Get last date with price data
- `insert_price_data()`: Insert/update price data
- `get_price_data_range()`: Get prices for date range
- `get_stocks_with_missing_dates()`: Find data gaps

### utilities/yfinance_utils.py
- `fetch_stock_data()`: Fetch data from Yahoo Finance
- `validate_price_data()`: Validate price data
- `format_price_data()`: Format for database
- `check_symbol_validity()`: Check if symbol is valid

### utilities/logging_utils.py
- `log_message()`: General logging
- `log_error()`: Error logging
- `log_warning()`: Warning logging
- `log_info()`: Info logging

## 📊 Database Schema

### stocks table
```sql
- id (UUID, PK)
- yfin_symbol (TEXT) - Yahoo Finance symbol
- stock_name (TEXT)
- is_active (BOOLEAN)
```

### stock_prices table
```sql
- stock_id (UUID, FK)
- date (DATE)
- open, high, low, close (NUMERIC)
- volume (BIGINT)
- dividends, stock_splits (NUMERIC)
- updated_at (TIMESTAMP)
- PRIMARY KEY (stock_id, date)
```

## 🔄 Migration from Old System

The new system maintains backward compatibility:

1. **Old script still works**: `python fetch_prices.py`
2. **Old backfill format**: `python fetch_prices.py --backfill 2025-10-14,2025-10-17`
3. **Gradual migration**: Use new scripts for better functionality

## 🛠️ Features

✅ **Modular Design**: Separated concerns into utilities
✅ **Environment Variables**: Secure credential management
✅ **Error Handling**: Comprehensive error handling and logging
✅ **Rate Limiting**: Respects API limits
✅ **Data Validation**: Ensures data quality
✅ **Backward Compatibility**: Supports old interfaces
✅ **Incremental Fetching**: Avoids duplicate data
✅ **Gap Detection**: Identifies missing data
✅ **Symbol Validation**: Prevents invalid API calls

## 🚨 Error Handling

- **API Failures**: Graceful handling of yfinance errors
- **Database Errors**: Retry logic and detailed logging
- **Invalid Data**: Validation and filtering
- **Missing Dependencies**: Clear error messages

## 📝 Logging

- **Daily Log Files**: `logs/price_fetcher_log_YYYYMMDD.txt`
- **Console Output**: Real-time progress
- **Log Levels**: INFO, WARNING, ERROR, SUCCESS
- **Detailed Timestamps**: UTC timestamps for all events

## 🔮 Future Enhancements

- [ ] Web interface for monitoring
- [ ] Email notifications for failures
- [ ] Data quality metrics
- [ ] Performance monitoring
- [ ] Multiple data sources
- [ ] Real-time data streaming