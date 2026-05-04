"""
MoneyControl Dry Run: Scrape news for a few stocks and print results without saving to DB.
"""
import os, sys
sys.path.append(os.getcwd())
from scrapers.scrape_moneycontrol import scrape_moneycontrol_news_selenium

def dry_run():
    # Test with a stock where params might be swapped
    test_stocks = [
        {"yfin_symbol": "DRREDDY.NS", "mc_link_1": "DRL", "mc_link_2": "drreddyslaboratories"}
    ]
    
    print("Starting Dry Run (No DB update)...")
    
    for stock in test_stocks:
        print(f"\n--- Scraping {stock['yfin_symbol']} ---")
        
        link_a = stock['mc_link_1'].lower().replace(' ', '').replace('.', '')
        link_b = stock['mc_link_2'].lower().replace(' ', '').replace('.', '')
        
        if len(link_a) > len(link_b):
            company_name = link_a
            symbol = link_b
        else:
            company_name = link_b
            symbol = link_a
            
        print(f"Computed company_name: {company_name}, symbol: {symbol}")
        headlines = scrape_moneycontrol_news_selenium(company_name, symbol)
        
        if not headlines:
            print(f"No news found for {stock['yfin_symbol']}")
            continue
            
        print(f"Found {len(headlines)} headlines:")
        for i, h in enumerate(headlines[:5], 1): # Show first 5
            print(f"{i}. [{h['timestamp']}] {h['title']}")
            print(f"   URL: {h['url']}")

if __name__ == "__main__":
    dry_run()
