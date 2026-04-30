"""
Sentiment Backfill Runner
=========================
Fills missing sentiment_score, confidence, is_volatile for all news articles.
Also re-scores articles that have sentiment_score but are missing confidence
(scored before Phase 1 upgrade).

Designed for large-scale backfill (50k+ articles).
Runs in batches of BATCH_SIZE to avoid memory and timeout issues.

Usage:
    python backfill_sentiment.py              # Fill missing sentiment only
    python backfill_sentiment.py --rescore    # Also rescore old articles missing confidence
    python backfill_sentiment.py --limit 500  # Process only N articles (for testing)
"""

import sys
import os
import time
import asyncio
import argparse
from datetime import datetime

# Add NLP path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "worker-NLP", "stock-news", "nlp"))

import psycopg2
import psycopg2.extras

DB_PARAMS = {
    "host": "aws-1-ap-southeast-2.pooler.supabase.com",
    "port": 5432,
    "database": "postgres",
    "user": "postgres.hdsntducurmhossannue",
    "password": "Wallposter27@"
}

BATCH_SIZE   = 50      # Articles per batch (adjust based on your RAM / speed)
SLEEP_SECS   = 0.1    # Brief pause between batches to avoid rate limits


def get_conn():
    return psycopg2.connect(**DB_PARAMS)


def fetch_batch(cur, mode: str, offset: int, limit: int):
    """Fetch a batch of articles that need processing."""
    if mode == "missing":
        # Articles with no sentiment at all
        cur.execute("""
            SELECT id, title, content, stock_name, yfin_symbol
            FROM public.news
            WHERE sentiment_score IS NULL
            ORDER BY published_at DESC
            LIMIT %s OFFSET %s;
        """, (limit, offset))
    else:
        # Articles with old sentiment but missing confidence (Phase 1 upgrade)
        cur.execute("""
            SELECT id, title, content, stock_name, yfin_symbol
            FROM public.news
            WHERE sentiment_score IS NOT NULL
              AND confidence IS NULL
            ORDER BY published_at DESC
            LIMIT %s OFFSET %s;
        """, (limit, offset))
    return cur.fetchall()


def update_article(cur, article_id: str, result: dict):
    cur.execute("""
        UPDATE public.news
        SET sentiment       = %s,
            sentiment_score = %s,
            confidence      = %s,
            is_volatile     = %s
        WHERE id = %s;
    """, (
        result["sentiment"],
        result["sentiment_score"],
        result.get("confidence"),
        result.get("is_volatile", False),
        article_id
    ))


def run(args):
    from analyze_sentiment_production import ProductionSentimentAnalyzer

    print(f"[{datetime.now():%Y-%m-%d %H:%M}] Loading FinBERT model...")
    analyzer = ProductionSentimentAnalyzer()
    print("Model ready.\n")

    conn = get_conn()
    conn.autocommit = True
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    modes = ["missing"]
    if args.rescore:
        modes.append("rescore")

    for mode in modes:
        # Count total for this mode
        if mode == "missing":
            cur.execute("SELECT COUNT(*) FROM public.news WHERE sentiment_score IS NULL;")
            label = "Missing sentiment"
        else:
            cur.execute("SELECT COUNT(*) FROM public.news WHERE sentiment_score IS NOT NULL AND confidence IS NULL;")
            label = "Re-scoring (upgrade confidence)"

        total = cur.fetchone()[0]
        if args.limit:
            total = min(total, args.limit)

        print(f"=== {label}: {total:,} articles ===\n")

        processed = 0
        success   = 0
        failed    = 0
        start     = time.time()

        while processed < total:
            batch = fetch_batch(cur, mode, processed, min(BATCH_SIZE, total - processed))
            if not batch:
                break

            for row in batch:
                article_id  = row["id"]
                title       = row["title"] or ""
                content     = row["content"] or ""
                stock_name  = row["stock_name"] or ""
                full_text   = f"{title} {content}".strip()

                try:
                    if stock_name:
                        result = analyzer.analyze_entity(stock_name, full_text)
                    else:
                        result = analyzer.analyze_text(full_text)

                    update_article(cur, article_id, result)
                    success += 1
                except Exception as e:
                    failed += 1

                processed += 1

            # Progress report every batch
            elapsed  = time.time() - start
            rate     = processed / elapsed if elapsed > 0 else 0
            eta_secs = (total - processed) / rate if rate > 0 else 0
            eta_min  = int(eta_secs / 60)

            print(
                f"  [{processed:>6,}/{total:,}] "
                f"OK={success:,} FAIL={failed:,} | "
                f"{rate:.1f} art/s | ETA ~{eta_min}min",
                flush=True
            )

            time.sleep(SLEEP_SECS)

        print(f"\n[{label}] Done. Processed {processed:,} | Success {success:,} | Failed {failed:,}")
        elapsed_total = int((time.time() - start) / 60)
        print(f"Time elapsed: {elapsed_total} min\n")

    cur.close()
    conn.close()
    print(f"[{datetime.now():%Y-%m-%d %H:%M}] Backfill complete.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sentiment backfill runner")
    parser.add_argument("--rescore", action="store_true", help="Also rescore articles missing confidence")
    parser.add_argument("--limit",   type=int, default=0,  help="Max articles to process (0 = all)")
    args = parser.parse_args()
    if args.limit == 0:
        args.limit = None

    run(args)
