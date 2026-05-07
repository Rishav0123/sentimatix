"""
Divis Cleanup: Remove articles for DIVISLAB.NS that matched 'Division' or other non-stock terms.
"""
import os, sys
sys.path.append(os.getcwd())
from utilities.get_active_stocks import get_supabase_client

def divis_cleanup():
    supabase = get_supabase_client()
    
    # 1. Delete articles for DIVISLAB.NS containing 'Division' but NOT 'Divi's' (possessive) or 'Divis Lab'
    # Actually, most of them just say 'Finance Division' or 'Nagpur division'
    
    # Let's pull them first to be safe
    res = supabase.table('news').select('id, title').eq('yfin_symbol', 'DIVISLAB.NS').ilike('title', '%division%').execute()
    
    ids_to_delete = []
    for n in res.data:
        title_lower = n['title'].lower()
        # Keep if it contains real stock terms
        if "divi's" in title_lower or "divis lab" in title_lower or "laboratories" in title_lower:
            continue
        ids_to_delete.append(n['id'])
    
    if ids_to_delete:
        print(f"Deleting {len(ids_to_delete)} 'Division' junk for Divis...")
        supabase.table('news').delete().in_('id', ids_to_delete).execute()
    else:
        print("No 'Division' junk found for Divis.")

if __name__ == "__main__":
    divis_cleanup()
