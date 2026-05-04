import os, sys
sys.path.append(os.getcwd())
from utilities.get_active_stocks import get_supabase_client
supabase = get_supabase_client()
res = supabase.table('news').select('id, source, title, url, scraped_at').eq('source', 'gnews').order('scraped_at', desc=True).limit(50).execute()
for n in res.data:
    try:
        title = n['title'].encode('ascii', 'replace').decode()
        print(f"[{n['id']}] [{n['scraped_at']}] [{n['source']}] {title} | URL: {n['url']}")
    except:
        print(f"[{n['id']}] error printing")
