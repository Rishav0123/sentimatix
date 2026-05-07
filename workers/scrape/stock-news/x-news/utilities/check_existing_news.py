import os
import logging
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

def get_supabase_client():
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables")
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def check_existing_news(title: str, yfin_symbol: str, url: str = None) -> bool:
    """
    Checks if a news article already exists in the Supabase 'news' table
    to prevent duplicate entries.

    Dedup strategy (in priority order):
      1. URL match (url, yfin_symbol) — fast and reliable
      2. Title match (title, yfin_symbol) — fallback when URL is absent
    """
    try:
        supabase = get_supabase_client()

        # Fast path: URL-based dedup (most reliable)
        if url and url.strip():
            result = supabase.table('news').select('id') \
                .eq('url', url.strip()).eq('yfin_symbol', yfin_symbol).limit(1).execute()
            if result.data:
                return True

        # Fallback: title-based dedup
        result = supabase.table('news').select('id') \
            .eq('title', title).eq('yfin_symbol', yfin_symbol).limit(1).execute()
        return len(result.data) > 0

    except Exception as e:
        logging.error(f"Database error while checking existing news: {e}")
        # On error, assume it doesn't exist so we attempt to save it
        return False
