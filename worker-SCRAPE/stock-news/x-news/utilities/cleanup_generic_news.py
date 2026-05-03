"""
Cleanup: Remove clearly generic/non-financial MoneyControl articles from the database.
Generic articles come from these URL paths when the scraper hit wrong URLs:
  /entertainment/, /sports/, /world/, /education/, /news/trends/, /news/india/
"""
import os
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from utilities.get_active_stocks import get_supabase_client

GENERIC_PATHS = [
    '/entertainment/',
    '/sports/',
    '/world/',
    '/education/',
    '/news/trends/',
    '/news/india/',
    '/automobile/',   # generic car sales news not tied to a stock
    '/technology/',   # generic tech product news (Samsung updates etc.)
]

def cleanup_generic_news():
    supabase = get_supabase_client()
    total_deleted = 0

    for path in GENERIC_PATHS:
        while True:
            res = (
                supabase.table('news')
                .select('id, url')
                .eq('source', 'moneycontrol')
                .ilike('url', f'%{path}%')
                .limit(1000)
                .execute()
            )
            if not res.data:
                break

            ids = [n['id'] for n in res.data]
            print(f"[{path}] Deleting {len(ids)} articles...")
            for i in range(0, len(ids), 100):
                supabase.table('news').delete().in_('id', ids[i:i+100]).execute()
                total_deleted += len(ids[i:i+100])

    print(f"\nTotal deleted: {total_deleted}")

    # Final count
    remaining = supabase.table('news').select('id', count='exact').eq('source', 'moneycontrol').execute()
    print(f"Remaining moneycontrol articles: {remaining.count}")

if __name__ == "__main__":
    cleanup_generic_news()
