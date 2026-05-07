import os
import time
import re
from playwright.sync_api import sync_playwright
from supabase import create_client, Client
from dotenv import load_dotenv

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

def search_google_for_mc_link(page, stock_name):
    query = f"site:moneycontrol.com {stock_name} stock price quote"
    url = f"https://www.google.com/search?q={query}"
    print(f"Searching Google for: {stock_name}...")
    
    try:
        page.goto(url, timeout=30000)
        
        # Look for the first result that matches moneycontrol.com
        # Google search results are usually in <a> tags inside h3
        page.wait_for_selector("h3", timeout=10000)
        links = page.query_selector_all("a")
        
        for link in links:
            href = link.get_attribute("href")
            if href and "moneycontrol.com/india/stockpricequote/" in href:
                # Some links are wrapped in google redirection, but Playwright handles it often
                # Or we can extract it
                if "google.com" in href:
                    match = re.search(r"url\?q=([^&]+)", href)
                    if match:
                        href = match.group(1)
                
                return href
        return None
    except Exception as e:
        print(f"Google search error for {stock_name}: {e}")
        return None

def test_strategy(limit=5):
    supabase = get_supabase_client()
    response = supabase.table('stocks').select('id, yfin_symbol, stock_name').ilike('mc_link_1', '%.NS%').limit(limit).execute()
    stocks = response.data
    
    if not stocks:
        print("No stocks found to test.")
        return

    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36")
        page = context.new_page()

        for stock in stocks:
            mc_url = search_google_for_mc_link(page, stock['stock_name'])
            if mc_url:
                mc1, mc2 = extract_ids_from_url(mc_url)
                results.append({
                    "Symbol": stock['yfin_symbol'],
                    "Name": stock['stock_name'],
                    "Found_URL": mc_url,
                    "MC1": mc1,
                    "MC2": mc2
                })
            else:
                results.append({
                    "Symbol": stock['yfin_symbol'],
                    "Name": stock['stock_name'],
                    "Found_URL": "NOT FOUND",
                    "MC1": None,
                    "MC2": None
                })
            time.sleep(2) # Delay for Google

        browser.close()
    
    print("\n--- Strategy Test Results ---")
    for res in results:
        print(f"Stock: {res['Symbol']} ({res['Name']})")
        print(f"  URL: {res['Found_URL']}")
        print(f"  IDs: mc1={res['MC1']}, mc2={res['MC2']}")
        print("-" * 30)

if __name__ == "__main__":
    test_strategy(5)
