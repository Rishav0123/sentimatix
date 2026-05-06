import json
from collections import Counter, defaultdict
import os
from dotenv import load_dotenv

load_dotenv(r'd:\sentimatix\worker-SCRAPE\stock-news\x-news\.env')

def fetch_index_keywords():
    try:
        from supabase import create_client
        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_KEY')
        supabase = create_client(url, key)
        response = supabase.table('index').select('id, index_name, keywords').execute()
        return response.data
    except Exception as e:
        print(f"Error fetching index keywords: {e}")
        return []

def fetch_stock_keywords(supabase):
    all_stocks = []
    page_size = 1000
    offset = 0
    while True:
        res = supabase.table('stocks').select('yfin_symbol, keyword_lst').eq('is_active', True).range(offset, offset + page_size - 1).execute()
        if not res.data:
            break
        all_stocks.extend(res.data)
        if len(res.data) < page_size:
            break
        offset += page_size
    return all_stocks

def generate_duplicate_keyword_report():
    try:
        from supabase import create_client
        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_KEY')
        supabase = create_client(url, key)
    except Exception as e:
        print(f"Error initializing Supabase: {e}")
        return

    # Fetch live data
    stocks = fetch_stock_keywords(supabase)
    index_data = fetch_index_keywords()

    keyword_map = defaultdict(list)
    
    # Process Stocks
    for stock in stocks:
        symbol = stock.get('yfin_symbol', 'UNKNOWN')
        kws_data = stock.get('keyword_lst')
        
        keywords = []
        if kws_data:
            try:
                if isinstance(kws_data, str):
                    parsed = json.loads(kws_data)
                    if isinstance(parsed, dict) and 'keyword' in parsed:
                        keywords = parsed['keyword']
                elif isinstance(kws_data, dict) and 'keyword' in kws_data:
                    keywords = kws_data['keyword']
            except:
                pass
        
        for kw in keywords:
            clean_kw = str(kw).strip().lower()
            if clean_kw:
                keyword_map[clean_kw].append((f"Stock: {symbol}", str(kw).strip()))

    # Process Indexes
    for idx in index_data:
        name = idx.get('index_name', 'UNKNOWN')
        kws = idx.get('keywords', [])
        
        if isinstance(kws, str):
            kws = [k.strip() for k in kws.split(',') if k.strip()]
        
        if isinstance(kws, list):
            for kw in kws:
                clean_kw = str(kw).strip().lower()
                if clean_kw:
                    keyword_map[clean_kw].append((f"Index: {name}", str(kw).strip()))

    # Find duplicates
    duplicates = {kw: entries for kw, entries in keyword_map.items() if len(set(sym for sym, orig in entries)) > 1}

    # Sort by count descending
    sorted_duplicates = sorted(duplicates.items(), key=lambda x: len(set(sym for sym, orig in x[1])), reverse=True)

    output_path = r'd:\sentimatix\scratch\keyword_report.md'
    with open(output_path, 'w', encoding='utf-8') as out:
        out.write("# Duplicate Keyword Report\n\n")
        out.write(f"Total stocks analyzed: {len(stocks)}\n")
        out.write(f"Total unique keywords found: {len(keyword_map)}\n")
        out.write(f"Keywords used in multiple stocks: {len(sorted_duplicates)}\n\n")
        
        if not sorted_duplicates:
            out.write("No duplicate keywords found across different stocks.\n")
            return

        out.write("| Keyword | Count | Stocks |\n")
        out.write("|---------|-------|--------|\n")
        for kw_lower, entries in sorted_duplicates:
            symbols = sorted(list(set(sym for sym, orig in entries)))
            count = len(symbols)
            # Use one of the original case variants
            display_kw = entries[0][1]
            out.write(f"| {display_kw} | {count} | {', '.join(symbols)} |\n")
    
    print(f"Report generated at: {output_path}")

if __name__ == "__main__":
    generate_duplicate_keyword_report()
