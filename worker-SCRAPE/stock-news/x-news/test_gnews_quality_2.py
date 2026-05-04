import os
import json
import random
import subprocess
from datetime import datetime, timezone
from dotenv import load_dotenv
from supabase import create_client

# Setup Supabase
load_dotenv('.env')
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

print("Fetching active stocks...")
all_stocks = []
page_size = 1000
offset = 0
while True:
    res = supabase.table('stocks').select('*').eq('is_active', True).range(offset, offset + page_size - 1).execute()
    if not res.data:
        break
    all_stocks.extend(res.data)
    if len(res.data) < page_size:
        break
    offset += page_size

if not all_stocks:
    print("No active stocks found.")
    exit(1)

# Exclude the previously picked 50 stocks if the old json exists
excluded_symbols = set()
old_file = "temp_50_stocks.json"
if os.path.exists(old_file):
    try:
        with open(old_file, "r") as f:
            old_stocks = json.load(f)
            for s in old_stocks:
                excluded_symbols.add(s['yfin_symbol'])
    except Exception:
        pass

available_stocks = [s for s in all_stocks if s['yfin_symbol'] not in excluded_symbols]

# Pick 50 new random stocks
random_stocks = random.sample(available_stocks, min(50, len(available_stocks)))
stock_symbols = [s['yfin_symbol'] for s in random_stocks]
print(f"Selected 50 NEW random stocks: {', '.join(stock_symbols[:10])}... and {len(stock_symbols)-10} more.")

# Save to temp JSON
temp_file = "temp_50_stocks_new.json"
with open(temp_file, "w") as f:
    json.dump(random_stocks, f)

# Run the GNews scraper
print("\nRunning GNews scraper for the new 50 stocks... (This will take a minute)")
start_time = datetime.now(timezone.utc).isoformat()

subprocess.run(["python", "scrapers/scrape_gnews.py", "--stocks-json", temp_file, "--run-id", "TEST_Q2"])

# Analyze results
print("\n--- QUALITY ANALYSIS (NEW BATCH) ---")
res = supabase.table('news').select('title,url,source,yfin_symbol,tags').gte('scraped_at', start_time).neq('source', 'moneycontrol').execute()
inserted_news = res.data

if not inserted_news:
    print("No news was inserted for these 50 stocks (Generic news was successfully filtered out!)")
else:
    print(f"Found {len(inserted_news)} highly-targeted articles inserted.")
    by_stock = {}
    for item in inserted_news:
        by_stock.setdefault(item['yfin_symbol'], []).append(item)
        
    for symbol, articles in by_stock.items():
        print(f"\n[{symbol}] - {len(articles)} articles found:")
        for a in articles:
            matched_kws = a.get('tags', [])
            safe_title = a['title'].encode('ascii', 'replace').decode()
            print(f"  -> {safe_title}")
            print(f"     (Source: {a['source']} | Matched: {matched_kws})")

if os.path.exists(temp_file):
    os.remove(temp_file)
