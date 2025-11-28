"""
MCP Tool: Identify Key Stock Developments from News
Analyzes recent news articles and identifies significant developments
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional
import os
from pathlib import Path
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables from mcp/.env
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

# Initialize Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Missing SUPABASE_URL or SUPABASE_KEY in environment")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def get_stock_id(symbol: str) -> Optional[str]:
    """
    Get the stock_id (UUID) from the stocks table for a given symbol
    
    Args:
        symbol: Stock symbol (e.g., 'TCS', 'INFY')
    
    Returns:
        UUID string of the stock, or None if not found
    """
    try:
        # Try both with and without .NS suffix
        symbols_to_try = [symbol, f"{symbol}.NS", symbol.replace('.NS', '')]
        
        response = supabase.table('stocks') \
            .select('id') \
            .in_('yfin_symbol', symbols_to_try) \
            .limit(1) \
            .execute()
        
        if response.data:
            return response.data[0]['id']
        return None
    except Exception as e:
        print(f"Error fetching stock_id for {symbol}: {e}")
        return None


def identify_key_developments(symbol: str, hours_back: int = 24) -> List[Dict]:
    """
    Identify key developments for a stock from recent news
    
    Args:
        symbol: Stock symbol (e.g., 'TCS', 'INFY')
        hours_back: How many hours of news to analyze
    
    Returns:
        List of identified developments with title, summary, category, sentiment
    """
    # Calculate time window
    cutoff_time = datetime.now() - timedelta(hours=hours_back)
    
    # Fetch recent news for this stock
    # Match both .NS and bare symbol
    response = supabase.table('news') \
        .select('id, title, content, published_at, sentiment_score') \
        .in_('yfin_symbol', [symbol, f"{symbol}.NS"]) \
        .gte('published_at', cutoff_time.isoformat()) \
        .order('published_at', desc=True) \
        .execute()
    
    articles = response.data
    
    if not articles:
        return []
    
    # Group articles by topic/theme using simple keyword matching
    developments = []
    
    # Define development categories with keywords
    categories = {
        'earnings': ['earnings', 'profit', 'revenue', 'quarterly', 'q1', 'q2', 'q3', 'q4', 'results', 'performance'],
        'merger': ['merger', 'acquisition', 'buyout', 'takeover', 'acquire', 'deal'],
        'regulatory': ['regulation', 'compliance', 'approval', 'license', 'permit', 'sebi', 'rbi'],
        'product': ['launch', 'product', 'service', 'release', 'unveil', 'introduce'],
        'financial': ['dividend', 'stock split', 'buyback', 'debt', 'funding', 'investment'],
        'management': ['ceo', 'cfo', 'appointment', 'resign', 'director', 'board'],
        'partnership': ['partnership', 'collaboration', 'alliance', 'tie-up', 'joint venture'],
        'expansion': ['expansion', 'plant', 'facility', 'capacity', 'growth', 'market entry']
    }
    
    # Track processed article groups to avoid duplicates
    processed_article_ids = set()
    
    for article in articles:
        if article['id'] in processed_article_ids:
            continue
            
        title_lower = article['title'].lower()
        content_lower = (article.get('content', '') or '').lower()
        combined_text = title_lower + ' ' + content_lower
        
        # Determine category
        detected_category = 'general'
        max_matches = 0
        
        for category, keywords in categories.items():
            matches = sum(1 for kw in keywords if kw in combined_text)
            if matches > max_matches:
                max_matches = matches
                detected_category = category
        
        # Only create development if it's significant (has category matches)
        if max_matches == 0:
            continue
        
        # Determine sentiment
        sentiment_score = article.get('sentiment_score') or 0  # Handle None from database
        if sentiment_score > 0.2:
            sentiment = 'positive'
        elif sentiment_score < -0.2:
            sentiment = 'negative'
        else:
            sentiment = 'neutral'
        
        # Create development summary
        # Extract first 200 chars of content as summary
        summary = article.get('content', article['title'])[:200]
        if len(summary) == 200:
            summary += '...'
        
        # Handle None sentiment_score
        impact_score = 0.5  # Default neutral impact
        if sentiment_score is not None:
            impact_score = min(abs(sentiment_score), 1.0)
        
        development = {
            'stock_id': None,  # Will be set by caller
            'development_date': article['published_at'],
            'title': article['title'],
            'summary': summary,
            'category': detected_category,
            'sentiment': sentiment,
            'impact_score': impact_score
            # Note: source_article_ids removed - schema expects INTEGER[] but news.id is UUID
        }
        
        developments.append(development)
        processed_article_ids.add(article['id'])
    
    # Sort by impact score (most significant first), handle None values
    developments.sort(key=lambda x: x.get('impact_score', 0.0), reverse=True)
    
    # Return top 5 most significant developments
    return developments[:5]


def store_developments(developments: List[Dict]) -> bool:
    """
    Store identified developments in the database
    
    Args:
        developments: List of development dictionaries
    
    Returns:
        True if successful
    """
    if not developments:
        return True
    
    try:
        # Insert developments
        response = supabase.table('stock_developments').insert(developments).execute()
        return True
    except Exception as e:
        print(f"Error storing developments: {e}")
        return False


def process_stock_developments(symbol: str) -> Dict:
    """
    Main function to identify and store developments for a stock
    
    Args:
        symbol: Stock symbol
    
    Returns:
        Status dictionary with count of developments found
    """
    # Get stock_id first
    stock_id = get_stock_id(symbol)
    if not stock_id:
        return {
            'symbol': symbol,
            'developments_found': 0,
            'stored': False,
            'error': 'Stock ID not found in database',
            'developments': []
        }
    
    developments = identify_key_developments(symbol, hours_back=24)
    
    if developments:
        # Set stock_id for all developments
        for dev in developments:
            dev['stock_id'] = stock_id
        
        success = store_developments(developments)
        return {
            'symbol': symbol,
            'developments_found': len(developments),
            'stored': success,
            'developments': developments
        }
    
    return {
        'symbol': symbol,
        'developments_found': 0,
        'stored': False,
        'developments': []
    }


if __name__ == '__main__':
    # Test with a symbol
    result = process_stock_developments('TCS')
    print(f"Processed {result['symbol']}: Found {result['developments_found']} developments")
    for dev in result['developments']:
        print(f"  - [{dev['category']}] {dev['title']}")
