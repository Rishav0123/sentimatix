"""
Move Today's News: Export all news scraped on 2026-05-03 to CSV and then delete from DB.
"""
import os, sys, csv
sys.path.append(os.getcwd())
from utilities.get_active_stocks import get_supabase_client

def move_today_news():
    supabase = get_supabase_client()
    date_str = '2026-05-03'
    
    # 1. Fetch all news from today
    print(f"Fetching news scraped on {date_str}...")
    res = supabase.table('news').select('*').gte('scraped_at', f'{date_str}T00:00:00').lt('scraped_at', '2026-05-04T00:00:00').execute()
    
    if not res.data:
        print("No entries found for today.")
        return
        
    # 2. Save to CSV
    filename = f"news_backup_{date_str}.csv"
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=res.data[0].keys())
        writer.writeheader()
        writer.writerows(res.data)
    
    print(f"Saved {len(res.data)} entries to {filename}")
    
    # 3. Delete from DB
    ids = [x['id'] for x in res.data]
    # Delete in batches of 500
    for i in range(0, len(ids), 500):
        batch = ids[i:i+500]
        supabase.table('news').delete().in_('id', batch).execute()
        print(f"  Deleted batch {i//500 + 1}")

    print("MOVE COMPLETED.")

if __name__ == "__main__":
    move_today_news()
