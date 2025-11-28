"""
Yahoo Finance data fetching utilities
"""
import yfinance as yf
import pandas as pd
from datetime import datetime, UTC, date, timedelta
from typing import Dict, Optional, Tuple

def fetch_stock_data(symbol: str, start_date: date, end_date: date) -> Optional[pd.DataFrame]:
    """
    Fetch stock data from Yahoo Finance
    
    Args:
        symbol (str): yfinance symbol (e.g., 'BAJFINANCE.NS')
        start_date (date): Start date for data fetch
        end_date (date): End date for data fetch
        
    Returns:
        Optional[pd.DataFrame]: Stock data DataFrame or None if fetch failed
    """
    try:
        stock = yf.Ticker(symbol)
        df = stock.history(start=start_date, end=end_date + timedelta(days=1))
        
        if df.empty:
            return None
            
        return df
    except Exception as e:
        raise Exception(f"Error fetching data for {symbol}: {e}")

def validate_price_data(row: pd.Series) -> bool:
    """
    Validate if a price data row is valid
    
    Args:
        row (pd.Series): Price data row from DataFrame
        
    Returns:
        bool: True if valid, False otherwise
    """
    return not (pd.isna(row['Close']) or row['Close'] <= 0)

def format_price_data(stock_id: str, date: datetime, row: pd.Series) -> Dict:
    """
    Format price data for database insertion
    
    Args:
        stock_id (str): Stock ID
        date (datetime): Date of the price data
        row (pd.Series): Price data row from DataFrame
        
    Returns:
        Dict: Formatted price data dictionary
    """
    return {
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

def get_trading_days(symbol: str, start_date: date, end_date: date) -> list:
    """
    Get trading days for a symbol within a date range
    
    Args:
        symbol (str): yfinance symbol
        start_date (date): Start date
        end_date (date): End date
        
    Returns:
        list: List of trading days in ISO format
    """
    try:
        df = fetch_stock_data(symbol, start_date, end_date)
        if df is None or df.empty:
            return []
        return [date.date().isoformat() for date in df.index]
    except Exception as e:
        raise Exception(f"Error getting trading days for {symbol}: {e}")

def check_symbol_validity(symbol: str) -> Tuple[bool, str]:
    """
    Check if a yfinance symbol is valid by attempting to fetch recent data
    
    Args:
        symbol (str): yfinance symbol to check
        
    Returns:
        Tuple[bool, str]: (is_valid, message)
    """
    try:
        stock = yf.Ticker(symbol)
        # Try to get just 1 day of recent data
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=7)  # Look back 7 days to find a trading day
        
        df = stock.history(start=start_date, end=end_date)
        
        if df.empty:
            return False, f"No data available for {symbol}"
        
        # Check if we have valid price data
        latest_row = df.iloc[-1]
        if pd.isna(latest_row['Close']) or latest_row['Close'] <= 0:
            return False, f"Invalid price data for {symbol}"
        
        return True, f"Valid symbol {symbol}"
        
    except Exception as e:
        return False, f"Error checking {symbol}: {e}"