import os
import time
import re
import json
import requests
from bs4 import BeautifulSoup
from supabase import create_client, Client
from dotenv import load_dotenv
from tqdm import tqdm

# Load environment variables
load_dotenv()
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

def get_supabase_client():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def extract_ids_from_url(url):
    pattern = r"stockpricequote/[^/]+/([^/]+)/([^/?#]+)"
    match = re.search(pattern, url)
    if match:
        return match.group(1), match.group(2)
    return None, None

def search_ddg_for_mc_link(stock_name):
    query = f"site:moneycontrol.com {stock_name} stock price quote"
    url = f"https://html.duckduckgo.com/html/?q={query}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            return None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        links = soup.select("a.result__a")
        
        for link in links:
            href = link.get('href')
            # Handle DDG redirection links
            if href and "moneycontrol.com/india/stockpricequote/" in href:
                # Sometimes DDG redirects like //duckduckgo.com/l/?uddg=URL
                if "uddg=" in href:
                    match = re.search(r"uddg=([^&]+)", href)
                    if match:
                        from urllib.parse import unquote
                        href = unquote(match.group(1))
                return href
        return None
    except Exception as e:
        print(f"Search error for {stock_name}: {e}")
        return None

def process_batch(limit=100):
    supabase = get_supabase_client()
    
    # Fetch stocks that need updating
    print(f"Fetching {limit} stocks from database...")
    response = supabase.table('stocks').select('id, yfin_symbol, stock_name').ilike('mc_link_1', '%.NS%').limit(limit).execute()
    stocks = response.data
    
    if not stocks:
        print("No stocks found to process.")
        return

    results = []
    print(f"Processing {len(stocks)} stocks via DuckDuckGo...")
    
    for stock in tqdm(stocks):
        mc_url = search_ddg_for_mc_link(stock['stock_name'])
        
        res = {
            "id": stock['id'],
            "yfin_symbol": stock['yfin_symbol'],
            "stock_name": stock['stock_name'],
            "mc_url": mc_url if mc_url else "NOT_FOUND",
            "mc_link_1": None,
            "mc_link_2": None
        }
        
        if mc_url:
            mc1, mc2 = extract_ids_from_url(mc_url)
            res["mc_link_1"] = mc1
            res["mc_link_2"] = mc2
            
        results.append(res)
        time.sleep(2) # Polite delay to avoid rate limiting
        
    # Save results locally
    output_file = 'extracted_mc_links_100.json'
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nCompleted! Results saved to {output_file}")
    
    # Show summary
    found_count = sum(1 for r in results if r['mc_url'] != "NOT_FOUND")
    print(f"Successfully matched: {found_count}/{len(results)}")

if __name__ == "__main__":
    process_batch(100)
