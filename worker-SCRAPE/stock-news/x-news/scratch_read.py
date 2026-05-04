import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv('.env')
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

start_time = '2026-05-04T16:56:44'
res = supabase.table('news').select('title,source,yfin_symbol,tags').gte('scraped_at', start_time).neq('source', 'moneycontrol').execute()

by_stock = {}
for item in res.data:
    by_stock.setdefault(item['yfin_symbol'], []).append(item)

for symbol, articles in by_stock.items():
    print(f"\n[{symbol}] - {len(articles)} articles found:")
    for a in articles:
        # Avoid Windows UnicodeEncodeError for rupees symbol
        safe_title = a['title'].encode('ascii', 'replace').decode()
        print(f"  -> {safe_title}")
        print(f"     (Source: {a['source']} | Matched: {a.get('tags')})")
