import os
from supabase import create_client
from dotenv import load_dotenv
import pandas as pd

load_dotenv()

def analyze_null_sentiment_news():
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_KEY')
    supabase = create_client(url, key)
    
    print("Fetching news with NULL sentiment...")
    
    # We might need pagination if there are many, but let's fetch up to 10,000
    all_data = []
    limit = 1000
    offset = 0
    while True:
        res = supabase.table('news').select('id, title, url, source, published_at, scraped_at, yfin_symbol').is_('sentiment', 'null').order('published_at', desc=True).range(offset, offset + limit - 1).execute()
        if not res.data:
            break
        all_data.extend(res.data)
        if len(res.data) < limit:
            break
        offset += limit
        
    if not all_data:
        print("No articles with NULL sentiment found.")
        return
        
    df = pd.DataFrame(all_data)
    
    print(f"\nTotal articles with NULL sentiment: {len(df)}")
    
    print("\n--- Breakdown by Source ---")
    print(df['source'].value_counts())
    
    # Analyze dates
    df['published_at'] = pd.to_datetime(df['published_at'], errors='coerce')
    
    print("\n--- Breakdown by Year-Month of published_at ---")
    # Group by Year-Month
    if not df['published_at'].isnull().all():
        df['year_month'] = df['published_at'].dt.to_period('M')
        print(df['year_month'].value_counts().sort_index(ascending=False).head(20))
    
    print("\n--- Oldest Articles ---")
    oldest = df.sort_values('published_at').head(5)
    for _, row in oldest.iterrows():
        print(f"[{row['source']}] {row['published_at']} | {row['title']} | {row['url']}")
        
    print("\n--- Newest Articles ---")
    newest = df.sort_values('published_at', ascending=False).head(5)
    for _, row in newest.iterrows():
        print(f"[{row['source']}] {row['published_at']} | {row['title']} | {row['url']}")
        
    # Check if there's a specific pattern with the old dates (e.g., from a specific scraper)
    old_news = df[df['published_at'] < pd.Timestamp('2026-01-01', tz='UTC')]
    if not old_news.empty:
        print(f"\n--- Analysis of Old News (< 2026) : {len(old_news)} articles ---")
        print(old_news['source'].value_counts())

if __name__ == "__main__":
    analyze_null_sentiment_news()
