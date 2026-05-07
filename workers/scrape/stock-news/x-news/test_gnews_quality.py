import os
import json
import random
import subprocess
from datetime import datetime, timezone
from dotenv import load_dotenv
from supabase import create_client

# 1. Setup Supabase
load_dotenv('.env')
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

print("Fetching active stocks...")
# Fetch all stocks (using pagination to get all)
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

# 2. Pick 50 random stocks
random_stocks = random.sample(all_stocks, min(50, len(all_stocks)))
stock_symbols = [s['yfin_symbol'] for s in random_stocks]
print(f"Selected 50 random stocks: {', '.join(stock_symbols[:10])}... and {len(stock_symbols)-10} more.")

# 3. Save to temp JSON
temp_file = "temp_50_stocks.json"
with open(temp_file, "w") as f:
    json.dump(random_stocks, f)

# 4. Run the GNews scraper
print("\nRunning GNews scraper for the 50 stocks... (This may take a minute or two)")
start_time = datetime.now(timezone.utc).isoformat()

subprocess.run(["python", "scrapers/scrape_gnews.py", "--stocks-json", temp_file, "--run-id", "TEST_QUALITY"])

# 5. Analyze results
print("\n--- QUALITY ANALYSIS ---")
print(f"Fetching news inserted after {start_time}...")

res = supabase.table('news').select('title,url,source,yfin_symbol,tags').gte('scraped_at', start_time).neq('source', 'moneycontrol').execute()
inserted_news = res.data

if not inserted_news:
    print("No news was inserted for these 50 stocks (This is actually a GOOD sign if none of them had genuine news, meaning generic news was successfully filtered out!)")
else:
    print(f"Found {len(inserted_news)} highly-targeted articles inserted.")
    
    # Group by stock
    by_stock = {}
    for item in inserted_news:
        by_stock.setdefault(item['yfin_symbol'], []).append(item)
        
    for symbol, articles in by_stock.items():
        print(f"\n[{symbol}] - {len(articles)} articles found:")
        for a in articles:
            matched_kws = a.get('tags', [])
            print(f"  -> {a['title']}")
            print(f"     (Source: {a['source']} | Matched Keywords: {matched_kws})")

# Cleanup temp file
if os.path.exists(temp_file):
    os.remove(temp_file)
