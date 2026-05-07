import json
import re
import os
from fuzzywuzzy import process, fuzz
from tqdm import tqdm

def extract_ids_from_url(url):
    pattern = r"stockpricequote/[^/]+/([^/]+)/([^/?#]+)"
    match = re.search(pattern, url)
    if match:
        return match.group(1), match.group(2)
    return None, None

def match_missing():
    # Load files
    mapping_file = 'full_mapping_directory.json'
    master_file = 'mc_master_mapping.json'
    
    if not os.path.exists(mapping_file) or not os.path.exists(master_file):
        print("Missing required files.")
        return

    with open(mapping_file, 'r') as f:
        mapping = json.load(f)
    
    with open(master_file, 'r') as f:
        master = json.load(f)
    
    # Prepare master list for matching
    # Only keep real stock links, not landing pages
    master_entries = []
    for key, url in master.items():
        if "/india/stockpricequote/" in url and not url.endswith("/Y") and not url.endswith("/others"):
            master_entries.append({'key': key, 'url': url})
            
    print(f"Loaded {len(mapping)} stocks and {len(master_entries)} valid master links.")
    
    updated_count = 0
    missing_stocks = [s for s in mapping if s['Status'] == 'Missing']
    
    # Optimization: pre-calculate master keys for fuzzy matching
    master_keys = [e['key'] for e in master_entries]
    
    for stock in tqdm(missing_stocks, desc="Matching missing stocks"):
        symbol = stock['Symbol'].split('.')[0].upper()
        nse_name = stock['NSE_Name']
        
        # Strategy 1: Exact Symbol Match in Master Key (Fast)
        found = False
        for entry in master_entries:
            key_upper = entry['key'].upper()
            # Common patterns: ", SYMBOL, ", " SYMBOL ", etc.
            if f", {symbol}," in key_upper or f" {symbol} " in key_upper or key_upper.endswith(f" {symbol}") or f"({symbol})" in key_upper:
                mc1, mc2 = extract_ids_from_url(entry['url'])
                if mc1 and mc2:
                    stock['MC1'] = mc1
                    stock['MC2'] = mc2
                    stock['MC_Match'] = entry['key']
                    stock['Status'] = 'Verify'
                    updated_count += 1
                    found = True
                    break
        
        if found: continue
            
        # Strategy 2: Fuzzy Match Name (Slow)
        # Only use if symbol match fails
        # Use token_set_ratio which is good for names like "Hindustan Unilever" vs "HUL" or partial names
        best_match = process.extractOne(nse_name, master_keys, scorer=fuzz.token_set_ratio)
        if best_match and best_match[1] > 90:
            match_key = best_match[0]
            # Find the entry for this key
            match_entry = next(e for e in master_entries if e['key'] == match_key)
            mc1, mc2 = extract_ids_from_url(match_entry['url'])
            if mc1 and mc2:
                stock['MC1'] = mc1
                stock['MC2'] = mc2
                stock['MC_Match'] = match_key
                stock['Status'] = 'Verify'
                updated_count += 1
                
    print(f"\nSuccessfully matched {updated_count} stocks locally.")
    
    # Save results
    output_file = 'full_mapping_v2.json'
    with open(output_file, 'w') as f:
        json.dump(mapping, f, indent=2)
    print(f"Updated mapping saved to {output_file}")

if __name__ == "__main__":
    match_missing()
