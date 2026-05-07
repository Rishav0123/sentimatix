import os
import json
from collections import Counter, defaultdict
from dotenv import load_dotenv
from supabase import create_client

def get_prefixes(name, num_words):
    # Strip common leading noise for cleaner prefixes
    name_clean = name.strip()
    if name_clean.lower().startswith('the '):
        name_clean = name_clean[4:].strip()
    
    words = name_clean.split()
    if len(words) <= num_words:
        return name_clean
    return " ".join(words[:num_words])

def refine_group_keywords():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--live', action='store_true')
    args = parser.parse_args()
    dry_run = not args.live

    load_dotenv(r'd:\sentimatix\workers/scrape\stock-news\x-news\.env')
    supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

    print("Fetching active stocks...")
    all_stocks = []
    page_size = 1000
    offset = 0
    while True:
        res = supabase.table('stocks').select('id,yfin_symbol,stock_name,keyword_lst').eq('is_active', True).range(offset, offset + page_size - 1).execute()
        if not res.data:
            break
        all_stocks.extend(res.data)
        if len(res.data) < page_size:
            break
        offset += page_size
    
    print(f"Total active stocks: {len(all_stocks)}")

    # Step 1: Calculate 2-word prefixes and their counts
    prefix2_map = defaultdict(list)
    for stock in all_stocks:
        name = stock.get('stock_name', '')
        if not name: continue
        p2 = get_prefixes(name, 2)
        prefix2_map[p2.lower()].append(stock['yfin_symbol'])

    # Step 2: Identify group names to remove (standalone or multi-word)
    group_names = {
        'tata', 'aditya', 'jsw', 'bajaj', 'mahindra', 'reliance', 'birla', 'jindal', 'adani', 'hdfc', 'icici', 'axis', 'itc', 'wipro', 'infosys',
        'gujarat', 'tamilnadu', 'tamil', 'nadu', 'andhra', 'maharashtra', 'punjab', 'karnataka', 'kerala', 'haryana', 'rajasthan', 'indianoil',
        'tamil nadu', 'madhya pradesh', 'uttar pradesh', 'west bengal', 'himachal pradesh'
    }

    # Step 3: Calculate 3-word prefixes for those that have 2-word duplicates
    # and also for those where the 2-word prefix is a known group/state name
    final_prefixes = {}
    for stock in all_stocks:
        symbol = stock['yfin_symbol']
        name = stock.get('stock_name', '')
        if not name: continue
        
        p2 = get_prefixes(name, 2)
        p2_lower = p2.lower()
        
        # If p2 is a duplicate OR it's a known generic/group name, use 3 words
        if len(prefix2_map[p2_lower]) > 1 or p2_lower in group_names:
            # Duplicate or generic found with 2 words, use 3 words
            p3 = get_prefixes(name, 3)
            final_prefixes[symbol] = p3
        else:
            final_prefixes[symbol] = p2
    
    total_updated = 0
    
    for stock in all_stocks:
        symbol = stock['yfin_symbol']
        raw_kws = stock.get('keyword_lst')
        if not raw_kws: continue
        
        try:
            if isinstance(raw_kws, str):
                raw_kws = json.loads(raw_kws)
            if isinstance(raw_kws, dict) and 'keyword' in raw_kws:
                kws = raw_kws['keyword']
            else:
                kws = []
        except:
            continue

        # 1. Logic to filter keywords
        new_kws = []
        name_for_prefix = stock['stock_name'].strip()
        if name_for_prefix.lower().startswith('the '):
            name_for_prefix = name_for_prefix[4:].strip()
        
        first_word = name_for_prefix.split()[0].lower() if name_for_prefix else ""
        
        symbol_short = symbol.replace('.NS', '').lower()
        
        for kw in kws:
            kw_clean = str(kw).strip()
            kw_lower = kw_clean.lower()
            
            # PROTECT: Never remove if it matches the symbol (case-insensitive)
            if kw_lower == symbol_short:
                new_kws.append(kw_clean)
                continue

            # Remove if it's a standalone group name
            if kw_lower in group_names:
                continue
                
            # Remove if it's just the first word of the company name and is a single word
            if kw_lower == first_word and ' ' not in kw_clean:
                continue
            
            new_kws.append(kw_clean)
        
        # 2. Add the refined prefix
        prefix = final_prefixes.get(symbol)
        if prefix and prefix.lower() not in [k.lower() for k in new_kws]:
            new_kws.append(prefix)
            
        # 3. Ensure the short symbol itself is ALWAYS present
        symbol_display = symbol.replace('.NS', '')
        if symbol_display.lower() not in [k.lower() for k in new_kws]:
            new_kws.append(symbol_display)
        
        # 3. Clean duplicates and sort
        new_kws = list(dict.fromkeys(new_kws)) # preserve order, remove duplicates
        
        if set(new_kws) != set(kws):
            total_updated += 1
            print(f"[{symbol}] Updating keywords: {kws} -> {new_kws}")
            
            if not dry_run:
                # LIVE UPDATE
                try:
                    new_value = {"keyword": new_kws}
                    supabase.table('stocks').update({'keyword_lst': json.dumps(new_value)}).eq('id', stock['id']).execute()
                except Exception as e:
                    print(f"Error updating {symbol}: {e}")

    if dry_run:
        print(f"\n[DRY RUN] Would have updated {total_updated} stocks.")
    else:
        print(f"\nSummary: Updated {total_updated} stocks with refined prefixes and removed standalone group names.")

if __name__ == "__main__":
    refine_group_keywords()
