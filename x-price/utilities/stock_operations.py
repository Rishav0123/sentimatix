"""
Stock operations for Supabase database
"""
from typing import List, Dict, Optional
from utilities.supabase_client import supabase

def get_active_stocks() -> List[Dict]:
    """
    Fetch all active stocks from the database
    
    Returns:
        List[Dict]: List of active stock records with id, yfin_symbol, and stock_name
    """
    try:
        response = supabase.table('stocks').select('id, yfin_symbol, stock_name').eq('is_active', True).execute()
        return response.data
    except Exception as e:
        raise Exception(f"Error fetching active stocks: {e}")

def get_stock_by_id(stock_id: str) -> Optional[Dict]:
    """
    Get stock information by ID
    
    Args:
        stock_id (str): Stock ID to fetch
        
    Returns:
        Optional[Dict]: Stock record or None if not found
    """
    try:
        response = supabase.table('stocks').select('*').eq('id', stock_id).single().execute()
        return response.data
    except Exception as e:
        raise Exception(f"Error fetching stock {stock_id}: {e}")

def get_stock_by_symbol(yfin_symbol: str) -> Optional[Dict]:
    """
    Get stock information by yfinance symbol
    
    Args:
        yfin_symbol (str): yfinance symbol (e.g., 'BAJFINANCE.NS')
        
    Returns:
        Optional[Dict]: Stock record or None if not found
    """
    try:
        response = supabase.table('stocks').select('*').eq('yfin_symbol', yfin_symbol).single().execute()
        return response.data
    except Exception as e:
        raise Exception(f"Error fetching stock {yfin_symbol}: {e}")

def update_stock_status(stock_id: str, is_active: bool) -> bool:
    """
    Update the active status of a stock
    
    Args:
        stock_id (str): Stock ID to update
        is_active (bool): New active status
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        response = supabase.table('stocks').update({'is_active': is_active}).eq('id', stock_id).execute()
        return len(response.data) > 0
    except Exception as e:
        raise Exception(f"Error updating stock {stock_id} status: {e}")