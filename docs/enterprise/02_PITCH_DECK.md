# Pitch Deck: Sentimatix

**Slide 1: Title Slide**
- **Headline:** Sentimatix - Structuring the Unstructured Indian Market.
- **Sub-headline:** Real-time sentiment analysis and financial news API for institutional investors.

**Slide 2: The Problem**
- The Indian stock market generates thousands of news articles daily.
- 80% of actionable market data is trapped in unstructured text.
- Funds spend excessive resources building NLP pipelines instead of trading models.

**Slide 3: The Opportunity**
- The NSE is one of the fastest-growing exchanges globally.
- Demand for quantitative, machine-readable news data for Indian equities is massively underserved compared to US markets.

**Slide 4: Our Solution**
- **Sentimatix:** A turnkey API that ingests, cleans, entity-links, and scores Indian financial news in real-time.
- We turn noise into quantifiable alpha.

**Slide 5: Platform Architecture**
- **Ingestion:** Scrapers targeting premium financial portals and Telegram feeds.
- **AI Engine:** Context-aware sentiment extraction and deduplication.
- **Storage:** Dual-tier system (Postgres Hot Tier for low latency, DuckDB/Parquet Cold Tier for historical scale).
- **Delivery:** High-performance REST API.

**Slide 6: Data Sourcing & Coverage**
- Focus: NSE (National Stock Exchange).
- Entity mapping standard: Yahoo Finance `.NS` tickers.
- Real-time updates with deep historical archives available for backtesting.

**Slide 7: The Sentiment Engine**
- Beyond simple positive/negative.
- Confidences scores, categorical tags, and a continuous `-1.0` to `+1.0` scale.
- **Volatility Tagging:** Specialized detection for market-sensitive events (Earnings, M&A).

**Slide 8: API Capabilities**
- RESTful, JSON-based.
- Real-time news streams.
- Aggregated ticker and sector-level sentiment.
- Enterprise-grade rate limiting and analytics (Mixpanel integrated).

**Slide 9: Use Cases**
- **Quant Funds:** Incorporate sentiment as an alpha factor in trading algorithms.
- **Retail Brokerages:** Display 'Live Stock Sentiment' on user dashboards (Zerodha, Upstox).
- **Risk Management:** Early warning alerts for negative PR or market-sensitive events.

**Slide 10: Competitive Advantage**
- Hyper-focused on the nuances of the Indian market.
- Cost-effective compared to Bloomberg or Refinitiv terminals.
- Developer-first API design.

**Slide 11: Contact & Next Steps**
- **Email:** [Your Email]
- **Interactive API Docs:** https://sentimatix-production.up.railway.app/docs
- **Call to Action:** Schedule a live data integration session.
