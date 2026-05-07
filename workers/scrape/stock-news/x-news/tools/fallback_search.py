import os
import time
import re
import json
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
from urllib.parse import unquote

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
            if href and "moneycontrol.com/india/stockpricequote/" in href:
                if "uddg=" in href:
                    match = re.search(r"uddg=([^&]+)", href)
                    if match:
                        href = unquote(match.group(1))
                return href
        return None
    except Exception as e:
        print(f"Search error for {stock_name}: {e}")
        return None

def process_fallback(limit=100):
    input_file = 'full_mapping_v2.json'
    output_file = 'full_mapping_v3.json'
    
    if not os.path.exists(input_file):
        print(f"Input file {input_file} not found.")
        return

    with open(input_file, 'r') as f:
        mapping = json.load(f)
    
    missing_stocks = [s for s in mapping if s['Status'] == 'Missing']
    print(f"Found {len(missing_stocks)} missing stocks. Processing up to {limit}...")
    
    to_process = missing_stocks[:limit]
    updated_count = 0
    
    try:
        for stock in tqdm(to_process, desc="Searching web"):
            stock_name = stock['NSE_Name']
            mc_url = search_ddg_for_mc_link(stock_name)
            
            if mc_url:
                mc1, mc2 = extract_ids_from_url(mc_url)
                if mc1 and mc2:
                    stock['MC1'] = mc1
                    stock['MC2'] = mc2
                    stock['MC_Match'] = mc_url
                    stock['Status'] = 'Verify'
                    updated_count += 1
                else:
                    # Mark as definitively not found if it looks wrong
                    stock['Status'] = 'Not Found'
            else:
                # Optional: keep as missing to try again or mark as Not Found
                # For now keep as Missing so we can try Google later if needed
                pass
            
            # Polite delay
            time.sleep(3)
            
            # Incremental save every 10 updates
            if updated_count % 10 == 0 and updated_count > 0:
                with open(output_file, 'w') as f:
                    json.dump(mapping, f, indent=2)
                    
    except KeyboardInterrupt:
        print("\nInterrupted by user. Saving progress...")
    
    with open(output_file, 'w') as f:
        json.dump(mapping, f, indent=2)
    
    print(f"\nFinished batch. Successfully found {updated_count} stocks.")
    print(f"Results saved to {output_file}")

if __name__ == "__main__":
    # Process in batches of 100 to be safe
    process_fallback(100)
