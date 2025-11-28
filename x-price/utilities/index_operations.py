"""
Index operations utility module for handling database operations related to indices
Similar to stock_operations.py but for the index table
"""

from typing import List, Dict, Optional
from .supabase_client import get_supabase_client

# Get Supabase client
supabase = get_supabase_client()

def get_active_indices() -> List[Dict]:
    """
    Fetch all indices from the database
    Note: Unlike stocks, indices don't have an is_active field based on the provided schema
    
    Returns:
        List[Dict]: List of index records with id, index_name, yfin_symbol, etc.
    """
    try:
        response = supabase.table('index').select('*').execute()
        return response.data if response.data else []
    except Exception as e:
        print(f"Error fetching indices: {e}")
        return []

def get_indices_with_symbols() -> List[Dict]:
    """
    Fetch indices that have yfin_symbol (can be fetched from yfinance)
    
    Returns:
        List[Dict]: List of index records that have yfin_symbol
    """
    try:
        response = (supabase.table('index')
                   .select('*')
                   .not_.is_('yfin_symbol', 'null')
                   .neq('yfin_symbol', '')
                   .execute())
        return response.data if response.data else []
    except Exception as e:
        print(f"Error fetching indices with symbols: {e}")
        return []

def get_index_by_id(index_id: str) -> Optional[Dict]:
    """
    Get a specific index by its ID
    
    Args:
        index_id (str): The UUID of the index
        
    Returns:
        Optional[Dict]: Index record or None if not found
    """
    try:
        response = supabase.table('index').select('*').eq('id', index_id).single().execute()
        return response.data
    except Exception as e:
        print(f"Error fetching index by ID {index_id}: {e}")
        return None

def get_index_by_symbol(yfin_symbol: str) -> Optional[Dict]:
    """
    Get a specific index by its yfinance symbol
    
    Args:
        yfin_symbol (str): The yfinance symbol (e.g., '^NSEI', '^BSESN')
        
    Returns:
        Optional[Dict]: Index record or None if not found
    """
    try:
        response = supabase.table('index').select('*').eq('yfin_symbol', yfin_symbol).single().execute()
        return response.data
    except Exception as e:
        print(f"Error fetching index by symbol {yfin_symbol}: {e}")
        return None

def add_index(index_data: Dict) -> bool:
    """
    Add a new index to the database
    
    Args:
        index_data (Dict): Index data containing index_name, country, yfin_symbol, etc.
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        response = supabase.table('index').insert(index_data).execute()
        return bool(response.data)
    except Exception as e:
        print(f"Error adding index: {e}")
        return False

def update_index(index_id: str, updates: Dict) -> bool:
    """
    Update an existing index
    
    Args:
        index_id (str): The UUID of the index to update
        updates (Dict): Dictionary containing fields to update
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        response = supabase.table('index').update(updates).eq('id', index_id).execute()
        return bool(response.data)
    except Exception as e:
        print(f"Error updating index {index_id}: {e}")
        return False

def get_indices_by_country(country: str) -> List[Dict]:
    """
    Get indices for a specific country
    
    Args:
        country (str): Country name to filter by
        
    Returns:
        List[Dict]: List of index records for the specified country
    """
    try:
        response = (supabase.table('index')
                   .select('*')
                   .eq('country', country)
                   .execute())
        return response.data if response.data else []
    except Exception as e:
        print(f"Error fetching indices for country {country}: {e}")
        return []

def get_indices_by_exchange(exchange: str) -> List[Dict]:
    """
    Get indices for a specific exchange
    
    Args:
        exchange (str): Exchange name to filter by
        
    Returns:
        List[Dict]: List of index records for the specified exchange
    """
    try:
        response = (supabase.table('index')
                   .select('*')
                   .eq('exchange', exchange)
                   .execute())
        return response.data if response.data else []
    except Exception as e:
        print(f"Error fetching indices for exchange {exchange}: {e}")
        return []

def search_indices_by_keywords(keywords: List[str]) -> List[Dict]:
    """
    Search indices that contain any of the specified keywords
    
    Args:
        keywords (List[str]): List of keywords to search for
        
    Returns:
        List[Dict]: List of index records that match the keywords
    """
    try:
        # Note: This uses PostgreSQL array overlap operator
        response = (supabase.table('index')
                   .select('*')
                   .overlaps('keywords', keywords)
                   .execute())
        return response.data if response.data else []
    except Exception as e:
        print(f"Error searching indices by keywords {keywords}: {e}")
        return []