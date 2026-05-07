import os, sys
sys.path.append(os.getcwd())
from utilities.get_active_stocks import get_supabase_client
supabase = get_supabase_client()
res = supabase.table('news').select('id', count='exact').eq('published_date', '2026-05-03').execute()
print(f"Total entries published on 2026-05-03: {res.count}")
