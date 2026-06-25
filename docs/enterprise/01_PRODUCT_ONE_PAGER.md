# Sentimatix: Enterprise Financial Sentiment API

## What is Sentimatix?
Sentimatix is an institutional-grade financial data engine that aggregates, structures, and analyzes financial news for the Indian Stock Market (NSE). We translate unstructured news articles into real-time, quantifiable sentiment scores and entity-linked datasets designed for algorithmic trading, quantitative analysis, and risk management.

## The Problem Solved
Traditional financial data feeds deliver raw, unstructured news that requires significant NLP engineering to process. Quant funds and institutional platforms spend millions building pipelines to ingest, deduplicate, entity-link, and analyze market news. Sentimatix provides this entire pipeline as a simple, low-latency API.

## Coverage
- **Markets:** National Stock Exchange of India (NSE)
- **Equities:** Comprehensive coverage of NSE-listed entities across all major sectors (Banking, IT, Auto, etc.)
- **News Sources:** Continuous monitoring of top-tier Indian financial news outlets, Telegram bot feeds, and real-time market wires.
- **Historical Depth:** Parquet-backed cold-tier storage for deep historical backtesting, alongside real-time Postgres hot-tier updates.

## Sentiment Methodology
Sentimatix utilizes fine-tuned AI models to analyze financial context rather than simple word counting.
- **Deduplication:** Aggressive filtering to ensure unique market events.
- **Entity Resolution:** Automatic mapping of complex company mentions to standardized Yahoo Finance ticker symbols (e.g., RELIANCE.NS).
- **Sentiment Scoring:** Continuous score from -1.0 to +1.0, categorized into Bullish, Bearish, and Neutral.
- **Volatility Tagging:** Identifying 'market-sensitive' events (M&A, earnings, dividends) critical for immediate price action.

## API Capabilities
- **`/api/v1/news`:** Real-time and historical news filtering by ticker, sector, and sentiment.
- **`/api/v1/sentiment`:** Aggregated 7-day and 30-day stock-level sentiment scores.
- **`/api/v1/sentiment/sectors`:** Macro-level market sentiment tracking by industry.
- **`/api/v1/entities`:** Discoverable directory of active NSE tickers and base sentiment metadata.

## Contact
**Interactive API Docs:** [https://sentimatix-production.up.railway.app/docs](https://sentimatix-production.up.railway.app/docs)
**Email:** [Your Email]
