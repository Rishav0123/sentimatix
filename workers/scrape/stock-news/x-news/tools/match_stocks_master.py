import json
import difflib
import re
from supabase import create_client, Client
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

def extract_ids_from_url(url):
    pattern = r"stockpricequote/[^/]+/([^/]+)/([^/?#]+)"
    match = re.search(pattern, url)
    if match:
        return match.group(1), match.group(2)
    return None, None

def match_stocks():
    # Load MC Master Mapping
    with open('mc_master_mapping.json', 'r', encoding='utf-8') as f:
        mc_directory = json.load(f)
    
    mc_names = list(mc_directory.keys())
    
    # Connect to Supabase
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # Fetch all stocks that need mapping (mc_link_1 is placeholder or NULL)
    response = supabase.table('stocks').select('id, yfin_symbol, stock_name').limit(5000).execute()
    nse_stocks = response.data
    
    print(f"Loaded {len(nse_stocks)} stocks from Supabase.")
    
    results = []
    
    from tqdm import tqdm
    for stock in tqdm(nse_stocks):
        nse_name = stock['stock_name']
        
        # 1. Try Exact Match
        match_name = None
        if nse_name in mc_directory:
            match_name = nse_name
        else:
            # 2. Try Cleaned Exact Match (remove 'Limited', 'Ltd', etc.)
            clean_nse = re.sub(r'\s+(Limited|Ltd\.?|LTD\.?|Ltd)$', '', nse_name, flags=re.IGNORECASE).strip()
            # Try to find a match in MC names that starts with or is similar to the cleaned name
            matches = difflib.get_close_matches(clean_nse, mc_names, n=1, cutoff=0.8)
            if matches:
                match_name = matches[0]
        
        if match_name:
            url = mc_directory[match_name]
            mc1, mc2 = extract_ids_from_url(url)
            results.append({
                "Symbol": stock['yfin_symbol'],
                "NSE_Name": nse_name,
                "MC_Match": match_name,
                "MC1": mc1,
                "MC2": mc2,
                "Score": 1.0 # Placeholder
            })
        else:
            results.append({
                "Symbol": stock['yfin_symbol'],
                "NSE_Name": nse_name,
                "MC_Match": "NO MATCH FOUND",
                "MC1": None,
                "MC2": None,
                "Score": 0.0
            })
            
    # Save preview
    with open('mapping_preview.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    found = sum(1 for r in results if r['MC1'])
    print(f"\nMatching complete!")
    print(f"Matched: {found}/{len(results)}")
    print(f"Preview saved to mapping_preview.json")

if __name__ == "__main__":
    match_stocks()
