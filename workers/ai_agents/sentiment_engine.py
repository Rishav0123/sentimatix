import os
import asyncio
import json
import httpx
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
from supabase import create_client, Client
import logging

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

# Configuration
VLLM_BASE_URL = "http://localhost:8000/v1" # Running on the same MI300X instance
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

class AMDSentimentEngine:
    def __init__(self):
        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        self.client = httpx.AsyncClient(timeout=30.0)

    async def get_all_unanalyzed_news(self, limit: int = 1000):
        """Fetch news that lacks AI sentiment enrichment and is not yet marked as ready."""
        response = (
            self.supabase.table("news")
            .select("id, title, content, yfin_symbol, stock_name")
            .eq("is_ready", "N")
            .order("published_at", desc=True)
            .limit(limit)
            .execute()
        )
        return response.data

    async def get_unanalyzed_news_for_stock(self, stock_symbol: str, limit: int = 50):
        """Fetch news for a specific stock that lacks AI sentiment enrichment and is not yet marked as ready."""
        since = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
        response = (
            self.supabase.table("news")
            .select("id, title, content, yfin_symbol, stock_name")
            .eq("yfin_symbol", stock_symbol)
            .eq("is_ready", "N")
            .gt("published_at", since)
            .limit(limit)
            .execute()
        )
        return response.data

    async def process_stock_sentiment(self, stock_symbol: str):
        """Batch process sentiment for a stock on the MI300X."""
        news_items = await self.get_unanalyzed_news_for_stock(stock_symbol)
        if not news_items:
            logger.info(f"No unanalyzed news for {stock_symbol}")
            return
            
        logger.info(f"Analyzing {len(news_items)} articles for {stock_symbol} on AMD MI300X...")
        
        for item in news_items:
            stock_name = item.get('stock_name') or stock_symbol
            analysis = await self.analyze_sentiment_qwen(item['title'], item.get('content', ''), stock_name)
            
            if analysis:
                self.supabase.table("news").update({
                    "sentiment": analysis['sentiment'],
                    "sentiment_score": analysis['score'],
                    "confidence": analysis['confidence'],
                    "is_volatile": analysis['sentiment'] == "conflicted",
                    "is_ready": "Y"
                }).eq("id", item['id']).execute()
                
        logger.info(f"Successfully enriched sentiment for {stock_symbol}")

    async def analyze_sentiment_qwen(self, title: str, content: str, stock_name: str):
        """Call the local Qwen 2.5 7B model to analyze sentiment."""
        text = f"Title: {title}\nContent: {content[:300]}"
        
        prompt = f"""
Determine the financial sentiment for {stock_name}.
News: {text}

Return JSON: {{"sentiment": "positive"|"negative"|"neutral"|"conflicted", "score": float, "confidence": float}}
"""
        
        payload = {
            "model": "Qwen/Qwen2.5-7B-Instruct",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,
            "response_format": { "type": "json_object" }
        }

        try:
            response = await self.client.post(f"{VLLM_BASE_URL}/chat/completions", json=payload)
            response.raise_for_status()
            raw_content = response.json()['choices'][0]['message']['content']
            return json.loads(raw_content)
        except Exception as e:
            logger.error(f"Qwen Error: {e}")
            return None

    async def process_all_unanalyzed(self, batch_limit: int = 500):
        """Process all news in the database missing sentiment."""
        news_items = await self.get_all_unanalyzed_news(limit=batch_limit)
        if not news_items:
            logger.info("Database is clean. No news missing sentiment.")
            return

        logger.info(f"🚀 Starting GLOBAL Sentiment Enrichment for {len(news_items)} articles...")
        
        for item in news_items:
            stock_name = item.get('stock_name') or item.get('yfin_symbol', 'Unknown Stock')
            analysis = await self.analyze_sentiment_qwen(item['title'], item.get('content', ''), stock_name)
            
            if analysis:
                self.supabase.table("news").update({
                    "sentiment": analysis['sentiment'],
                    "sentiment_score": analysis['score'],
                    "confidence": analysis['confidence'],
                    "is_volatile": analysis['sentiment'] == "conflicted",
                    "is_ready": "Y"
                }).eq("id", item['id']).execute()
                print(f"✅ Analyzed: {item['title'][:50]}... -> {analysis['sentiment']}")

async def main():
    import sys
    engine = AMDSentimentEngine()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--global":
        await engine.process_all_unanalyzed()
    elif len(sys.argv) > 1:
        await engine.process_stock_sentiment(sys.argv[1])
    else:
        print("Usage: python3 sentiment_engine.py [--global | STOCK_SYMBOL]")

if __name__ == "__main__":
    asyncio.run(main())
