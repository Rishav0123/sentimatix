"""
Supabase client configuration and initialization
"""
import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def get_supabase_client() -> Client:
    """
    Initialize and return Supabase client using environment variables
    
    Returns:
        Client: Configured Supabase client
        
    Raises:
        ValueError: If required environment variables are missing
    """
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')
    
    if not supabase_url or not supabase_key:
        raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables")
    
    return create_client(supabase_url, supabase_key)

# Global client instance for easy access
supabase = get_supabase_client()