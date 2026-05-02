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
    """
    Extracts mc_link_1 and mc_link_2 from MoneyControl URL
    Pattern: https://www.moneycontrol.com/india/stockpricequote/{sector}/{slug}/{id}
    """
    pattern = r"stockpricequote/[^/]+/([^/]+)/([^/?#]+)"
    match = re.search(pattern, url)
    if match:
        return match.group(1), match.group(2)
    return None, None

def process_stocks(limit=5):
    supabase = get_supabase_client()
    
    # Fetch stocks that need updating (where mc_link_1 matches placeholder or is empty)
    # We'll check for stocks where mc_link_1 contains '.NS' which was our placeholder
    response = supabase.table('stocks').select('id, yfin_symbol, stock_name').ilike('mc_link_1', '%.NS%').limit(limit).execute()
    stocks = response.data
    
    if not stocks:
        print("No stocks found that need updating.")
        return

    print(f"Processing {len(stocks)} stocks...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36")
        page = context.new_page()

        for stock in stocks:
            symbol = stock['yfin_symbol'].split('.')[0]
            name = stock['stock_name']
            print(f"\nSearching for {symbol} ({name})...")
            
            try:
                # Go to MoneyControl
                page.goto("https://www.moneycontrol.com/", timeout=60000)
                
                # Handle popups
                try:
                    # Cancel notification popup if it appears
                    page.wait_for_selector("button.wzrk-cancel", timeout=3000)
                    page.click("button.wzrk-cancel")
                except:
                    pass

                # Find search bar and type
                search_selector = "input#search_str"
                page.wait_for_selector(search_selector, timeout=10000)
                page.click(search_selector) # Focus
                page.fill(search_selector, symbol)
                
                # Wait for suggestions dropdown
                # The subagent mentioned .mctv6suggest or .suggestion_box
                dropdown_selector = ".mctv6suggest"
                page.wait_for_selector(dropdown_selector, timeout=15000)
                time.sleep(2) # Stabilize
                
                # Click the first matching result 
                # We target the first link in the suggestion box
                suggestion_link = "div.suggestion_box a"
                page.wait_for_selector(suggestion_link, timeout=5000)
                
                # Log the text of the link to be sure
                link_text = page.inner_text(suggestion_link)
                print(f"Clicking suggestion: {link_text.strip()}")
                
                page.click(suggestion_link)
                
                # Wait for navigation
                page.wait_for_load_state("networkidle", timeout=30000)
                
                current_url = page.url
                mc1, mc2 = extract_ids_from_url(current_url)
                
                if mc1 and mc2:
                    print(f"Found: mc1={mc1}, mc2={mc2}")
                    # Update database
                    supabase.table('stocks').update({
                        'mc_link_1': mc1,
                        'mc_link_2': mc2
                    }).eq('id', stock['id']).execute()
                    print(f"Updated {symbol} in database.")
                else:
                    print(f"Could not extract IDs from URL: {current_url}")
                    
            except Exception as e:
                print(f"Error processing {symbol}: {e}")
                # Save screenshot for debugging
                page.screenshot(path=f"error_{symbol}.png")
                
        browser.close()

if __name__ == "__main__":
    import sys
    batch_limit = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    process_stocks(limit=batch_limit)
