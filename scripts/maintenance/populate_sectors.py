import os
import json
import time
import yfinance as yf
from dotenv import load_dotenv
from supabase import create_client
from collections import Counter

load_dotenv(r'd:\sentimatix\workers/scrape\stock-news\x-news\.env')
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

# Fetch all active stocks
print("Fetching active stocks...")
all_stocks = []
offset = 0
while True:
    res = supabase.table('stocks').select('id,yfin_symbol,sector').eq('is_active', True).range(offset, offset + 999).execute()
    if not res.data: break
    all_stocks.extend(res.data)
    if len(res.data) < 1000: break
    offset += 1000

print(f"Total active stocks: {len(all_stocks)}")

# Only update stocks that are Unknown/null/empty
to_update = [s for s in all_stocks if not s.get('sector') or s['sector'].strip() in ('', 'Unknown', 'NULL/Empty')]
print(f"Stocks needing sector update: {len(to_update)}\n")

BATCH_SIZE = 50
updated = 0
failed = 0
sector_counts = Counter()

for i in range(0, len(to_update), BATCH_SIZE):
    batch = to_update[i:i + BATCH_SIZE]
    symbols = [s['yfin_symbol'] for s in batch]
    batch_str = " ".join(symbols)

    print(f"Processing batch {i//BATCH_SIZE + 1}/{(len(to_update) + BATCH_SIZE - 1)//BATCH_SIZE} | symbols {i+1}-{min(i+BATCH_SIZE, len(to_update))}")

    try:
        tickers = yf.Tickers(batch_str)

        for stock in batch:
            sym = stock['yfin_symbol']
            try:
                info = tickers.tickers[sym].info
                sector = info.get('sector') or info.get('industry') or None

                if sector:
                    supabase.table('stocks').update({'sector': sector}).eq('id', stock['id']).execute()
                    sector_counts[sector] += 1
                    updated += 1
                else:
                    failed += 1
            except Exception as e:
                failed += 1

    except Exception as e:
        print(f"  Batch error: {e}")
        failed += len(batch)

    # Small delay to avoid rate limiting
    time.sleep(0.5)

print(f"\n{'='*50}")
print(f"Done!")
print(f"  Updated: {updated}")
print(f"  No data found: {failed}")
print(f"\nSector breakdown of newly updated stocks:")
for sec, count in sorted(sector_counts.items(), key=lambda x: -x[1]):
    print(f"  {sec:<45} {count:>5}")
