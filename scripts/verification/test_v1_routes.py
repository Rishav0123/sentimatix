import os
import sys
import asyncio
from dotenv import load_dotenv

sys.path.insert(0, os.path.abspath("d:/sentimatix/apps/api"))
load_dotenv("d:/sentimatix/apps/api/.env")

from v1_routes import get_news

async def main():
    print("Testing get_news logic...")
    # Mock user and tier
    user = {"id": "test_user"}
    tier = "enterprise"
    
    # Query for something older to hit S3 and maybe Postgres if not archived
    # The archiver script was last run "last week", today is June 4 2026
    # So 30 days ago is May 5 2026. Data older than May 5 is in S3. Data newer than May 5 is in Postgres.
    res_cold = await get_news(
        symbols="RELIANCE",
        sectors=None,
        sentiment=None,
        published_before="2026-04-01", # Older than 30 days, should hit S3
        published_after="2026-01-01",
        only_market_sensitive=False,
        limit=5,
        page=1,
        user=user,
        tier=tier
    )
    print("\n[TEST] OLD QUERY (Hitting S3 / Cold Tier):")
    print(f"Meta found: {res_cold['meta']['found']}")
    if 'data' in res_cold and res_cold['data']:
        print(f"Fetched {len(res_cold['data'])} records.")
    
    # Query for something recent to hit Postgres
    res_hot = await get_news(
        symbols="RELIANCE",
        sectors=None,
        sentiment=None,
        published_before=None,
        published_after="2026-05-15", # Newer than 30 days, should hit Postgres
        only_market_sensitive=False,
        limit=5,
        page=1,
        user=user,
        tier=tier
    )
    print("\n[TEST] RECENT QUERY (Hitting Postgres / Hot Tier):")
    print(f"Meta found: {res_hot['meta']['found']}")
    if 'data' in res_hot and res_hot['data']:
        print(f"Fetched {len(res_hot['data'])} records.")

if __name__ == "__main__":
    asyncio.run(main())
