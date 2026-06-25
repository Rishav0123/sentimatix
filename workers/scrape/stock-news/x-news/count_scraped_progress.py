import os, sys
from datetime import datetime
sys.path.append(os.getcwd())
from utilities.get_active_stocks import get_supabase_client
supabase = get_supabase_client()
today_str = datetime.now().strftime('%Y-%m-%d')
res = supabase.table('news').select('id', count='exact').gte('scraped_at', f'{today_str}T00:00:00').execute()
print(f"Total entries scraped on {today_str}: {res.count}")
