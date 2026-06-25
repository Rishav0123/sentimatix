# Sentimatix Data Dictionary

## Table: `news`
Core dataset containing ingested articles and AI-generated sentiment scores.

| Field Name | Type | Description |
| :--- | :--- | :--- |
| `id` | UUID | Unique identifier for the news record |
| `title` | String | Headline of the news article |
| `content` | Text | Full text or snippet of the article |
| `url` | String | Source URL of the article |
| `source` | String | Name of the publisher (e.g., Moneycontrol, Telegram Bot) |
| `published_at` | Timestamp | UTC timestamp of when the article was published |
| `yfin_symbol` | String | Mapped Yahoo Finance ticker symbol (e.g., RELIANCE.NS) |
| `sentiment` | String | Categorical label: `positive`, `negative`, `neutral`, `conflicted` |
| `sentiment_score` | Float | Continuous score ranging from -1.0 to +1.0 |
| `confidence` | Float | AI confidence score for the assigned sentiment (0.0 to 1.0) |
| `is_volatile` | Boolean | True if the news is classified as market-sensitive (Earnings, M&A) |
| `is_ready` | String | Status flag indicating if processing is complete (e.g., 'Y') |

## Table: `stocks`
Entity directory for supported equities.

| Field Name | Type | Description |
| :--- | :--- | :--- |
| `yfin_symbol` | String | Yahoo Finance ticker symbol (Primary Key) |
| `stock_name` | String | Full registered company name |
| `sector` | String | Industry classification (e.g., Banking, IT Services) |
| `exchange` | String | Stock Exchange (e.g., NSE) |
| `country` | String | Country of exchange (e.g., India) |
| `sentiment_7d` | Float | Moving average sentiment score over the last 7 days |
| `sentiment_30d` | Float | Moving average sentiment score over the last 30 days |
| `is_active` | Boolean | Whether the stock is currently monitored |
