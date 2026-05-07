import os, sys
sys.path.append(os.getcwd())
from utilities.get_active_stocks import get_supabase_client
supabase = get_supabase_client()
res = supabase.table('news').select('*').limit(1).execute()
if res.data:
    print(f"Columns in 'news' table: {list(res.data[0].keys())}")
else:
    print("No data in 'news' table.")
