import os
import sys
import asyncio
from collections import Counter
from dotenv import load_dotenv

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
from supabase import create_client, Client
from pathlib import Path

# Load local .env from the script's directory
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

async def analyze_quality():
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    print("Fetching last 1000 analyzed news articles...")
    response = supabase.table("news").select("id, title, sentiment, is_ready").eq("is_ready", "Y").order("published_at", desc=True).limit(1000).execute()
    
    data = response.data
    print(f"Retrieved {len(data)} articles.")
    
    if not data:
        return
        
    sentiments = [item['sentiment'] for item in data if item.get('sentiment')]
    counts = Counter(sentiments)
    
    print("\n--- Sentiment Distribution ---")
    total = len(sentiments)
    for sentiment, count in counts.most_common():
        percentage = (count / total) * 100
        print(f"{sentiment}: {count} ({percentage:.2f}%)")
        
    print("\n--- Sample Articles ---")
    for sentiment_type in counts.keys():
        print(f"\n[ Sample {sentiment_type.upper()} Articles ]")
        samples = [item['title'] for item in data if item.get('sentiment') == sentiment_type][:3]
        for s in samples:
            print(f"- {s}")

if __name__ == "__main__":
    asyncio.run(analyze_quality())
