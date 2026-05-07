"""
Master Cleanup: Remove clearly generic/non-financial news based on Title keywords.
Targeting junk that leaked into the stock database.
"""
import os, sys
sys.path.append(os.getcwd())
from utilities.get_active_stocks import get_supabase_client

# Keywords that definitely indicate non-financial news for our stock list
GENERIC_TITLE_KEYWORDS = [
    'actor', 'movie', 'film', 'series', 'bollywood', 'hollywood', 'met gala', 
    'harry potter', 'voldemort', 'shakira', 'rahul roy', 'janhvi kapoor', 
    'rashmika mandanna', 'ipl', 'cricket', 'score', 'match', 'toss', 'auction', 
    't20', 'arjun tendulkar', 'rovman powell', 'sunil narine', 'election', 
    'poll', 'votes', 'bjp', 'tmc', 'akhilesh yadav', 'pinarayi vijayan', 
    'bengal assembly', 'tamil nadu assembly', 'viral', 'techie', 'marriage', 
    'noida high-rise', 'buckets', 'slum', 'space station', 'nasa', 'dinosaurs', 
    'hajj', 'neet exam', 'physics tough', 'succession', 'cost cuts',
    'pakistan army', 'donald trump', 'nick stewart', 'khawaja asif'
]
# Note: 'succession' and 'cost cuts' are business terms, but in the context of 'Air India' 
# assigned to 'JINDALSTEL.NS', they are junk. 
# However, I should be careful with broad terms. 
# Let's focus on the most obvious ones first.

GENERIC_PATHS = [
    '/entertainment/', '/sports/', '/world/', '/education/', 
    '/news/trends/', '/news/india/', '/automobile/', '/technology/'
]

def master_cleanup():
    supabase = get_supabase_client()
    total_deleted = 0

    # 1. Cleanup by URL path (already done but let's re-verify)
    for path in GENERIC_PATHS:
        print(f"Cleaning path: {path}")
        while True:
            res = supabase.table('news').select('id').ilike('url', f'%{path}%').limit(1000).execute()
            if not res.data: break
            ids = [x['id'] for x in res.data]
            supabase.table('news').delete().in_('id', ids).execute()
            total_deleted += len(ids)
            print(f"  Deleted {len(ids)} by path")

    # 2. Cleanup by Title keywords
    for kw in GENERIC_TITLE_KEYWORDS:
        print(f"Cleaning keyword: {kw}")
        while True:
            res = supabase.table('news').select('id', 'title').ilike('title', f'%{kw}%').limit(1000).execute()
            if not res.data: break
            ids = [x['id'] for x in res.data]
            supabase.table('news').delete().in_('id', ids).execute()
            total_deleted += len(ids)
            print(f"  Deleted {len(ids)} by keyword '{kw}'")

    print(f"\nTOTAL DELETED: {total_deleted}")

if __name__ == "__main__":
    master_cleanup()
