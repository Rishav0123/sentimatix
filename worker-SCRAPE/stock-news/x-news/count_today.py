import os, sys
sys.path.append(os.getcwd())
from utilities.get_active_stocks import get_supabase_client
supabase = get_supabase_client()
# Check count for today
res = supabase.table('news').select('id', count='exact').gte('scraped_at', '2026-05-03T00:00:00').lt('scraped_at', '2026-05-04T00:00:00').execute()
print(f"Total entries scraped on 2026-05-03: {res.count}")
