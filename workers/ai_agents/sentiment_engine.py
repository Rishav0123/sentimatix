import os
import sys
import asyncio
import json
import httpx
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
from supabase import create_client, Client
import logging

# Ensure standard output/error streams use UTF-8 encoding to prevent UnicodeEncodeError on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

# Setup Logging
logger = logging.getLogger(__name__)

from pathlib import Path
# Load local .env from the script's directory
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

# Configuration
VLLM_BASE_URL = os.environ.get("LLM_BASE_URL", "http://localhost:11434/v1")
LLM_MODEL = os.environ.get("LLM_MODEL", "qwen2.5:7b")

# If model starts with provider prefix (like ollama/, openai/ or groq/), strip it for raw REST API request
if LLM_MODEL.startswith("ollama/"):
    LLM_MODEL = LLM_MODEL.replace("ollama/", "")
elif LLM_MODEL.startswith("openai/"):
    LLM_MODEL = LLM_MODEL.replace("openai/", "")
elif LLM_MODEL.startswith("groq/"):
    LLM_MODEL = LLM_MODEL.replace("groq/", "")

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

class AMDSentimentEngine:
    def __init__(self):
        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        headers = {}
        api_key = os.environ.get("LLM_API_KEY")
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
            
        self.client = httpx.AsyncClient(headers=headers, timeout=120.0)  # 120s for slow local Ollama inference

    async def _execute_with_retry(self, query_builder, max_retries: int = 5, initial_delay: float = 2.0, backoff_factor: float = 2.0):
        """Execute a Supabase query builder with retry logic for network and connection issues."""
        delay = initial_delay
        for attempt in range(max_retries):
            try:
                loop = asyncio.get_running_loop()
                return await loop.run_in_executor(None, query_builder.execute)
            except Exception as e:
                logger.warning(
                    f"Supabase request failed (attempt {attempt + 1}/{max_retries}). "
                    f"Error: {e}. Retrying in {delay}s..."
                )
                if attempt == max_retries - 1:
                    logger.error("Max retries reached. Failing.")
                    raise e
                await asyncio.sleep(delay)
                delay *= backoff_factor

    async def get_all_unanalyzed_news(self, limit: int = 1000):
        """Fetch news that lacks AI sentiment enrichment and is not yet marked as ready."""
        query = (
            self.supabase.table("news")
            .select("id, title, content, yfin_symbol, stock_name")
            .eq("is_ready", "N")
            .order("published_at", desc=True)
            .limit(limit)
        )
        response = await self._execute_with_retry(query)
        return response.data

    async def get_unanalyzed_news_for_stock(self, stock_symbol: str, limit: int = 50):
        """Fetch news for a specific stock that lacks AI sentiment enrichment and is not yet marked as ready."""
        since = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
        query = (
            self.supabase.table("news")
            .select("id, title, content, yfin_symbol, stock_name")
            .eq("yfin_symbol", stock_symbol)
            .eq("is_ready", "N")
            .gt("published_at", since)
            .limit(limit)
        )
        response = await self._execute_with_retry(query)
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
                query = self.supabase.table("news").update({
                    "sentiment": analysis['sentiment'],
                    "sentiment_score": analysis['score'],
                    "confidence": analysis['confidence'],
                    "is_volatile": analysis['sentiment'] == "conflicted",
                    "is_ready": "Y"
                }).eq("id", item['id'])
                await self._execute_with_retry(query)
                
            # Tiny 500ms spacing sleep to prevent hitting Groq's RPM/TPM rate limits
            await asyncio.sleep(0.5)
                
        logger.info(f"Successfully enriched sentiment for {stock_symbol}")

    async def analyze_sentiment_qwen(self, title: str, content: str, stock_name: str):
        """Call the Qwen/Groq model to analyze sentiment, featuring retry logic for rate limits."""
        text = f"Title: {title}\nContent: {content[:300]}"
        
        prompt = f"""
Analyze the financial sentiment of the following news for the stock: {stock_name}.
News: {text}

Strictly follow these criteria:
- "irrelevant": The text is a daily proverb, motivational quote, generic advice, or non-financial fluff completely unrelated to the stock or company.
- "positive": Strong positive indicators like surging profits, major successful acquisitions, significant analyst upgrades, or blockbuster earnings.
- "negative": Clear negative indicators like declining profits, management turnover, lawsuits, missing estimates, high inflation impacts, or analyst downgrades (not just the word "sell").
- "neutral": Routine corporate filings, scheduling of AGMs, granting of ESOPs, appointment of regular executives, or purely factual market updates without strong positive/negative implications.
- "conflicted": Contains both strong positive and strong negative news about the stock.

Return JSON: {{"sentiment": "positive"|"negative"|"neutral"|"conflicted"|"irrelevant", "score": float, "confidence": float}}
"""
        
        payload = {
            "model": LLM_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,
            "response_format": { "type": "json_object" }
        }

        max_retries = 5
        backoff_factor = 2
        delay = 2.0  # Initial delay in seconds

        for attempt in range(max_retries):
            try:
                response = await self.client.post(f"{VLLM_BASE_URL}/chat/completions", json=payload)
                
                # Check explicitly for 429 rate limit
                if response.status_code == 429:
                    logger.warning(f"Rate limited (429) by Groq on attempt {attempt+1}/{max_retries}. Backing off for {delay}s...")
                    await asyncio.sleep(delay)
                    delay *= backoff_factor
                    continue
                
                response.raise_for_status()
                raw_content = response.json()['choices'][0]['message']['content']
                return json.loads(raw_content)
                
            except Exception as e:
                err_msg = str(e) or repr(e)  # httpx.ReadTimeout etc. have empty str()
                logger.error(f"Attempt {attempt+1}/{max_retries} failed for '{title[:30]}': [{type(e).__name__}] {err_msg}")
                if attempt == max_retries - 1:
                    return None
                await asyncio.sleep(delay)
                delay *= backoff_factor
                
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
                query = self.supabase.table("news").update({
                    "sentiment": analysis['sentiment'],
                    "sentiment_score": analysis['score'],
                    "confidence": analysis['confidence'],
                    "is_volatile": analysis['sentiment'] == "conflicted",
                    "is_ready": "Y"
                }).eq("id", item['id'])
                await self._execute_with_retry(query)
                print(f"✅ Analyzed: {item['title'][:50]}... -> {analysis['sentiment']}")
                
            # Tiny 500ms spacing sleep to prevent hitting Groq's RPM/TPM rate limits
            await asyncio.sleep(0.5)

async def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
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
