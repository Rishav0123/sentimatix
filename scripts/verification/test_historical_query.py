import os
import sys
from dotenv import load_dotenv

# Add apps/api to path so we can import historical_query_engine
sys.path.insert(0, os.path.abspath("d:/sentimatix/apps/api"))

# Load environment variables
load_dotenv("d:/sentimatix/apps/api/.env")

from historical_query_engine import historical_engine

def test_query():
    print("Testing Historical Query Engine connection to Cloudflare R2...")
    print(f"S3_BUCKET_NAME: {os.getenv('S3_BUCKET_NAME')}")
    print(f"S3_ENDPOINT_URL: {os.getenv('S3_ENDPOINT_URL')}")
    
    # Query for historical news older than 60 days
    # Let's request some limit of records
    total_count, records = historical_engine.query_historical_news(
        limit=5,
        published_before="2026-03-26"
    )
    
    print(f"\nQuery results:")
    print(f"Total matching historical records found: {total_count}")
    print(f"Number of records retrieved in this page: {len(records)}")
    
    if records:
        print("\nSample records:")
        for idx, rec in enumerate(records):
            print(f"\n[{idx + 1}] ID: {rec['id']}")
            print(f"    Title: {rec['title']}")
            print(f"    Published At: {rec['published_at']}")
            print(f"    Symbol: {rec['yfin_symbol']}")
            print(f"    Sentiment: {rec['sentiment']}")
            
if __name__ == "__main__":
    test_query()
