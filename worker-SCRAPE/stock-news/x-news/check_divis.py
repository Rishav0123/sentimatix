import os, sys
sys.path.append(os.getcwd())
from utilities.get_active_stocks import get_supabase_client
supabase = get_supabase_client()
res = supabase.table('news').select('id, title, url, source').eq('yfin_symbol', 'DIVISLAB.NS').order('scraped_at', desc=True).limit(100).execute()
print(f"Total articles for DIVISLAB.NS: {len(res.data)}")
for n in res.data:
    title = n['title'].encode('ascii', 'replace').decode()
    print(f"[{n['source']}] {title} | URL: {n['url']}")
