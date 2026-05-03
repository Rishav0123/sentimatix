import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv('d:/sentimatix/worker-SCRAPE/stock-news/x-news/.env')
url = os.environ.get('SUPABASE_URL')
key = os.environ.get('SUPABASE_KEY')
supabase = create_client(url, key)

all_data = []
offset = 0
limit = 1000

print("Fetching stocks from database...")
while True:
    res = supabase.table('stocks').select('yfin_symbol,mc_link_1').range(offset, offset + limit - 1).execute()
    all_data.extend(res.data)
    if len(res.data) < limit:
        break
    offset += limit

total = len(all_data)
placeholders = [x for x in all_data if x['mc_link_1'] == x['yfin_symbol']]
valid = total - len(placeholders)

print(f"\nDatabase Summary:")
print(f"Total stocks: {total}")
print(f"Stocks with valid MC links: {valid}")
print(f"Stocks with placeholders (MC1 = Symbol): {len(placeholders)}")
print(f"Coverage: {(valid/total)*100:.2f}%")
