import os
from dotenv import load_dotenv
from supabase import create_client
from collections import Counter

load_dotenv(r'd:\sentimatix\workers/scrape\stock-news\x-news\.env')
s = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

res = s.table('stocks').select('sector').eq('is_active', True).execute()

sectors = Counter()
for r in res.data:
    sec = r.get('sector') or 'NULL/Empty'
    sec = sec.strip() if sec else 'NULL/Empty'
    if sec == '':
        sec = 'NULL/Empty'
    sectors[sec] += 1

print(f"Total active stocks: {sum(sectors.values())}")
print(f"Distinct sectors: {len(sectors)}\n")
print(f"{'Sector':<45} {'Count':>6}")
print('-' * 53)
for sec, count in sorted(sectors.items(), key=lambda x: -x[1]):
    print(f"{sec:<45} {count:>6}")
