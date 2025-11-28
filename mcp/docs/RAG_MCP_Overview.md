# Stockify RAG + MCP System (Concise Study Guide)

## 1. Purpose
Combine live market + sentiment data (via existing REST APIs) with semantic retrieval over historical news to let an LLM answer "Why did X move?" or "Price vs sentiment last N days" using evidence, not guesses.

## 2. High-Level Flow
User / UI → LLM (with tool-calls) → MCP Server (/call) →
- Live APIs: /api/stocks, /api/news
- RAG Vector DB: semantic search (Supabase pgvector)
MCP orchestrator aggregates → LLM synthesizes → UI displays answer + sources.

## 3. Core Components
| Layer | Component | Function |
|-------|-----------|----------|
| Data | Backend API | Current prices, stock list, news items w/ sentiment |
| Storage | Supabase Postgres + pgvector | Persist embeddings + metadata |
| Embeddings | OpenAI text-embedding-3-small (1536 dims) | Dense vectors for semantic similarity |
| Retrieval | match_news_embeddings() (SQL RPC) | Filter by symbol/date + cosine ranking |
| Tooling | FastAPI MCP server | Validated structured tool calls |
| Orchestration | explain_price_change tool | Multi-step aggregation in one call |
| Analytics | Correlation tools | Sentiment ↔ price statistical relationship |

## 4. Data Model (news_embeddings)
Fields: news_id (unique), symbol, title, content_preview, published_at (TZ), sentiment, sentiment_score, source, url, embedding vector(1536), created_at/updated_at.
Indexes: symbol, published_at, sentiment + HNSW on embedding for fast approximate similarity.

## 5. Tool Inventory (MCP)
1. get_stock_summary(symbol, period_days)
2. get_historical_prices(symbol, start_date, end_date, aggregation_period)
3. get_news_sentiment(symbol, start_date, end_date, top_n, sentiment_filter?)
4. get_sentiment_aggregate(symbol, start_date, end_date)
5. get_rag_evidence(symbol, start_date, end_date, query_text, top_k)
6. calculate_correlation(series_a, series_b)
7. calculate_sentiment_price_correlation(price_changes, sentiment_scores, symbol)
8. explain_price_change(symbol, start_date, end_date)  (orchestrator)
9. get_rag_stats()

## 6. Request Lifecycle (example: explain_price_change)
1. LLM sends MCP tool call: { name: "explain_price_change", arguments: { symbol, start_date, end_date } }
2. Server validates payload → computes period_days → calls sub-tools:
   - get_stock_summary → price change %, volatility (if stock data available)
   - get_historical_prices → time series for correlation
   - get_news_sentiment + get_sentiment_aggregate → narrative + stats
   - get_rag_evidence → semantic evidence docs (ranked, similarity)
   - calculate_sentiment_price_correlation → coefficient + interpretation
3. Returns structured JSON (including per-tool status flags).
4. LLM prompt composes explanation with citations.

## 7. RAG Retrieval Mechanics
- Query text embedded → vector q
- RPC function filters rows by symbol/date range → computes cosine similarity (1 - <=>) → threshold + top_k limit.
- Post-processing adds qualitative bucket: EXCELLENT/HIGH/GOOD/MODERATE/LOW.
- Returned docs used directly as cite-able context for LLM (avoid hallucination).

## 8. Error & Status Handling
Each sub-call may return {"error": "..."}; orchestrator records tool_status map: ok | error.
422 errors typically mean payload schema mismatch (need { name, arguments }). 401 = bad API key. Missing stock summary now due to symbol format mismatch (e.g., backend uses HDFCBANK vs news using HDFCBANK.NS).

## 9. Performance Considerations (Fast Path)
- Embeddings: Batch future ingestions to reduce per-request OpenAI overhead.
- Retrieval: HNSW index chosen for speed; tune m (graph complexity) and ef (search breadth) for latency vs recall.
- Cache: Short TTL (30–120s) for stock summaries & historical prices to dampen repeat tool calls.
- Pre-aggregation: Daily sentiment averages & price returns (store separately) → reduces correlation prep costs.
- Payload size: Limit top_k (6–10) to keep LLM context efficient.
- Network: Reuse HTTP sessions for Supabase + backend (requests.Session) to reduce TLS overhead.

## 10. Quality & Observability
- Logs: Each tool invocation with args + success/error → logs/mcp_server_*.log
- Stats: get_rag_stats shows embedding coverage; monitor growth vs recall success.
- Evaluation: Periodically sample answers and verify each cited source appears verbatim in tool output.
- Guardrails: Force LLM to cite explicit tool fields (title, published_at, source) only.

## 11. Symbol Normalization (Current Gap)
Issue: Price tools expect raw symbol; news + embeddings may include suffix (.NS). Action: Introduce normalization layer:
- Input symbol → variants [SYMBOL, SYMBOL.NS]
- Query backend with canonical form, query RAG with both; merge.

## 12. Extensibility Hooks
- Add long-form transcript chunking (chunk_size=1000 w/ overlap=100) for earnings calls.
- Add sentiment trend tool (returns rolling 7-day averages precomputed).
- Add anomaly detector (price move vs historical volatility percentile).
- Switch to streaming LLM completion with incremental evidence insertion.

## 13. Security & Access Control
- Single API key (X-API-Key) for MCP server; rotate regularly.
- Row Level Security on Supabase enforcing read policies; service_role used for ingestion.
- Potential enhancement: scoped tool permissions per client app.

## 14. Minimal Study Checklist
[ ] Understand vector insertion (scripts/ingest_historical.py)
[ ] Trace orchestrator flow (server/tools/orchestrator.py)
[ ] Inspect RPC function match_news_embeddings in setup_vectordb.sql
[ ] Run get_rag_evidence manually, examine similarity scores
[ ] Normalize symbols to fix missing price data
[ ] Benchmark latency (mean tool call time) and set targets

## 15. Core Design Principles
- Deterministic tool outputs over free-form scraping
- Separation of retrieval (RAG) and computation (correlation, volatility)
- Evidence-first answer synthesis (numerical facts precede narrative)
- Modular tool schema for easier LLM function-calling alignment

## 16. Quick Glossary
- RAG: Retrieval Augmented Generation—LLM uses external factual context fetched at query time.
- Embedding: Numeric vector representation enabling semantic similarity search.
- HNSW: Hierarchical Navigable Small World graph-based ANN index for fast approximate nearest neighbor.
- Correlation Coefficient (Pearson): Linear relationship strength between two series (−1 to +1).
- Volatility: Standard deviation of returns; used to contextualize price movement magnitude.

## 17. Next High-Impact Improvements (Fast Wins)
1. Symbol normalization layer → enables full orchestrator success.
2. Precompute daily sentiment & returns table → faster correlation tool.
3. Add caching decorator for stable endpoints.
4. Implement retry/backoff for transient HTTP failures.
5. Add tool: get_sentiment_trend(symbol, days) for sparkline insights.

## 18. How To Experiment Quickly
```powershell
# Check health
curl http://localhost:8001/health

# Simple RAG stats
curl -X POST http://localhost:8001/call -H "X-API-Key: stockify-mcp-2025" -H "Content-Type: application/json" -d '{"name":"get_rag_stats","arguments":{}}'

# News sentiment
curl -X POST http://localhost:8001/call -H "X-API-Key: stockify-mcp-2025" -H "Content-Type: application/json" -d '{"name":"get_news_sentiment","arguments":{"symbol":"HDFCBANK","start_date":"2025-11-10","end_date":"2025-11-17","top_n":5}}'
```

---
Study this file alongside the code in `server/tools/` and the SQL in `scripts/setup_vectordb.sql` to connect concepts to implementation.
