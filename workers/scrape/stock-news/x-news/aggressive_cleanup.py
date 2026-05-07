"""
Aggressive Cleanup: Delete all MoneyControl news that match generic patterns.
"""
import os, sys
sys.path.append(os.getcwd())
from utilities.get_active_stocks import get_supabase_client

GENERIC_PATHS = [
    'entertainment', 'sports', 'world', 'education', 
    'news/trends', 'news/india', 'automobile', 'technology'
]

GENERIC_KEYWORDS = [
    'actor', 'movie', 'film', 'series', 'bollywood', 'hollywood', 'met gala', 
    'harry potter', 'voldemort', 'shakira', 'rahul roy', 'janhvi kapoor', 
    'rashmika mandanna', 'ipl', 'cricket', 'score', 'match', 'toss', 'auction', 
    't20', 'arjun tendulkar', 'rovman powell', 'sunil narine', 'election', 
    'poll', 'votes', 'bjp', 'tmc', 'akhilesh yadav', 'pinarayi vijayan', 
    'bengal assembly', 'tamil nadu assembly', 'viral', 'techie', 'marriage', 
    'noida high-rise', 'buckets', 'slum', 'space station', 'nasa', 'dinosaurs', 
    'hajj', 'neet exam', 'physics tough', 'succession', 'cost cuts',
    'pakistan army', 'donald trump', 'nick stewart', 'khawaja asif', 'air india'
]

def aggressive_cleanup():
    supabase = get_supabase_client()
    
    # 1. Delete by URL patterns
    for path in GENERIC_PATHS:
        print(f"Checking URL path: {path}")
        res = supabase.table('news').delete().eq('source', 'moneycontrol').ilike('url', f'%/{path}/%').execute()
        # Note: some supabase-py versions might not return count directly on delete
        print(f"  Finished path {path}")

    # 2. Delete by Title keywords
    for kw in GENERIC_KEYWORDS:
        print(f"Checking Title keyword: {kw}")
        res = supabase.table('news').delete().eq('source', 'moneycontrol').ilike('title', f'%{kw}%').execute()
        print(f"  Finished keyword {kw}")

if __name__ == "__main__":
    aggressive_cleanup()
