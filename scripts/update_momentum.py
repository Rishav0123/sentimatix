"""
Phase 3: Daily Sentiment Momentum Updater
==========================================
Run this AFTER your scraper completes each day.
It computes weekly momentum slope + volume Z-score for every stock
and writes them back to the stocks table.

Schedule: Once daily, after scraper completes.
Command:  python update_momentum.py
"""

import psycopg2
import psycopg2.extras
from datetime import datetime

DB_PARAMS = {
    "host": "aws-1-ap-southeast-2.pooler.supabase.com",
    "port": 5432,
    "database": "postgres",
    "user": "postgres.hdsntducurmhossannue",
    "password": "Wallposter27@"
}

# Z-Score thresholds for volume spike alerts
Z_SCORE_ALERT_HIGH    = 2.0   # Breaking news: very unusual volume
Z_SCORE_ALERT_MEDIUM  = 1.0   # Elevated coverage: worth watching


def get_momentum_label(slope: float) -> str:
    if slope is None:
        return "stable"
    if slope > 0.05:
        return "improving"
    if slope < -0.05:
        return "declining"
    return "stable"


def get_volume_alert(z_score: float) -> str:
    if z_score is None:
        return "normal"
    if z_score >= Z_SCORE_ALERT_HIGH:
        return "breaking"       # Unusual spike: 2x+ normal volume
    if z_score >= Z_SCORE_ALERT_MEDIUM:
        return "elevated"       # Above average coverage
    if z_score <= -Z_SCORE_ALERT_MEDIUM:
        return "quiet"          # Below average coverage
    return "normal"


def run():
    print(f"[{datetime.now():%Y-%m-%d %H:%M}] Starting daily momentum update...")
    conn = psycopg2.connect(**DB_PARAMS)
    conn.autocommit = True
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # Pull full momentum snapshot from the view
    cur.execute("SELECT * FROM public.v_stock_momentum ORDER BY ABS(momentum_slope) DESC NULLS LAST;")
    rows = cur.fetchall()

    if not rows:
        print("No momentum data found. Have the scrapers run today?")
        cur.close()
        conn.close()
        return

    print(f"Computing momentum for {len(rows)} stocks...\n")

    updated = 0
    alerts = []

    for row in rows:
        symbol          = row["yfin_symbol"]
        stock_name      = row["stock_name"]
        sentiment_7d    = row["sentiment_7d"]
        momentum_slope  = row["momentum_slope"]
        momentum_label  = row["momentum_label"]
        articles_today  = row["articles_today"]
        avg_daily       = row["avg_daily_articles_30d"]
        z_score         = float(row["volume_z_score"]) if row["volume_z_score"] is not None else 0.0
        volume_alert    = get_volume_alert(z_score)

        # Write back to stocks table
        cur.execute("""
            UPDATE public.stocks
            SET
                sentiment_7d          = %s,
                sentiment_updated_at  = NOW()
            WHERE yfin_symbol = %s;
        """, (sentiment_7d, symbol))

        updated += 1

        # Print per-stock summary
        arrow = "/\\" if momentum_label == "improving" else ("\\" if momentum_label == "declining" else "->")
        alert_tag = f" [{volume_alert.upper()}]" if volume_alert != "normal" else ""
        print(
            f"  {arrow} {stock_name:<35} "
            f"7d={float(sentiment_7d or 0):+.3f}  slope={float(momentum_slope or 0):+.3f}  "
            f"vol={articles_today}/{float(avg_daily or 0):.1f}  z={z_score:+.2f}{alert_tag}"
        )

        if volume_alert in ("breaking", "elevated"):
            alerts.append({
                "symbol":       symbol,
                "stock_name":   stock_name,
                "alert":        volume_alert,
                "z_score":      z_score,
                "articles_today": articles_today,
                "sentiment_7d": sentiment_7d,
                "slope":        momentum_slope
            })

    print(f"\n[OK] Updated {updated} stocks.")

    # Print alert summary
    if alerts:
        print(f"\n{'='*60}")
        print(f"VOLUME ALERTS ({len(alerts)} stocks with unusual coverage):")
        print(f"{'='*60}")
        for a in sorted(alerts, key=lambda x: x["z_score"], reverse=True):
            print(
                f"  [{a['alert'].upper():8s}] {a['stock_name']:<35} "
                f"z={a['z_score']:+.2f}  articles_today={a['articles_today']}  "
                f"7d_sentiment={float(a['sentiment_7d'] or 0):+.3f}  "
                f"slope={float(a['slope'] or 0):+.3f}"
            )
    else:
        print("\nNo volume alerts today.")

    cur.close()
    conn.close()
    print(f"\n[{datetime.now():%Y-%m-%d %H:%M}] Momentum update complete.")


if __name__ == "__main__":
    run()
