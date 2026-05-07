"""
Move Today's News (Looping): Export all news scraped on 2026-05-03 to CSV and then delete from DB.
Handles cases with >1000 entries.
"""
import os, sys, csv
sys.path.append(os.getcwd())
from utilities.get_active_stocks import get_supabase_client

def move_today_news():
    supabase = get_supabase_client()
    date_str = '2026-05-03'
    total_moved = 0
    
    filename = f"news_backup_{date_str}_full.csv"
    file_exists = os.path.isfile(filename)
    
    while True:
        # 1. Fetch a batch of news from today
        print(f"Fetching batch of news scraped on {date_str}...")
        res = supabase.table('news').select('*').gte('scraped_at', f'{date_str}T00:00:00').lt('scraped_at', '2026-05-04T00:00:00').limit(1000).execute()
        
        if not res.data:
            break
            
        # 2. Append to CSV
        mode = 'a' if file_exists else 'w'
        with open(filename, mode, newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=res.data[0].keys())
            if not file_exists:
                writer.writeheader()
                file_exists = True
            writer.writerows(res.data)
        
        # 3. Delete from DB
        ids = [x['id'] for x in res.data]
        for i in range(0, len(ids), 500):
            batch = ids[i:i+500]
            supabase.table('news').delete().in_('id', batch).execute()
            
        total_moved += len(ids)
        print(f"  Moved {len(ids)} articles in this batch. Total: {total_moved}")

    print(f"MOVE COMPLETED. Total moved: {total_moved}. Backup saved to {filename}")

if __name__ == "__main__":
    move_today_news()
