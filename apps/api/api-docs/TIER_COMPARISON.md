# Sentimatix API — Free vs Pro Tier Comparison

> Base URL: `https://stockify-back.onrender.com`  
> Authentication: `Authorization: Bearer <your_api_key>`

---

## Tier Summary

| | Free | Pro (₹199/mo) | Enterprise |
|---|---|---|---|
| **Price** | ₹0 | ₹199/month | Custom |
| **Requests/day** | 50 | 5,000 | Unlimited |
| **News history** | Last 7 days only | Full history | Full history |
| **Max results per request** | 3 | 100 | 1,000 |
| **Raw sentiment scores** | ❌ | ✅ | ✅ |
| **Confidence scores** | ❌ | ✅ | ✅ |
| **Market sensitivity flag** | ❌ | ✅ | ✅ |
| **Sector sentiment** | ❌ (403) | ✅ | ✅ |
| **Stock sentiment signals** | ❌ (403) | ✅ | ✅ |
| **Phase 4 Intelligence API** | ❌ (403) | ✅ | ✅ |
| **Support** | Community | Email | Dedicated + SLA |

---

## Endpoint-by-Endpoint Breakdown

---

### `GET /api/v1/news` — Financial News Feed

Both tiers can access this endpoint, but Free is heavily restricted.

#### Free Tier
```json
{
  "meta": {
    "found": 4821,
    "returned": 3,
    "limit": 3,
    "page": 1,
    "total_pages": 1607
  },
  "data": [
    {
      "uuid": "40b41093-...",
      "title": "Reliance Q4 profits surge 18%",
      "snippet": "Reliance Industries reported strong financial results for Q4...(truncated at 200 chars)",
      "url": "https://moneycontrol.com/...",
      "source": "moneycontrol.com",
      "published_at": "2026-04-29T15:39:10Z",
      "sentiment": "positive",
      "entities": [{ "symbol": "RELIANCE.NS", "name": "Reliance Industries", "sector": "Conglomerate" }]
    }
  ]
}
```

**Restrictions applied automatically:**
- `limit` is capped to **3** regardless of what you request
- `published_after` is forced to **last 7 days** (older news is blocked)
- `snippet` is **truncated to 200 characters**
- `sentiment_score`, `confidence`, `is_market_sensitive` fields are **removed**
- `only_market_sensitive=true` filter is **ignored**

#### Pro Tier
```json
{
  "meta": {
    "found": 4821,
    "returned": 100,
    "limit": 100,
    "page": 1,
    "total_pages": 49
  },
  "data": [
    {
      "uuid": "40b41093-...",
      "title": "Reliance Q4 profits surge 18%",
      "snippet": "Full article content, no truncation...",
      "url": "https://moneycontrol.com/...",
      "source": "moneycontrol.com",
      "published_at": "2026-04-29T15:39:10Z",
      "sentiment": "positive",
      "sentiment_score": 0.72,
      "confidence": 0.89,
      "is_market_sensitive": true,
      "entities": [{ "symbol": "RELIANCE.NS", "name": "Reliance Industries", "sector": "Conglomerate", "exchange": "NSE", "country": "IN" }]
    }
  ]
}
```

**What Pro gets extra:**
- `limit` up to **100** per request
- **Full article content** (no truncation)
- **All historical data** (no 7-day cap)
- `sentiment_score` — numeric NLP score (-1.0 to +1.0)
- `confidence` — FinBERT model confidence (0.0 to 1.0)
- `is_market_sensitive` — boolean flag for high-impact news
- `only_market_sensitive=true` filter works

---

### `GET /api/v1/entities` — Stock Directory

Both tiers can access this. Free gets basic metadata only.

#### Free Tier
```json
{
  "data": [
    {
      "symbol": "RELIANCE.NS",
      "name": "Reliance Industries",
      "sector": "Conglomerate",
      "exchange": "NSE",
      "country": "IN"
    }
  ]
}
```

#### Pro Tier
```json
{
  "data": [
    {
      "symbol": "RELIANCE.NS",
      "name": "Reliance Industries",
      "sector": "Conglomerate",
      "exchange": "NSE",
      "country": "IN",
      "sentiment_7d": 31.13,
      "sentiment_30d": 25.32
    }
  ]
}
```

**What Pro gets extra:**
- `sentiment_7d` — 7-day rolling sentiment score
- `sentiment_30d` — 30-day rolling sentiment score

---

### `GET /api/v1/sentiment` — Stock Sentiment Signals 🔒 Pro Only

#### Free Tier
```json
{
  "detail": "Sentiment endpoint requires Pro or Enterprise tier."
}
```
HTTP Status: `403 Forbidden`

#### Pro Tier
```json
{
  "data": [
    {
      "symbol": "TCS.NS",
      "name": "Tata Consultancy Services",
      "sector": "IT Services",
      "sentiment_7d": -55.04,
      "sentiment_30d": -55.04,
      "sentiment_label": "Bearish",
      "updated_at": "2026-04-30T00:34:43Z"
    }
  ]
}
```

**Parameters:**
- `symbols` (required) — comma-separated tickers e.g. `TCS,RELIANCE`
- `period` — `7d` or `30d`

---

### `GET /api/v1/sentiment/sectors` — Sector Sentiment 🔒 Pro Only

#### Free Tier
```json
{ "detail": "Sector Sentiment endpoint requires Pro or Enterprise tier." }
```
HTTP Status: `403 Forbidden`

#### Pro Tier
```json
{
  "period": "7d",
  "data": [
    { "sector": "IT Services", "avg_sentiment_score": -0.3369, "sentiment_label": "Bearish", "total_articles": 9 },
    { "sector": "Pharmaceuticals", "avg_sentiment_score": -0.1095, "sentiment_label": "Neutral", "total_articles": 3 },
    { "sector": "Banking", "avg_sentiment_score": 0.2812, "sentiment_label": "Bullish", "total_articles": 21 }
  ]
}
```

---

### `GET /api/sentiment/stock/{symbol}` — Full Stock Insight Object 🔒 Pro Only

#### Free Tier
```json
{ "detail": "Stock sentiment insight requires a Pro or Enterprise subscription." }
```
HTTP Status: `403 Forbidden`

#### Pro Tier
```json
{
  "entity": "Tata Consultancy Services",
  "yfin_symbol": "TCS.NS",
  "sector": "IT Services",
  "sentiment": {
    "label": "negative",
    "score": -0.3291,
    "confidence": 0.7841,
    "is_volatile": false
  },
  "momentum": {
    "sentiment_7d": -55.04,
    "sentiment_prev_7d": -42.11,
    "slope": -12.93,
    "label": "declining",
    "articles_7d": 9,
    "articles_today": 2,
    "volume_z_score": 0.81,
    "volume_alert": "normal"
  },
  "top_news": [
    { "title": "TCS misses Q4 estimates...", "sentiment": "negative", "score": -0.51, "confidence": 0.88, "published_at": "2026-04-29T10:00:00Z" }
  ],
  "context_clause": "TCS misses Q4 estimates amid global slowdown concerns",
  "generated_at": "2026-04-30T17:30:00Z"
}
```

---

### `GET /api/sentiment/market` — Market-Wide Heatmap 🔒 Pro Only

#### Free Tier
```json
{ "detail": "Market sentiment heatmap requires a Pro or Enterprise subscription." }
```
HTTP Status: `403 Forbidden`

#### Pro Tier
```json
{
  "count": 50,
  "generated_at": "2026-04-30T17:30:00Z",
  "stocks": [
    {
      "yfin_symbol": "TCS.NS",
      "stock_name": "Tata Consultancy Services",
      "sector": "IT Services",
      "sentiment_7d": -55.04,
      "momentum_slope": -12.93,
      "momentum_label": "declining",
      "volume_z_score": 0.81,
      "volume_alert": "normal",
      "articles_7d": 9,
      "articles_today": 2
    }
  ]
}
```

---

### `GET /api/sentiment/news` — Enriched News Feed 🔒 Pro Only

#### Free Tier
```json
{ "detail": "Enriched sentiment news feed requires a Pro or Enterprise subscription." }
```
HTTP Status: `403 Forbidden`

#### Pro Tier — Includes computed `signal` and `impact_tier` fields
```json
{
  "count": 20,
  "articles": [
    {
      "title": "Reliance Q4 profits surge 18%",
      "sentiment": "positive",
      "sentiment_score": 0.72,
      "confidence": 0.89,
      "is_volatile": false,
      "signal": "bullish",
      "impact_tier": "high"
    }
  ]
}
```

---

### `GET /api/sentiment/momentum/leaderboard` — Winners & Losers 🔒 Pro Only

#### Free Tier
```json
{ "detail": "Momentum leaderboard requires a Pro or Enterprise subscription." }
```
HTTP Status: `403 Forbidden`

#### Pro Tier
```json
{
  "generated_at": "2026-04-30T17:30:00Z",
  "improving": [
    { "yfin_symbol": "RELIANCE.NS", "stock_name": "Reliance Industries", "sentiment_7d": 31.13, "momentum_slope": 12.45, "momentum_label": "improving", "volume_alert": "elevated" }
  ],
  "declining": [
    { "yfin_symbol": "TCS.NS", "stock_name": "Tata Consultancy Services", "sentiment_7d": -55.04, "momentum_slope": -12.93, "momentum_label": "declining", "volume_alert": "normal" }
  ]
}
```

---

## Quick Reference

| Endpoint | Free | Pro |
|---|---|---|
| `GET /api/v1/news` | ✅ (3 results, 7d, no scores) | ✅ (100 results, all history, full scores) |
| `GET /api/v1/entities` | ✅ (basic fields only) | ✅ (+ sentiment_7d, sentiment_30d) |
| `GET /api/v1/sentiment` | ❌ 403 | ✅ |
| `GET /api/v1/sentiment/sectors` | ❌ 403 | ✅ |
| `GET /api/sentiment/stock/{symbol}` | ❌ 403 | ✅ |
| `GET /api/sentiment/market` | ❌ 403 | ✅ |
| `GET /api/sentiment/news` | ❌ 403 | ✅ |
| `GET /api/sentiment/momentum/leaderboard` | ❌ 403 | ✅ |

---

## Upgrade to Pro

Click "Upgrade to Pro" on the portal page and pay securely via Razorpay (UPI, Cards, Net Banking, Wallets).

Portal: `https://stockify-back.onrender.com/portal`
