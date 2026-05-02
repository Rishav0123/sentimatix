import json
import time
import re
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
        return None

def run_full_fallback(batch_size=200):
    # Load the results from the directory matching
    with open('full_mapping_directory.json', 'r') as f:
        mapping = json.load(f)
    
    missing_stocks = [m for m in mapping if m['Status'] == 'Missing']
    print(f"Total missing: {len(missing_stocks)}. Processing first {batch_size}...")
    
    # Only process a batch to be safe
    stocks_to_process = missing_stocks[:batch_size]
    
    updated_count = 0
    for stock in tqdm(stocks_to_process):
        name = stock['NSE_Name']
        mc_url = search_ddg_for_mc_link(name)
        
        if mc_url:
            mc1, mc2 = extract_ids_from_url(mc_url)
            if mc1 and mc2:
                stock['MC_Match'] = "FOUND VIA FALLBACK"
                stock['MC1'] = mc1
                stock['MC2'] = mc2
                stock['Status'] = "Matched"
                updated_count += 1
        
        time.sleep(2.5) # Polite delay for larger batch
        
    # Save updated mapping
    with open('full_mapping_with_fallback.json', 'w') as f:
        json.dump(mapping, f, indent=2)
    
    print(f"\nBatch fallback complete! Recovered {updated_count}/{len(stocks_to_process)} stocks.")

if __name__ == "__main__":
    run_full_fallback(200) # Start with 200
