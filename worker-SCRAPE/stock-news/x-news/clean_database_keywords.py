import os
import json
import argparse
from dotenv import load_dotenv
from supabase import create_client

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--live', action='store_true', help='Actually perform the database updates (Dry run by default)')
    args = parser.parse_args()
    
    dry_run = not args.live
    
    load_dotenv('.env')
    supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

    print(f"Starting Keyword Cleanup ({'DRY RUN' if dry_run else 'LIVE RUN'})")
    
    generic_suspects = {
        'the', 'and', 'ltd', 'limited', 'inc', 'corp', 'corporation', 'co', 'company',
        'bank', 'india', 'indian', 'asian', 'global', 'international', 'national',
        'steel', 'power', 'energy', 'finance', 'capital', 'holdings', 'group',
        'enterprises', 'industries', 'technologies', 'services', 'solutions', 'systems',
        'network', 'media', 'food', 'agro', 'pharma', 'chem', 'cement', 'motors',
        'auto', 'textiles', 'retail', 'hotels', 'infra', 'engineering', 'projects',
        'logistics', 'shipping', 'marine', 'financial', 'mutual', 'insurance',
        'health', 'medical', 'digital', 'tech', 'telecom', 'entertainment',
        'chemicals', 'metals', 'electronics', 'consumer', 'city', 'star',
        'royal', 'king', 'smart', 'expert', 'master', 'pro', 'first', 'best',
        'top', 'premium', 'prime', 'core', 'base', 'root', 'source', 'cloud',
        'data', 'info', 'cyber', 'virtual', 'real', 'true', 'pure', 'clear',
        'bright', 'shine', 'glow', 'spark', 'flash', 'light', 'sun', 'moon',
        'sky', 'earth', 'land', 'water', 'air', 'fire', 'wind', 'storm', 'rain',
        'green', 'blue', 'red', 'white', 'black', 'gold', 'silver', 'diamond',
        'new', 'old', 'modern', 'classic', 'vintage', 'retro', 'future', 'next',
        'now', 'today', 'tomorrow', 'fast', 'quick', 'speed', 'rapid', 'swift',
        'slow', 'steady', 'safe', 'secure', 'guard', 'shield', 'protect', 'defend',
        'save', 'keep', 'hold', 'catch', 'grab', 'take', 'get', 'have', 'own',
        'share', 'give', 'send', 'receive', 'accept', 'bring', 'carry', 'move',
        'go', 'come', 'stay', 'wait', 'stop', 'start', 'begin', 'end', 'finish',
        'complete', 'done', 'ready', 'set', 'empower', 'prakash', 'shree', 'sri',
        'jai', 'hind', 'bharat', 'hindustan', 'oriental', 'occidental', 'northern',
        'southern', 'eastern', 'western', 'central', 'pacific', 'atlantic', 'european',
        'american', 'african', 'universal', 'cosmic', 'galaxy', 'nova', 'apex',
        'zenith', 'summit', 'peak', 'crest', 'majestic', 'grand', 'super', 'mega',
        'ultra', 'max', 'plus', 'advance', 'intelligent', 'brilliant', 'genius',
        'champion', 'hero', 'leader', 'pioneer', 'choice', 'select', 'elite',
        'nexus', 'link', 'connect', 'grid', 'matrix', 'web', 'net',
        'all', 'any', 'some', 'many', 'few', 'much', 'more', 'most', 'less', 'least',
        'this', 'that', 'these', 'those', 'such', 'what', 'which', 'who', 'whom', 'whose',
        'gujarat', 'tata', 'jindal', 'indo', 'dcm', 'aditya', 'mahindra', 'jsw', 'bajaj',
        'kirloskar', 'vardhman', 'welspun', 'reliance', 'laxmi', 'blue', 'tvs', 'mangalam',
        'supreme', 'kothari', 'kalyani', 'premier', 'jubilant', 'apollo', 'godrej', 'future',
        'jk', 'manaksia', 'nahar', 'star', 'sundaram', 'united', 'muthoot', 'raj', 'zee',
        'deepak', 'icici', 'one', 'canara', 'aarti', 'dhunseri', 'arihant', 'aeroflex',
        'euro', 'pnb', 'arvind', 'sai', 'birla', 'emami', 'borosil', 'century', 'central',
        'ganesh', 'globe', 'inox', 'jain', 'lloyds', 'max', 'national', 'om', 'oriental',
        'oswal', 'prakash', 'ptc', 'raymond', 'shanti', 'shriram', 'shyam', 'tci', 'industrial'
    }

    all_stocks = []
    page_size = 1000
    offset = 0
    print("Fetching active stocks...")
    while True:
        res = supabase.table('stocks').select('id,yfin_symbol,keyword_lst').eq('is_active', True).range(offset, offset + page_size - 1).execute()
        if not res.data:
            break
        all_stocks.extend(res.data)
        if len(res.data) < page_size:
            break
        offset += page_size
        
    print(f"Total active stocks: {len(all_stocks)}")
    
    total_modified = 0
    total_deleted_kws = 0
    stocks_reduced_to_zero = 0
    
    for stock in all_stocks:
        raw_kws = stock.get('keyword_lst')
        if not raw_kws:
            continue
            
        # Parse keyword structure
        original_kws = []
        try:
            if isinstance(raw_kws, str):
                raw_kws = json.loads(raw_kws)
                
            if isinstance(raw_kws, dict) and 'keyword' in raw_kws:
                original_kws = raw_kws['keyword']
            elif isinstance(raw_kws, list):
                original_kws = raw_kws
        except Exception:
            continue
            
        if not original_kws:
            continue
            
        new_kws = []
        deleted_from_this_stock = []
        
        for kw in original_kws:
            kw_clean = str(kw).strip()
            kw_lower = kw_clean.lower()
            
            # Check if bad
            is_bad = False
            # If it's a single word and exactly in suspects
            if kw_lower in generic_suspects and ' ' not in kw_clean:
                is_bad = True
            # Or if it's <= 2 chars and doesn't contain spaces
            elif len(kw_clean) <= 2 and ' ' not in kw_clean:
                is_bad = True
                
            if is_bad:
                deleted_from_this_stock.append(kw_clean)
            else:
                new_kws.append(kw_clean)
                
        if deleted_from_this_stock:
            total_modified += 1
            total_deleted_kws += len(deleted_from_this_stock)
            
            if len(new_kws) == 0:
                stocks_reduced_to_zero += 1
                
            # Format the new value
            # Standardizing to dictionary format {"keyword": [...]} as seen in DB
            new_value = {"keyword": new_kws}
            
            # Just log it
            print(f"[{stock['yfin_symbol']}] Deleting {deleted_from_this_stock} -> New List: {new_kws}")
            
            if not dry_run:
                try:
                    supabase.table('stocks').update({'keyword_lst': json.dumps(new_value)}).eq('id', stock['id']).execute()
                except Exception as e:
                    print(f"Error updating {stock['yfin_symbol']}: {e}")

    print("\n--- SUMMARY ---")
    print(f"Stocks modified: {total_modified}")
    print(f"Total generic keywords deleted: {total_deleted_kws}")
    print(f"Stocks reduced to ZERO keywords: {stocks_reduced_to_zero}")
    if dry_run:
        print("\nTHIS WAS A DRY RUN. No database changes were made. Run with --live to execute.")
    else:
        print("\nLIVE RUN COMPLETE. Database has been updated.")

if __name__ == '__main__':
    main()
