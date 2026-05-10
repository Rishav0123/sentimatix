# Phase A — yfinance Fallback: Implementation Plan

## Goal

Fix all broken price-dependent MCP tools by adding yfinance as a fallback
in the backend price endpoint. Also add the new `get_news_with_price_context`
MCP tool using the same yfinance data source.

## What's Broken Today

The `stock_prices` Supabase table is stale (no active ingestion job).
Every tool that depends on price data returns empty results:

- `get_stock_summary` → calls `/stocks/prices/{symbol}` → empty
- `get_historical_prices` → same
- `get_technical_analysis` → same (depends on price history)
- `calculate_correlation` → same
- `explain_price_change` → same
- `get_news_with_price_context` → doesn't exist yet

## Root Cause in Code

```
MCP tool → backend /stocks/prices/{symbol}
         → get_stock_prices() in database.py (line 5)
         → queries stock_prices Supabase table (stale)
         → returns [] ← the actual problem
```

One function. One fix.

---

## Proposed Changes

### [MODIFY] [requirements.txt](file:///d:/sentimatix/apps/api/requirements.txt)

Add `yfinance` to the API dependencies.

```diff
+ yfinance>=0.2.40
```

**Why here**: The fallback runs inside the FastAPI backend process,
not in the MCP. The MCP calls the backend API; the backend needs yfinance.

---

### [MODIFY] [database.py](file:///d:/sentimatix/apps/api/database.py)

**Current `get_stock_prices` (line 5–61)**:
- Resolves symbol → stock_id → queries `stock_prices` table
- Returns `[]` if table has no data for the date range

**Change**: Add yfinance fallback when Supabase returns empty.

The fallback logic goes in **one place** — after line 58 (the return statement),
inside the `get_stock_prices` function:

```python
# After:
#   return response.data if response and hasattr(response, 'data') else []
# Add fallback:

if not response.data:
    logger.info(f"stock_prices table empty for {key}, falling back to yfinance")
    return _fetch_from_yfinance(key, start_date, end_date)

return response.data
```

And add the helper function above `get_stock_prices`:

```python
def _fetch_from_yfinance(symbol: str, start_date: datetime, end_date: datetime) -> list:
    """
    Fallback price fetch from yfinance when stock_prices table is stale.
    Normalises output to match the stock_prices table schema expected by callers.
    """
    try:
        import yfinance as yf
        # Ensure .NS suffix for NSE stocks
        yfin_symbol = symbol.upper()
        if not yfin_symbol.endswith(".NS"):
            yfin_symbol = yfin_symbol + ".NS"

        ticker = yf.Ticker(yfin_symbol)
        df = ticker.history(
            start=start_date.strftime("%Y-%m-%d"),
            end=(end_date + timedelta(days=1)).strftime("%Y-%m-%d")  # yfinance end is exclusive
        )

        if df.empty:
            return []

        result = []
        for ts, row in df.iterrows():
            open_  = round(float(row["Open"]),   2)
            close_ = round(float(row["Close"]),  2)
            result.append({
                "date":           str(ts.date()),
                "open":           open_,
                "high":           round(float(row["High"]),   2),
                "low":            round(float(row["Low"]),    2),
                "close":          close_,
                "volume":         int(row["Volume"]),
                "change":         round(close_ - open_, 2),
                "change_percent": round((close_ - open_) / open_ * 100, 2) if open_ else 0,
            })
        return result

    except Exception as e:
        print(f"yfinance fallback failed for {symbol}: {e}")
        return []
```

> [!IMPORTANT]
> The output dict keys (`date`, `open`, `high`, `low`, `close`, `volume`,
> `change`, `change_percent`) exactly match what `get_stock_prices_history`
> in `server.py` (line 1838–1847) already formats. No changes needed in the
> formatter.

---

### [MODIFY] [server.py](file:///d:/sentimatix/apps/api/server.py) — `get_stock_prices_history` (lines 1815–1856)

**Current** (line 1830–1832):
```python
stock_data = await get_stock_prices(supabase, clean_symbol, start_date, end_date)
if not stock_data:
    logger.info(f"No price data found for {symbol}")
    return []
```

**Change**: Log that yfinance fallback will be tried (the actual fallback is
already inside `get_stock_prices` now), and remove the early-return on empty:

```python
stock_data = await get_stock_prices(supabase, clean_symbol, start_date, end_date)
if not stock_data:
    logger.warning(f"No price data for {symbol} from Supabase or yfinance fallback")
    return []
```

This is a **one-line log message change** — the logic moved to `database.py`.

---

### [NEW] `server/tools/news_tools.py` — `get_news_with_price_context()`

Add a new function that fetches news from Supabase and enriches each
article with same-day price data from yfinance.

```python
def get_news_with_price_context(
    symbol: str,
    start_date: str,
    end_date: str,
    top_n: int = 10
) -> dict:
    """
    Returns news articles enriched with price context for each article's date.
    Price data comes from yfinance (or Supabase if table is fresh).
    """
    # 1. Fetch news from Supabase (reuse existing get_news_sentiment logic)
    news = get_news_sentiment(symbol, start_date, end_date, top_n)
    if not news or "error" in news:
        return news

    # 2. Fetch full price range from yfinance — one call for entire date range
    yfin_symbol = symbol.upper()
    if not yfin_symbol.endswith(".NS"):
        yfin_symbol += ".NS"

    try:
        import yfinance as yf
        df = yf.Ticker(yfin_symbol).history(start=start_date, end=end_date)
        price_by_date = {}
        for ts, row in df.iterrows():
            d = str(ts.date())
            open_ = float(row["Open"])
            close_ = float(row["Close"])
            price_by_date[d] = {
                "price_on_date":      round(close_, 2),
                "price_change_pct":   round((close_ - open_) / open_ * 100, 2) if open_ else 0,
            }
    except Exception:
        price_by_date = {}

    # 3. Enrich each article
    articles = news.get("articles", news) if isinstance(news, dict) else news
    for article in articles:
        pub_date = (article.get("published_at") or "")[:10]
        price_ctx = price_by_date.get(pub_date)
        if price_ctx:
            article["price_context"] = {
                **price_ctx,
                "sentiment_confirmed": (
                    (article.get("sentiment") == "positive" and price_ctx["price_change_pct"] > 0)
                    or (article.get("sentiment") == "negative" and price_ctx["price_change_pct"] < 0)
                )
            }
        else:
            article["price_context"] = None  # Weekend / holiday — no trading

    return {"symbol": symbol, "articles": articles}
```

---

### [MODIFY] [mcp_stdio.py](file:///d:/sentimatix/apps/mcp/mcp_stdio.py) — Register new tool

**In `list_tools()` (after line 305)**, add:

```python
types.Tool(
    name="get_news_with_price_context",
    description=(
        "Fetches news articles for an NSE stock enriched with same-day market "
        "price data. For each article, returns the closing price on publication "
        "date, the day's price change %, and whether the market confirmed or "
        "contradicted the news sentiment. Unique to Sentimatix — no other tool "
        "provides this sentiment-price confirmation signal."
    ),
    inputSchema={
        "type": "object",
        "properties": {
            "symbol":     {"type": "string", "description": "NSE stock symbol e.g. TCS, RELIANCE"},
            "start_date": {"type": "string", "description": "Start date YYYY-MM-DD"},
            "end_date":   {"type": "string", "description": "End date YYYY-MM-DD"},
            "top_n":      {"type": "integer", "default": 10, "minimum": 1, "maximum": 30},
        },
        "required": ["symbol", "start_date", "end_date"],
    },
),
```

**In `call_tool()` (after the `get_rag_evidence` block)**, add:

```python
elif name == "get_news_with_price_context":
    result = get_news_with_price_context(**arguments)
```

**In imports (top of file)**, add:

```python
from server.tools.news_tools import get_news_with_price_context
```

---

### [MODIFY] Smithery TOOLS_LIST in `mcp_stdio.py` (line ~410)

Add the same tool to the `TOOLS_LIST` dict inside `run_sse()` for Smithery
scanning:

```python
{
    "name": "get_news_with_price_context",
    "description": "Retrieves financial news for an NSE stock with actual market "
                   "price reactions embedded per article. Returns closing price on "
                   "the publication date, same-day price change %, and a "
                   "sentiment_confirmed boolean indicating whether the market "
                   "confirmed or rejected the news sentiment. A capability unique "
                   "to Sentimatix.",
    "inputSchema": {
        "type": "object",
        "properties": {
            "symbol":     {"type": "string", "description": "NSE stock symbol (e.g. HDFCBANK, TCS)."},
            "start_date": {"type": "string", "description": "Start date (YYYY-MM-DD)."},
            "end_date":   {"type": "string", "description": "End date (YYYY-MM-DD)."},
            "top_n":      {"type": "integer", "description": "Max articles to return (default 10)."},
        },
        "required": ["symbol", "start_date", "end_date"]
    }
},
```

---

## File Change Summary

| File | Change Type | Lines Affected |
|------|------------|----------------|
| `apps/api/requirements.txt` | Add dependency | +1 line |
| `apps/api/database.py` | Add `_fetch_from_yfinance()` + fallback call | ~40 lines added |
| `apps/api/server.py` | Update log message in `get_stock_prices_history` | 1 line |
| `apps/mcp/server/tools/news_tools.py` | Add `get_news_with_price_context()` | ~50 lines |
| `apps/mcp/mcp_stdio.py` | Register new tool in list + handler + import | ~25 lines |

**Total: ~117 lines changed/added. Zero deletions. Zero breaking changes.**

---

## Verification Plan

1. **Price tools**: Call `get_stock_summary` for `TCS` — should return current price, not empty
2. **Historical**: Call `get_historical_prices` for `RELIANCE` with last 30 days — should return 20–22 trading day records
3. **New tool**: Call `get_news_with_price_context` for `HDFCBANK` — articles should have `price_context` populated
4. **Existing tools unaffected**: Call `get_news_sentiment` — should still work exactly as before
5. **MCP registration**: Check Smithery scanner sees 12 tools (was 11)

---

## Deployment Note

After changes, redeploy the FastAPI backend (Railway/EC2). The MCP server
picks up the new tool automatically on next restart since it imports from
the same `server/tools/` package.
