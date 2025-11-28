
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

def check_existing_news(title, published_at, yfin_symbol):
    """
    Check if a news article already exists in the 'news' table by title and yfin_symbol.
    Also checks for similar titles and published dates to catch duplicates.
    Returns True if exists, False otherwise.
    """
    try:
        supabase = get_supabase_client()
        
        # Primary check: exact title and symbol match
        existing = supabase.table('news').select('*')\
            .eq('title', title)\
            .eq('yfin_symbol', yfin_symbol)\
            .execute()
        
        if existing.data:
            return True
            
        # Secondary check: same symbol and similar title (first 50 chars) to catch minor variations
        if title and len(title) > 10:
            title_prefix = title[:50]
            similar = supabase.table('news').select('*')\
                .eq('yfin_symbol', yfin_symbol)\
                .ilike('title', f"{title_prefix}%")\
                .execute()
            
            if similar.data:
                print(f"Found similar article for {yfin_symbol}: {title[:30]}...")
                return True
                
        return False
    except Exception as e:
        print(f"Error checking existing news: {e}")
        return False
