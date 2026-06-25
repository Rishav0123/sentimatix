"""
Standalone data fetcher — pulls real news from Sentimatix Supabase
and returns a formatted, grounded brief for direct injection into CrewAI tasks.
No LLM required at this stage.
"""
from supabase import create_client, Client
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
import os

load_dotenv()


def fetch_stock_brief(stock_symbol: str, limit: int = 10) -> str:
    """Fetch latest news for a stock and return a formatted research brief."""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not url or not key:
        raise ValueError("Supabase credentials missing from environment.")

    sb: Client = create_client(url, key)

    # Ensure symbol has .NS suffix
    symbol = stock_symbol if stock_symbol.endswith(".NS") else f"{stock_symbol}.NS"

    # Filter for the last 30 days to leverage the index and keep the brief relevant
    since = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()

    # Query the stocks table first to get the indexed stock UUID
    stock_resp = sb.table("stocks").select("id").eq("yfin_symbol", symbol).execute()
    
    if stock_resp.data:
        stock_id = stock_resp.data[0]["id"]
        response = (
            sb.table("news")
            .select("title, source, published_at, sentiment, url")
            .eq("stock_id", stock_id)
            .gte("published_at", since)
            .order("published_at", desc=True)
            .limit(limit)
            .execute()
        )
    else:
        # Fallback to symbol-based query if not found in stocks directory
        response = (
            sb.table("news")
            .select("title, source, published_at, sentiment, url")
            .eq("yfin_symbol", symbol)
            .gte("published_at", since)
            .order("published_at", desc=True)
            .limit(limit)
            .execute()
        )

    articles = response.data
    if not articles:
        return f"No recent news found in the Sentimatix database for {symbol}."

    # Sentiment summary counts
    counts = {"positive": 0, "negative": 0, "neutral": 0, "unscored": 0}
    for a in articles:
        s = (a.get("sentiment") or "unscored").lower()
        counts[s if s in counts else "unscored"] += 1

    total = len(articles)
    bullish_pct = round(counts["positive"] / total * 100)
    bearish_pct = round(counts["negative"] / total * 100)

    lines = [
        f"# SENTIMATIX GROUNDED BRIEF: {symbol}",
        f"**Data pulled:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        f"**Sentiment summary across {total} articles:** "
        f"{bullish_pct}% Bullish | {bearish_pct}% Bearish | {counts['neutral']} Neutral\n",
        "## Latest News Articles (with live source links)\n",
    ]

    for idx, a in enumerate(articles, 1):
        sentiment = (a.get("sentiment") or "UNSCORED").upper()
        pub = a.get("published_at", "")[:10]
        title = a.get("title", "No title")
        src = a.get("source", "Unknown")
        article_url = a.get("url", "")

        link = f"[{title}]({article_url})" if article_url else title
        lines.append(f"{idx}. **{link}**")
        lines.append(f"   - Source: **{src}** | Date: {pub} | Sentiment: `{sentiment}`\n")

    return "\n".join(lines)


if __name__ == "__main__":
    brief = fetch_stock_brief("RELIANCE")
    print(brief)
