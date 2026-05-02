import json
import time
import os
import re
from playwright.sync_api import sync_playwright

def scrape_mc_letter_playwright(page, letter):
    url = f"https://www.moneycontrol.com/india/stockpricequote/{letter}"
    print(f"Scraping letter: {letter}...")
    
    try:
        # Increase timeout and use 'networkidle'
        page.goto(url, timeout=60000, wait_until="networkidle")
        
        # Wait for the table to be visible
        page.wait_for_selector("table.pcq_tbl", timeout=20000)
        
        # Extract stock names and links
        links = page.query_selector_all("table.pcq_tbl a.bl_12")
        
        stocks = {}
        for link in links:
            name = link.inner_text().strip()
            href = link.get_attribute("href")
            if name and href:
                stocks[name] = href
        
        print(f"Found {len(stocks)} stocks for letter {letter}")
        return stocks
    except Exception as e:
        print(f"Error scraping {letter}: {e}")
        # Save screenshot on error
        page.screenshot(path=f"debug_scrape_{letter}.png")
        return {}

def build_directory(letters=['D', 'V', 'T', 'R']):
    master_directory = {}
    
    with sync_playwright() as p:
        # Try launching with a visible window for debugging if needed, but keeping headless for now
        browser = p.chromium.launch(headless=True)
        # Use a more modern UA
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        page = context.new_page()
        
        for char in letters:
            stocks = scrape_mc_letter_playwright(page, char)
            master_directory.update(stocks)
            time.sleep(2)
            
        browser.close()
    
    with open('mc_directory_test.json', 'w') as f:
        json.dump(master_directory, f, indent=2)
    
    print(f"Saved {len(master_directory)} stocks to mc_directory_test.json")

if __name__ == "__main__":
    build_directory()
