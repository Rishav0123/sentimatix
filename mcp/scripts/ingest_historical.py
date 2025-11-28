"""
Ingest Historical News into Vector Database

This script:
1. Fetches news from your /api/news endpoint
2. Generates embeddings for each article
3. Stores embeddings in Supabase vector database

Run this once to populate historical data, then run periodically to update.
"""

import requests
import logging
from datetime import datetime, timedelta
from pathlib import Path
import time
import sys

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from rag.embeddings import generate_embedding, prepare_text_for_embedding
from rag.vectordb import get_vector_db
from server.config import BACKEND_API_URL, BACKEND_API_KEY

# Setup logging
log_dir = Path(__file__).parent.parent / "logs"
log_dir.mkdir(exist_ok=True)
log_file = log_dir / f"ingestion_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def fetch_all_news(limit: int = 5000, symbol: str | None = None, start_date: str | None = None, end_date: str | None = None, max_pages: int = 1) -> list:
    """Fetch news articles with optional symbol/date filtering and basic pagination (client-side date filter)."""
    try:
        url = f"{BACKEND_API_URL}/news"
        params = {"limit": limit, "page": 1}
        if symbol:
            params["stock_symbol"] = symbol
        # If backend supports server-side date filtering, pass through to reduce payload
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        headers = {}
        if BACKEND_API_KEY:
            headers["Authorization"] = f"Bearer {BACKEND_API_KEY}"

        logger.info(f"Fetching news from {url} (limit={limit}, symbol={symbol}, start={start_date}, end={end_date})...")
        news_items = []
        page = 1
        while page <= max_pages:
            params["page"] = page
            response = requests.get(url, params=params, headers=headers, timeout=45)
            response.raise_for_status()
            data = response.json()
            batch = data.get("data", [])
            if not batch:
                break
            news_items.extend(batch)
            if len(batch) < limit:
                break
            page += 1

        # Client-side date filter if provided
        if start_date or end_date:
            filtered = []
            for item in news_items:
                pub = item.get("published_at", "")[:10]
                if start_date and pub < start_date:
                    continue
                if end_date and pub > end_date:
                    continue
                filtered.append(item)
            logger.info(f"Date filtering reduced {len(news_items)} → {len(filtered)} items")
            news_items = filtered

        logger.info(f"✅ Fetched {len(news_items)} news articles")
        return news_items

    except Exception as e:
        logger.error(f"❌ Error fetching news: {e}")
        return []


def ingest_news_item(news_item: dict, vector_db, aliases: list[str] | None = None) -> bool:
    """Generate embedding and store for a single news item"""
    try:
        news_id = news_item.get("id")
        if not news_id:
            logger.warning("Skipping news item without ID")
            return False
        
        # Check if already exists
        if vector_db.check_exists(news_id):
            logger.debug(f"Skipping {news_id} - already exists")
            return False
        
        # Prepare text for embedding
        title = news_item.get("title", "")
        content = news_item.get("content", "")
        
        if not title:
            logger.warning(f"Skipping {news_id} - no title")
            return False
        
        entities = []
        sym = news_item.get("stock_symbol", "")
        if sym:
            entities.append(sym)
        if aliases:
            entities.extend([a for a in aliases if a])
        text = prepare_text_for_embedding(
            title=title,
            content=content,
            summary=content[:500] if content else "",
            entities=entities or None
        )
        
        # Generate embedding
        embedding = generate_embedding(text)
        
        # Prepare metadata
        metadata = {
            "symbol": news_item.get("stock_symbol", ""),
            "title": title,
            "published_at": news_item.get("published_at"),
            "sentiment": news_item.get("sentiment"),
            "sentiment_score": news_item.get("impact_score", 0.0),
            "source": news_item.get("source", ""),
            "url": news_item.get("url", ""),
            "content_preview": content[:500] if content else title
        }
        
        # Insert into vector DB
        success = vector_db.insert_embedding(news_id, embedding, metadata)
        
        if success:
            logger.info(f"✅ Ingested: {news_id} - {title[:50]}...")
            return True
        else:
            logger.warning(f"❌ Failed to ingest: {news_id}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error ingesting news item {news_item.get('id', 'unknown')}: {e}")
        return False


def main():
    """Main ingestion process with CLI args for targeted backfill."""
    import argparse
    parser = argparse.ArgumentParser(description="Ingest historical news into vector DB")
    parser.add_argument("--symbol", type=str, help="Restrict ingestion to a single symbol (e.g., HDFCBANK)", required=False)
    parser.add_argument("--start-date", type=str, help="Filter start date YYYY-MM-DD", required=False)
    parser.add_argument("--end-date", type=str, help="Filter end date YYYY-MM-DD", required=False)
    parser.add_argument("--limit", type=int, default=1000, help="Max news items to fetch per page (default 1000)")
    parser.add_argument("--max-pages", type=int, default=1, help="Number of pages to fetch (default 1)")
    parser.add_argument("--batch-sleep", type=float, default=2.0, help="Sleep seconds after each 50 items (rate limiting)")
    parser.add_argument("--keywords", type=str, default="", help="Comma-separated keyword filters to include (title/content contains)")
    parser.add_argument("--aliases", type=str, default="", help="Comma-separated aliases/company names to tag and include (e.g., 'HDFC Bank,HDFC')")
    args = parser.parse_args()

    logger.info("=" * 80)
    logger.info("STARTING HISTORICAL NEWS INGESTION")
    logger.info(f"Args: symbol={args.symbol} start={args.start_date} end={args.end_date} limit={args.limit}")
    logger.info("=" * 80)

    start_time = time.time()

    # Validate date order
    if args.start_date and args.end_date:
        try:
            if datetime.fromisoformat(args.start_date) > datetime.fromisoformat(args.end_date):
                logger.error("Start date is after end date; aborting.")
                return
        except ValueError:
            logger.error("Invalid date format provided; use YYYY-MM-DD.")
            return

    # Initialize vector DB
    try:
        vector_db = get_vector_db()
        logger.info("✅ Connected to vector database")
    except Exception as e:
        logger.error(f"❌ Failed to connect to vector database: {e}")
        return

    # Fetch news with filters
    news_items = fetch_all_news(limit=args.limit, symbol=args.symbol, start_date=args.start_date, end_date=args.end_date, max_pages=args.max_pages)
    if not news_items:
        logger.error("❌ No news items fetched. Exiting.")
        return

    logger.info(f"📰 Processing {len(news_items)} news articles...")

    success_count = 0
    skip_count = 0
    error_count = 0

    # Build optional filters
    keyword_list = [k.strip() for k in (args.keywords or "").split(",") if k.strip()]
    alias_list = [a.strip() for a in (args.aliases or "").split(",") if a.strip()]

    for i, news_item in enumerate(news_items, 1):
        try:
            # Client-side include filter: keywords/aliases in title/content/symbol
            if keyword_list or alias_list:
                haystack = " ".join([
                    str(news_item.get("title", "")),
                    str(news_item.get("content", "")),
                    str(news_item.get("stock_symbol", ""))
                ]).lower()
                include = False
                for k in keyword_list:
                    if k.lower() in haystack:
                        include = True
                        break
                if not include and alias_list:
                    for a in alias_list:
                        if a.lower() in haystack:
                            include = True
                            break
                if not include:
                    skip_count += 1
                    continue

            if ingest_news_item(news_item, vector_db, aliases=alias_list):
                success_count += 1
            else:
                skip_count += 1

            if i % 10 == 0:
                logger.info(f"Progress: {i}/{len(news_items)} (ingested={success_count}, skipped={skip_count}, errors={error_count})")

            if i % 50 == 0:
                logger.info("Pausing for rate limit...")
                time.sleep(args.batch_sleep)

        except Exception as e:
            logger.error(f"Error processing item {i}: {e}")
            error_count += 1

    elapsed = time.time() - start_time

    logger.info("=" * 80)
    logger.info("INGESTION COMPLETE")
    logger.info("=" * 80)
    logger.info(f"Total items processed: {len(news_items)}")
    logger.info(f"✅ Successfully ingested: {success_count}")
    logger.info(f"⏭️  Skipped (already exists / filtered): {skip_count}")
    logger.info(f"❌ Errors: {error_count}")
    logger.info(f"⏱️  Time elapsed: {elapsed:.2f} seconds")
    if elapsed > 0:
        logger.info(f"📊 Rate: {len(news_items) / elapsed:.2f} items/second raw")
    logger.info("=" * 80)

    try:
        stats = vector_db.get_stats()
        logger.info(f"📈 Vector DB Stats: {stats}")
    except Exception as e:
        logger.error(f"Error getting stats: {e}")


if __name__ == "__main__":
    main()
