from supabase import create_client, Client
from dotenv import load_dotenv
import os
import json

load_dotenv()
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

def get_supabase_client():
    """Get Supabase client, creating it only when needed"""
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables")
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def fetch_stock_keywords():
    """
    Fetch keywords for all active stocks from the 'stocks' table.
    Returns a list of dicts: [{id, yfin_symbol, stock_name, keyword_lst}, ...]
    """
    try:
        supabase = get_supabase_client()
        response = supabase.table('stocks').select('id, yfin_symbol, stock_name, keyword_lst').eq('is_active', True).execute()
        return response.data
    except Exception as e:
        print(f"Error fetching stock keywords: {e}")
        return []

def fetch_index_keywords():
    """
    Fetch keywords for all indexes from the 'index' table.
    Returns a list of dicts: [{id, index_name, keywords}, ...]
    """
    try:
        supabase = get_supabase_client()
        response = supabase.table('index').select('id, index_name, keywords').execute()
        return response.data
    except Exception as e:
        print(f"Error fetching index keywords: {e}")
        return []

def parse_keyword_json(keyword_data):
    """
    Parse the keyword_lst JSON field which contains structure like:
    {"keyword": ["ABB India", "ABB India Limited", "ABB Ltd"]}
    """
    keywords = []
    
    if not keyword_data:
        return keywords
    
    try:
        # If it's already a dict, use it directly
        if isinstance(keyword_data, dict):
            json_data = keyword_data
        # If it's a string, parse it as JSON
        elif isinstance(keyword_data, str):
            json_data = json.loads(keyword_data)
        else:
            return keywords
        
        # Extract keywords from the "keyword" field
        if "keyword" in json_data and isinstance(json_data["keyword"], list):
            keywords.extend(json_data["keyword"])
        
    except (json.JSONDecodeError, TypeError, KeyError) as e:
        print(f"Error parsing keyword JSON: {e}, data: {keyword_data}")
    
    return keywords

def get_all_keywords():
    """
    Get all keywords from both stocks and indexes tables and return as a flat list
    """
    all_keywords = []
    
    # Get stock keywords
    stock_data = fetch_stock_keywords()
    for stock in stock_data:
        # Add symbol
        if stock.get('yfin_symbol'):
            all_keywords.append(stock['yfin_symbol'])
        
        # Add stock name
        if stock.get('stock_name'):
            all_keywords.append(stock['stock_name'])
        
        # Parse and add keywords from keyword_lst JSON
        if stock.get('keyword_lst'):
            parsed_keywords = parse_keyword_json(stock['keyword_lst'])
            all_keywords.extend(parsed_keywords)
    
    # Get index keywords
    index_data = fetch_index_keywords()
    for index in index_data:
        # Add index name
        if index.get('index_name'):
            all_keywords.append(index['index_name'])
        
        # Add keywords from keywords field
        if index.get('keywords'):
            if isinstance(index['keywords'], list):
                all_keywords.extend(index['keywords'])
            elif isinstance(index['keywords'], str):
                # Split by comma and clean up
                keywords = [k.strip() for k in index['keywords'].split(',') if k.strip()]
                all_keywords.extend(keywords)
    
    # Remove duplicates and empty strings
    all_keywords = list(set([k.strip() for k in all_keywords if k and k.strip()]))
    
    # Add fallback keywords if nothing found
    if not all_keywords:
        all_keywords = [
            'stock', 'share', 'market', 'NSE', 'BSE', 'Sensex', 'Nifty',
            'earnings', 'profit', 'revenue', 'investment', 'dividend',
            'Reliance', 'HDFC', 'TCS', 'Infosys', 'Wipro'
        ]
    
    return all_keywords

if __name__ == "__main__":
    stock_keywords = fetch_stock_keywords()
    print("Stock Keywords:")
    for sk in stock_keywords[:5]:  # Show first 5 only
        print(f"Symbol: {sk.get('yfin_symbol')}, Name: {sk.get('stock_name')}")
        if sk.get('keyword_lst'):
            parsed = parse_keyword_json(sk['keyword_lst'])
            print(f"  Parsed keywords: {parsed}")
        print()

    index_keywords = fetch_index_keywords()
    print(f"\nIndex Keywords: {len(index_keywords)} found")
    
    all_kw = get_all_keywords()
    print(f"\nTotal unique keywords: {len(all_kw)}")
    print(f"Sample keywords: {all_kw[:10]}")