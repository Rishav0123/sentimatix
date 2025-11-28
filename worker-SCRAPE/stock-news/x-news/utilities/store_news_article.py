from .check_existing_news import check_existing_news
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

def store_news_article(news_data):
    try:
        # Use check_existing_news utility for duplicate check
        if check_existing_news(news_data['title'], news_data['published_at'], news_data['yfin_symbol']):
            return False
        
        supabase = get_supabase_client()
        result = supabase.table('news').insert(news_data).execute()
        return bool(result.data)
    except Exception as e:
        print(f"Error storing news article: {e}")
        return False
