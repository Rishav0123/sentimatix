# Sentimatix API V1 Documentation

## Base URL
`https://sentimatix-production.up.railway.app`

## Authentication
Sentimatix uses Bearer token authentication or RapidAPI Proxy Secrets. 
Include your API key in the Authorization header:
`Authorization: Bearer YOUR_API_KEY`

---

## Endpoints

### 1. Search Financial News
Retrieves a paginated list of financial news articles for NSE-listed companies, including real-time sentiment and market-sensitive alerts.

**GET** `/api/v1/news`

**Parameters:**
- `symbols` (string, optional): Comma-separated NSE tickers (e.g., 'RELIANCE,TCS').
- `sectors` (string, optional): Comma-separated industry sectors (e.g., 'Banking,IT Services').
- `sentiment` (string, optional): Filter by categorical sentiment ('positive', 'negative', 'neutral', 'conflicted').
- `published_before` (string, optional): Date format YYYY-MM-DD.
- `published_after` (string, optional): Date format YYYY-MM-DD.
- `only_market_sensitive` (boolean, optional): If true, returns only high-impact news (Requires Pro+ tier).
- `limit` (int, default: 10): Max results per page.
- `page` (int, default: 1): Pagination page number.

---

### 2. List Supported Entities
Returns a directory of all NSE-listed stocks supported by the Sentimatix platform.

**GET** `/api/v1/entities`

**Parameters:**
- `sector` (string, optional): Filter by industry sector.
- `exchange` (string, default: 'NSE'): Filter by stock exchange.
- `search` (string, optional): Fuzzy search by company name or ticker symbol.

---

### 3. Get Aggregated Stock Sentiment (Pro+)
Retrieves the aggregated sentiment scores for specific stocks over a 7-day or 30-day period.

**GET** `/api/v1/sentiment`

**Parameters:**
- `symbols` (string, required): Comma-separated NSE tickers.
- `period` (string, default: '7d'): Lookback window ('7d' or '30d').

---

### 4. Get Market Sector Sentiment (Pro+)
Analyzes the 'mood' of entire market sectors by aggregating sentiment across all stocks within those sectors.

**GET** `/api/v1/sentiment/sectors`

**Parameters:**
- `sectors` (string, optional): Comma-separated sectors.
- `period` (string, default: '7d'): Lookback window ('7d' or '30d').

---

### 5. Get Trending Stocks
Returns a list of stocks with the highest news volume over a specified period.

**GET** `/api/v1/analytics/trending`

**Parameters:**
- `hours` (int, default: 24): Lookback period in hours.
