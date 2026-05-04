"""
Test MoneyControl scraper locally without inserting into the database.
Tests a few stocks with both correct and previously-broken URL patterns.
"""
import sys
import os
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from scrapers.scrape_moneycontrol import scrape_moneycontrol_news_selenium

# Test stocks: (mc_link_1, mc_link_2, yfin_symbol)
TEST_STOCKS = [
    ("zyduslifesciences", "chc",               "ZYDUSLIFE.NS"),   # Was broken before
    ("mahindramahindra",  "mm",                "M&M.NS"),          # Was working
    ("jindalsteel",       "jsp",               "JINDALSTEL.NS"),   # Known good
    ("godrejconsumerproducts", "gcp",          "GODREJCP.NS"),     # Was broken before
]

print("=" * 70)
print("MoneyControl Scraper Test (DRY RUN - no DB inserts)")
print("=" * 70)

for mc_link_1, mc_link_2, symbol in TEST_STOCKS:
    print(f"\n[{symbol}] Scraping: {mc_link_1} / {mc_link_2}")
    print(f"  URL: https://www.moneycontrol.com/company-article/{mc_link_1}/news/{mc_link_2}")
    
    headlines = scrape_moneycontrol_news_selenium(mc_link_1, mc_link_2)
    
    if not headlines:
        print(f"  [FAIL] No company-specific articles found (0 results after URL filter)")
    else:
        print(f"  [PASS] Found {len(headlines)} company-specific articles:")
        for i, h in enumerate(headlines[:5], 1):
            url = h.get('url', '')
            title = h.get('title', '').encode('ascii', 'replace').decode()
            # Quick sanity check
            is_company = '/company-article/' in (url or '')
            status = "OK" if is_company else "GENERIC - BUG!"
            print(f"    {i}. [{status}] {title[:80]}")
            print(f"         URL: {url[:90]}")
    
    print()

print("=" * 70)
print("Test complete.")
