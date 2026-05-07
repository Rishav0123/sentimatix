import sys
import os
from pathlib import Path

# Add the parent directory to sys.path so we can import scrapers
sys.path.append(str(Path(__file__).parent.parent))

from scrapers.scrape_moneycontrol import scrape_moneycontrol_news_selenium

def test_validation():
    # Problematic case reported by user
    company_name = "srghflns"
    symbol = "srghfl"
    stock_name = "SRG Housing Finance"
    
    print(f"Testing validation for {company_name} ({symbol}) - {stock_name}")
    print("This should be skipped due to generic fallback title.")
    
    headlines = scrape_moneycontrol_news_selenium(company_name, symbol, stock_name)
    
    if not headlines:
        print("\nSUCCESS: Scraper correctly skipped the generic fallback page.")
    else:
        print(f"\nFAILURE: Scraper found {len(headlines)} articles which might be junk.")

if __name__ == "__main__":
    test_validation()
