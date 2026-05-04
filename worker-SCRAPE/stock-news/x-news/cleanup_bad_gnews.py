import os
from dotenv import load_dotenv
from supabase import create_client
from datetime import datetime, timezone

load_dotenv('.env')
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

print("Cleaning up junk news entries...")

# Time of the bad scraper run (approximately before 16:50:00 UTC today)
bad_run_cutoff = '2026-05-04T16:50:00+00:00'
start_of_day = '2026-05-04T00:00:00+00:00'

# First count how many we are going to delete
res_count = supabase.table('news') \
    .select('id', count='exact') \
    .gte('scraped_at', start_of_day) \
    .lte('scraped_at', bad_run_cutoff) \
    .neq('source', 'moneycontrol') \
    .execute()

count = res_count.count if res_count.count else len(res_count.data)
print(f"Found {count} junk entries to delete.")

if count > 0:
    res = supabase.table('news') \
        .delete() \
        .gte('scraped_at', start_of_day) \
        .lte('scraped_at', bad_run_cutoff) \
        .neq('source', 'moneycontrol') \
        .execute()
    
    print(f"Successfully deleted {len(res.data)} junk articles.")
else:
    print("Nothing to delete.")
