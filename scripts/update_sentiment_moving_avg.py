"""
update_sentiment_moving_avg.py
===============================
Recalculates sentiment moving averages for all active stocks and writes them
back to the `stocks` table. Also bumps `updated_at` and `sentiment_updated_at`.

Columns updated in stocks:
  - sentiment_7d           → avg(sentiment_score) for news in last 7 days
  - sentiment_30d          → avg(sentiment_score) for news in last 30 days
  - sentiment_updated_at   → now()
  - updated_at             → now()

Usage:
    python scripts/update_sentiment_moving_avg.py          # all active stocks
    python scripts/update_sentiment_moving_avg.py --dry-run # preview without writing
"""

import argparse
import psycopg2
import psycopg2.extras
from datetime import datetime

DB_PARAMS = {
    "host":     "aws-1-ap-southeast-2.pooler.supabase.com",
    "port":     5432,
    "database": "postgres",
    "user":     "postgres.hdsntducurmhossannue",
    "password": "Wallposter27@"
}


def get_conn():
    return psycopg2.connect(**DB_PARAMS)


# ── Single SQL UPDATE that does all the math in Postgres ──────────────────────
UPDATE_SQL = """
UPDATE public.stocks s
SET
    sentiment_7d          = sub.avg_7d,
    sentiment_30d         = sub.avg_30d,
    sentiment_updated_at  = NOW(),
    updated_at            = NOW()
FROM (
    SELECT
        stock_id,
        ROUND(
            AVG(sentiment_score) FILTER (
                WHERE published_at >= NOW() - INTERVAL '7 days'
                  AND sentiment_score IS NOT NULL
            )::numeric, 4
        ) AS avg_7d,
        ROUND(
            AVG(sentiment_score) FILTER (
                WHERE published_at >= NOW() - INTERVAL '30 days'
                  AND sentiment_score IS NOT NULL
            )::numeric, 4
        ) AS avg_30d
    FROM public.news
    WHERE stock_id IS NOT NULL
    GROUP BY stock_id
) sub
WHERE s.id = sub.stock_id
  AND s.is_active = TRUE
RETURNING
    s.yfin_symbol,
    s.sentiment_7d,
    s.sentiment_30d,
    s.sentiment_updated_at;
"""

# ── Preview query (dry-run) ───────────────────────────────────────────────────
PREVIEW_SQL = """
SELECT
    s.yfin_symbol,
    s.sentiment_7d  AS current_7d,
    s.sentiment_30d AS current_30d,
    ROUND(
        AVG(n.sentiment_score) FILTER (
            WHERE n.published_at >= NOW() - INTERVAL '7 days'
        )::numeric, 4
    ) AS new_7d,
    ROUND(
        AVG(n.sentiment_score) FILTER (
            WHERE n.published_at >= NOW() - INTERVAL '30 days'
        )::numeric, 4
    ) AS new_30d,
    COUNT(n.id) FILTER (
        WHERE n.published_at >= NOW() - INTERVAL '7 days'
          AND n.sentiment_score IS NOT NULL
    ) AS articles_7d,
    COUNT(n.id) FILTER (
        WHERE n.published_at >= NOW() - INTERVAL '30 days'
          AND n.sentiment_score IS NOT NULL
    ) AS articles_30d
FROM public.stocks s
LEFT JOIN public.news n ON n.stock_id = s.id
WHERE s.is_active = TRUE
GROUP BY s.id, s.yfin_symbol, s.sentiment_7d, s.sentiment_30d
ORDER BY s.yfin_symbol;
"""


def run(dry_run: bool):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{now}] Connecting to database...")

    conn = get_conn()
    conn.autocommit = False
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    if dry_run:
        print("\n[DRY-RUN] Showing what WOULD be written (no changes made):\n")
        print(f"{'Symbol':<20} {'Old 7d':>8} {'New 7d':>8}  {'Old 30d':>8} {'New 30d':>8}  {'Art 7d':>7} {'Art 30d':>7}")
        print("-" * 80)
        cur.execute(PREVIEW_SQL)
        rows = cur.fetchall()
        changed = 0
        for r in rows:
            sym       = r["yfin_symbol"]
            old_7d    = r["current_7d"]
            new_7d    = r["new_7d"]
            old_30d   = r["current_30d"]
            new_30d   = r["new_30d"]
            art_7d    = r["articles_7d"]
            art_30d   = r["articles_30d"]
            marker = " ←" if (old_7d != new_7d or old_30d != new_30d) else ""
            if marker:
                changed += 1
            print(f"{sym:<20} {str(old_7d):>8} {str(new_7d):>8}  {str(old_30d):>8} {str(new_30d):>8}  {art_7d:>7} {art_30d:>7}{marker}")
        print(f"\n{len(rows)} stocks reviewed, {changed} would be updated.")
    else:
        print("\nUpdating sentiment moving averages in stocks table...")
        cur.execute(UPDATE_SQL)
        updated_rows = cur.fetchall()
        conn.commit()

        print(f"\nUpdated {len(updated_rows)} stocks:\n")
        print(f"{'Symbol':<20} {'sentiment_7d':>14} {'sentiment_30d':>14}  {'Updated At'}")
        print("-" * 75)
        for r in updated_rows:
            print(f"{r['yfin_symbol']:<20} {str(r['sentiment_7d']):>14} {str(r['sentiment_30d']):>14}  {r['sentiment_updated_at']}")

        # Stocks with no news at all (left out of the UPDATE)
        cur.execute("""
            SELECT yfin_symbol FROM public.stocks
            WHERE is_active = TRUE
              AND id NOT IN (SELECT DISTINCT stock_id FROM public.news WHERE stock_id IS NOT NULL);
        """)
        no_news = [r[0] for r in cur.fetchall()]
        if no_news:
            print(f"\nWARNING: {len(no_news)} active stocks have no linked news (stock_id IS NULL in news):")
            print("   ", ", ".join(no_news))

    cur.close()
    conn.close()
    print(f"\n[{datetime.now():%Y-%m-%d %H:%M:%S}] Done.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Update sentiment moving averages in stocks table")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without writing to DB")
    args = parser.parse_args()
    run(dry_run=args.dry_run)
