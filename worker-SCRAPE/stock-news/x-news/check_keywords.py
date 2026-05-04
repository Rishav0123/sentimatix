import os, sys
sys.path.append(os.getcwd())
from utilities.get_active_stocks import get_supabase_client
supabase = get_supabase_client()
res = supabase.table('stocks').select('yfin_symbol, keyword_lst').eq('yfin_symbol', 'DIVISLAB.NS').execute()
if res.data:
    print(f"Keywords for DIVISLAB.NS: {res.data[0]['keyword_lst']}")
else:
    print("Stock not found.")
