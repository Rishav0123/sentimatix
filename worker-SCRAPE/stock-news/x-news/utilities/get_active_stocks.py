from supabase import create_client, Client
from dotenv import load_dotenv
import os

load_dotenv()
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

def get_supabase_client():
    """Get Supabase client, creating it only when needed"""
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables")
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def get_active_stocks():
    try:
        supabase = get_supabase_client()
        response = supabase.table('stocks').select('*').eq('is_active', True).execute()
        return response.data
    except Exception as e:
        print(f"Error fetching stocks from database: {e}")
        return []
