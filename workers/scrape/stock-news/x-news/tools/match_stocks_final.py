import json
import difflib
import re
from supabase import create_client, Client
import os
from tqdm import tqdm
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

def extract_ids_from_url(url):
    # Pattern: stockpricequote/[category]/[name]/[id]
    pattern = r"stockpricequote/[^/]+/([^/]+)/([^/?#]+)"
    match = re.search(pattern, url)
    if match:
        return match.group(1), match.group(2)
    return None, None

def clean_name(name):
    # Remove noise words and special characters
    noise = r'\s+(Limited|Ltd\.?|LTD\.?|Ltd|India|Holdings?|Corporation|Corp\.?|Group|Services|Technologies|Industries|Inds\.?|Systems|Engineering|Infrastructure|Projects|Ventures|Solutions)\b'
    name = re.sub(noise, '', name, flags=re.IGNORECASE)
    name = re.sub(r'[^\w\s]', '', name) # Remove special chars
    return name.strip().lower()

def match_stocks(limit=100):
    # Load MC Master Mapping
    with open('mc_master_mapping.json', 'r', encoding='utf-8') as f:
        mc_directory = json.load(f)
    
    # Pre-clean MC names for matching
    mc_mapping_cleaned = {clean_name(name): name for name in mc_directory.keys()}
    mc_names_cleaned = list(mc_mapping_cleaned.keys())
    
    # Connect to Supabase
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # Fetch all stocks (using pagination to bypass 1000 limit)
    nse_stocks = []
    start = 0
    page_size = 1000
    
    while True:
        response = supabase.table('stocks').select('id, yfin_symbol, stock_name').range(start, start + page_size - 1).execute()
        if not response.data:
            break
        nse_stocks.extend(response.data)
        if len(response.data) < page_size:
            break
        start += page_size
    
    print(f"Loaded {len(nse_stocks)} stocks from Supabase.")
    
    results = []
    
    for stock in tqdm(nse_stocks):
        nse_name = stock['stock_name']
        symbol_base = stock['yfin_symbol'].split('.')[0].lower()
        
        # 1. Try Cleaned Exact Match
        nse_cleaned = clean_name(nse_name)
        match_found = None
        
        if nse_cleaned in mc_mapping_cleaned:
            match_found = mc_mapping_cleaned[nse_cleaned]
        else:
            # 2. Try Fuzzy Match on Cleaned Names with high cutoff
            matches = difflib.get_close_matches(nse_cleaned, mc_names_cleaned, n=1, cutoff=0.9)
            if matches:
                match_found = mc_mapping_cleaned[matches[0]]
        
        if match_found:
            url = mc_directory[match_found]
            mc1, mc2 = extract_ids_from_url(url)
            
            # 3. Double Check with Symbol (Heuristic)
            symbol_match = False
            if symbol_base in mc2.lower() or mc2.lower() in symbol_base:
                symbol_match = True
            
            results.append({
                "Symbol": stock['yfin_symbol'],
                "NSE_Name": nse_name,
                "MC_Match": match_found,
                "MC1": mc1,
                "MC2": mc2,
                "Status": "Matched" if symbol_match else "Verify"
            })
        else:
            results.append({
                "Symbol": stock['yfin_symbol'],
                "NSE_Name": nse_name,
                "MC_Match": "NO MATCH FOUND",
                "MC1": None,
                "MC2": None,
                "Status": "Missing"
            })
            
    # Save preview
    output_file = 'full_mapping_directory.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    found = sum(1 for r in results if r['MC1'])
    print(f"\nDirectory matching complete for all stocks!")
    print(f"Matched: {found}/{len(results)}")
    print(f"Results saved to {output_file}")

if __name__ == "__main__":
    match_stocks(5000)
