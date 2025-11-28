"""
Stock price operations for Supabase database
"""
from typing import List, Dict, Optional
from datetime import datetime, date
from utilities.supabase_client import supabase

def get_last_price_date(stock_id: str) -> Optional[date]:
    """
    Get the last date we have price data for a specific stock
    
    Args:
        stock_id (str): Stock ID to check
        
    Returns:
        Optional[date]: Last date with price data, or None if no data exists
    """
    try:
        response = (supabase.table('stock_prices')
                   .select('date')
                   .eq('stock_id', stock_id)
                   .order('date', desc=True)
                   .limit(1)
                   .execute())
        
        if response.data:
            return datetime.fromisoformat(response.data[0]['date']).date()
        return None
    except Exception as e:
        raise Exception(f"Error fetching last price date for stock {stock_id}: {e}")

def insert_price_data(price_data: Dict) -> bool:
    """
    Insert or update price data for a stock
    
    Args:
        price_data (Dict): Price data dictionary
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        result = (supabase.table('stock_prices')
                 .upsert(price_data, on_conflict='stock_id,date')
                 .execute())
        return len(result.data) > 0
    except Exception as e:
        raise Exception(f"Error inserting price data: {e}")

def get_price_data_range(stock_id: str, start_date: date, end_date: date) -> List[Dict]:
    """
    Get price data for a stock within a date range
    
    Args:
        stock_id (str): Stock ID
        start_date (date): Start date
        end_date (date): End date
        
    Returns:
        List[Dict]: List of price records
    """
    try:
        response = (supabase.table('stock_prices')
                   .select('*')
                   .eq('stock_id', stock_id)
                   .gte('date', start_date.isoformat())
                   .lte('date', end_date.isoformat())
                   .order('date')
                   .execute())
        return response.data
    except Exception as e:
        raise Exception(f"Error fetching price data for stock {stock_id}: {e}")

def get_price_data_dates(stock_id: str, start_date: date, end_date: date) -> List[str]:
    """
    Get only the dates we have price data for within a range
    
    Args:
        stock_id (str): Stock ID
        start_date (date): Start date
        end_date (date): End date
        
    Returns:
        List[str]: List of dates in ISO format
    """
    try:
        response = (supabase.table('stock_prices')
                   .select('date')
                   .eq('stock_id', stock_id)
                   .gte('date', start_date.isoformat())
                   .lte('date', end_date.isoformat())
                   .order('date')
                   .execute())
        return [row['date'] for row in response.data]
    except Exception as e:
        raise Exception(f"Error fetching price dates for stock {stock_id}: {e}")

def delete_price_data(stock_id: str, date_to_delete: date) -> bool:
    """
    Delete price data for a specific stock and date
    
    Args:
        stock_id (str): Stock ID
        date_to_delete (date): Date to delete
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        response = (supabase.table('stock_prices')
                   .delete()
                   .eq('stock_id', stock_id)
                   .eq('date', date_to_delete.isoformat())
                   .execute())
        return len(response.data) > 0
    except Exception as e:
        raise Exception(f"Error deleting price data for stock {stock_id} on {date_to_delete}: {e}")

def get_stocks_with_missing_dates(start_date: date, end_date: date) -> Dict[str, List[str]]:
    """
    Find stocks that are missing price data for specific dates
    
    Args:
        start_date (date): Start date to check
        end_date (date): End date to check
        
    Returns:
        Dict[str, List[str]]: Dictionary mapping stock_id to list of missing dates
    """
    from utilities.stock_operations import get_active_stocks
    import yfinance as yf
    
    try:
        # Get all active stocks
        stocks = get_active_stocks()
        missing_data = {}
        
        for stock in stocks:
            stock_id = stock['id']
            symbol = stock['yfin_symbol']
            
            # Get trading days from yfinance for comparison
            ticker = yf.Ticker(symbol)
            df = ticker.history(start=start_date, end=end_date)
            trading_days = [date.date().isoformat() for date in df.index]
            
            # Get dates we have in database
            db_dates = get_price_data_dates(stock_id, start_date, end_date)
            
            # Find missing dates
            missing_dates = set(trading_days) - set(db_dates)
            if missing_dates:
                missing_data[stock_id] = sorted(missing_dates)
        
        return missing_data
    except Exception as e:
        raise Exception(f"Error checking for missing dates: {e}")