"""
Backfill missing stock_id in the news table.

The scrape_moneycontrol (and potentially early scrape_gnews) runs stored news rows
without populating `stock_id`. Since `yfin_symbol` was always stored, we can JOIN
news -> stocks on yfin_symbol to fill the gap.

Run once, safe to re-run (WHERE stock_id IS NULL guard prevents touching already-fixed rows).
"""

import os
import sys
from pathlib import Path

# Allow running from repo root or scripts/ directory
sys.path.append(str(Path(__file__).parent.parent / "worker-SCRAPE" / "stock-news" / "x-news"))

from dotenv import load_dotenv
from supabase import create_client

# Load env from x-news .env (has SUPABASE_URL and SUPABASE_KEY)
env_path = Path(__file__).parent.parent / "worker-SCRAPE" / "stock-news" / "x-news" / ".env"
load_dotenv(dotenv_path=env_path)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("ERROR: SUPABASE_URL and SUPABASE_KEY must be set.")
    sys.exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def audit_missing():
    """Report how many news rows are missing stock_id, grouped by yfin_symbol."""
    print("\n=== Audit: news rows with missing stock_id ===")

    # Fetch all news rows that have no stock_id but have a yfin_symbol
    result = (
        supabase.table("news")
        .select("id, yfin_symbol")
        .is_("stock_id", "null")
        .not_.is_("yfin_symbol", "null")
        .execute()
    )
    rows = result.data or []

    if not rows:
        print("No rows with missing stock_id found. Nothing to do!")
        return {}

    # Group by yfin_symbol
    from collections import Counter
    counts = Counter(r["yfin_symbol"] for r in rows)
    print(f"Total rows missing stock_id: {len(rows)}")
    for sym, cnt in sorted(counts.items()):
        print(f"  {sym}: {cnt} rows")

    return counts


def backfill():
    """
    Update news.stock_id for rows where it is NULL,
    by matching news.yfin_symbol = stocks.yfin_symbol.
    """
    print("\n=== Fetching stocks table for yfin_symbol -> id mapping ===")
    stocks_resp = supabase.table("stocks").select("id, yfin_symbol").execute()
    stocks = stocks_resp.data or []

    if not stocks:
        print("ERROR: No stocks found in stocks table!")
        sys.exit(1)

    # Build mapping: yfin_symbol -> stock id
    symbol_to_id = {s["yfin_symbol"]: s["id"] for s in stocks if s.get("yfin_symbol")}
    print(f"Loaded {len(symbol_to_id)} stocks with yfin_symbol.")

    print("\n=== Fetching news rows with missing stock_id ===")
    news_resp = (
        supabase.table("news")
        .select("id, yfin_symbol, stock_id")
        .is_("stock_id", "null")
        .not_.is_("yfin_symbol", "null")
        .execute()
    )
    news_rows = news_resp.data or []

    if not news_rows:
        print("No news rows with missing stock_id. Nothing to update.")
        return

    print(f"Found {len(news_rows)} news rows to backfill.")

    updated = 0
    skipped_no_match = 0
    errors = 0

    for row in news_rows:
        news_id = row["id"]
        yfin_symbol = row["yfin_symbol"]

        if yfin_symbol not in symbol_to_id:
            print(f"  SKIP  id={news_id}: yfin_symbol='{yfin_symbol}' not found in stocks table")
            skipped_no_match += 1
            continue

        stock_id = symbol_to_id[yfin_symbol]

        try:
            supabase.table("news").update({"stock_id": stock_id}).eq("id", news_id).execute()
            updated += 1
        except Exception as e:
            print(f"  ERROR id={news_id}: {e}")
            errors += 1

    print(f"\n=== Backfill complete ===")
    print(f"  Updated:             {updated}")
    print(f"  Skipped (no match):  {skipped_no_match}")
    print(f"  Errors:              {errors}")


if __name__ == "__main__":
    missing_before = audit_missing()
    if not missing_before:
        sys.exit(0)

    confirm = input("\nProceed with backfill? [y/N]: ").strip().lower()
    if confirm != "y":
        print("Aborted.")
        sys.exit(0)

    backfill()

    print("\n=== Post-backfill audit ===")
    audit_missing()
