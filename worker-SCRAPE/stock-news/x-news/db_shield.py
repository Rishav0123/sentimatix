"""
DB Shield: Continuously delete junk news for the next 5 minutes.
Use this to keep the DB clean while the source is being killed.
"""
import os, sys, time
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

def run_shield(duration_minutes=5):
    supabase = get_supabase_client()
    end_time = time.time() + (duration_minutes * 60)
    
    print(f"Shield ACTIVE for {duration_minutes} minutes...")
    
    while time.time() < end_time:
        total_deleted = 0
        
        # Delete by paths
        for path in GENERIC_PATHS:
            res = supabase.table('news').delete().eq('source', 'moneycontrol').ilike('url', f'%{path}%').execute()
            # We don't get count easily but it's fine
            
        # Delete by keywords
        for kw in GENERIC_KEYWORDS:
            res = supabase.table('news').delete().eq('source', 'moneycontrol').ilike('title', f'%{kw}%').execute()
            
        print(f"[{time.strftime('%H:%M:%S')}] Cleanup pulse completed.")
        time.sleep(10) # Pulse every 10 seconds

if __name__ == "__main__":
    run_shield()
