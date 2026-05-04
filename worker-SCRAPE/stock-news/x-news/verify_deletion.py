import os, sys
sys.path.append(os.getcwd())
from utilities.get_active_stocks import get_supabase_client
supabase = get_supabase_client()
id_to_check = 'f17562be-f9d0-406d-8271-cdecc5245adf'
res = supabase.table('news').select('id, title').eq('id', id_to_check).execute()
if res.data:
    print(f"FOUND: {res.data[0]['title']}")
else:
    print("NOT FOUND - Deleted successfully.")
