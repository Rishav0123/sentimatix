import os, sys
sys.path.append(os.getcwd())
from utilities.get_active_stocks import get_supabase_client
supabase = get_supabase_client()
res = supabase.table('news').select('*').order('scraped_at', desc=True).limit(50).execute()
for n in res.data:
    print(f"[{n['source']}] {n['title']} | URL: {n['url']}")
