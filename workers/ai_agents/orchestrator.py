import os
import time
import httpx
from datetime import datetime, timedelta, timezone
from pathlib import Path
from dotenv import load_dotenv

# Load local .env from the script's directory
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

from main import run_pipeline
from distributor import distribute_content
from sentiment_engine import AMDSentimentEngine

API_URL = os.environ.get("SENTIMATIX_API_URL")
API_KEY = os.environ.get("SENTIMATIX_API_KEY")
HEADERS = {"Authorization": f"Bearer {API_KEY}"}

def get_trending_stocks(hours: int = 48) -> list:
    """Fetch stocks with the highest news volume via the API."""
    try:
        with httpx.Client(timeout=20.0) as client:
            resp = client.get(f"{API_URL}/api/v1/analytics/trending", headers=HEADERS, params={"hours": hours})
            resp.raise_for_status()
            data = resp.json().get("data", [])
            # Return list of (symbol, count)
            return [(item["symbol"], item["news_count"]) for item in data]
    except Exception as e:
        print(f"❌ Error fetching trending stocks from API: {e}")
        return []

def get_recent_runs(limit: int = 25) -> list:
    """Fetch the symbols of the last N successful agent runs via the API."""
    try:
        with httpx.Client(timeout=20.0) as client:
            resp = client.get(f"{API_URL}/api/v1/internal/history", headers=HEADERS, params={"limit": limit})
            resp.raise_for_status()
            data = resp.json().get("data", [])
            return [item["stock_symbol"] for item in data]
    except Exception as e:
        print(f"❌ Error fetching history from API: {e}")
        return []

def log_run(result: dict) -> bool:
    """Log the completion of an agent run via the API. Returns True if successful."""
    try:
        payload = {
            "stock_symbol": result["symbol"],
            "news_count": result["news_count"],
            "content": str(result["content"])
        }
        with httpx.Client(timeout=20.0) as client:
            resp = client.post(f"{API_URL}/api/v1/internal/history", headers=HEADERS, json=payload)
            resp.raise_for_status()
        print(f"🎉 Successfully logged {result['symbol']} to history via API.")
        return True
    except Exception as e:
        print(f"❌ Error logging run to API: {e}")
        return False

async def main():
    sentiment_engine = AMDSentimentEngine()
    
    print("🚀 Starting Autonomous Orchestrator (API-DRIVEN MODE)...")
    
    if not API_URL or not API_KEY:
        print("❌ Missing API_URL or API_KEY in .env")
        return

    # 1. Get trending stocks via API (FORCED TEST MODE: 1000 hours)
    trending = get_trending_stocks(hours=1000)
    if not trending:
        print("❌ No trending news found in the last 1000 hours via API.")
        return
    
    # Filter out stocks (FORCED TEST MODE: threshold = 1)
    trending = [t for t in trending if t[1] >= 1]
        
    # 2. Get recent history via API
    recent_history = get_recent_runs()
    
    # 3. Selection Loop
    selected_stock = None
    for sym, count in trending:
        if sym not in recent_history:
            selected_stock = sym
            print(f"✅ Selected '{sym}' (News Volume: {count})")
            break
        else:
            print(f"⏭️ Skipping '{sym}' (Already processed recently)")
            
    if not selected_stock:
        print("⏭️ All trending stocks have been processed recently. Stopping.")
        return
        
    # 4. ENRICHMENT: Still happens directly on MI300X DB for efficiency
    print(f"🧠 Enriching news sentiment for {selected_stock} using local Qwen model...")
    await sentiment_engine.process_stock_sentiment(selected_stock)
    
    # 5. Execute the pipeline
    try:
        result = await run_pipeline(selected_stock)
        
        # 6. Log the run via API
        if log_run(result):
            # 7. Distribute content
            distribute_content(result)
        else:
            print("⚠️ Distribution skipped because API history logging failed.")
        
    except Exception as e:
        print(f"💥 Critical error during pipeline execution: {e}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
