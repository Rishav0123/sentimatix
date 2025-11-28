# MCP System - Quick Start Guide

## Setup Instructions

### 1. Install Dependencies

```bash
cd mcp
pip install -r requirements.txt
```

### 2. Setup Environment Variables

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Required variables:
- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_KEY` - Your Supabase service role key
- `OPENAI_API_KEY` - Your OpenAI API key
- `BACKEND_API_URL` - Your backend API URL (e.g., http://localhost:8000/api)
- `MCP_API_KEY` - Generate a secure key for MCP server authentication

### 3. Setup Vector Database

Run the SQL script in your Supabase SQL Editor:

```bash
# Open scripts/setup_vectordb.sql and run it in Supabase
```

This will:
- Enable pgvector extension
- Create `news_embeddings` table
- Add HNSW index for fast similarity search
- Create helper functions

### 4. Ingest Historical Data

Populate the vector database with your existing news:

```bash
python scripts/ingest_historical.py
```

This will:
- Fetch news from your `/api/news` endpoint
- Generate embeddings for each article
- Store embeddings in Supabase
- Log progress to `logs/ingestion_*.log`

**Note:** This may take time depending on the number of articles. The script includes rate limiting for OpenAI API.

### 5. Start MCP Server

```bash
python server/main.py
```

Server will start on `http://localhost:8001`

### 6. Test the Server

#### Option A: Run Examples

```bash
python client/examples.py
```

This provides 7 example queries demonstrating all tools.

#### Option B: Interactive Chat

```bash
python client/chat_interface.py
```

Ask questions in natural language:
- "Why did AAPL drop in the last week?"
- "What's the sentiment for TSLA?"
- "Find news about NVDA earnings"

#### Option C: Direct API Calls

```bash
curl -X POST http://localhost:8001/call \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "explain_price_change",
    "parameters": {
      "symbol": "AAPL",
      "start_date": "2024-01-01",
      "end_date": "2024-01-07"
    }
  }'
```

## Available Tools

### 1. **explain_price_change** (Orchestrator - RECOMMENDED)

Comprehensive analysis combining all tools:

```json
{
  "tool_name": "explain_price_change",
  "parameters": {
    "symbol": "AAPL",
    "start_date": "2024-01-01",
    "end_date": "2024-01-07"
  }
}
```

Returns:
- Stock summary (price changes, volatility)
- Historical prices
- News sentiment (individual + aggregate)
- RAG evidence (semantic search)
- Sentiment-price correlation

### 2. **get_stock_summary**

Get stock performance metrics:

```json
{
  "tool_name": "get_stock_summary",
  "parameters": {
    "symbol": "TSLA",
    "period_days": 30
  }
}
```

### 3. **get_historical_prices**

Get time-series price data:

```json
{
  "tool_name": "get_historical_prices",
  "parameters": {
    "symbol": "TSLA",
    "start_date": "2024-01-01",
    "end_date": "2024-01-31",
    "aggregation_period": "1d"
  }
}
```

### 4. **get_news_sentiment**

Get news articles with sentiment:

```json
{
  "tool_name": "get_news_sentiment",
  "parameters": {
    "symbol": "NVDA",
    "start_date": "2024-01-01",
    "end_date": "2024-01-07",
    "top_n": 5,
    "sentiment_filter": null
  }
}
```

### 5. **get_sentiment_aggregate**

Get aggregated sentiment stats:

```json
{
  "tool_name": "get_sentiment_aggregate",
  "parameters": {
    "symbol": "NVDA",
    "start_date": "2024-01-01",
    "end_date": "2024-01-07"
  }
}
```

### 6. **get_rag_evidence**

Semantic search for relevant news:

```json
{
  "tool_name": "get_rag_evidence",
  "parameters": {
    "symbol": "GOOGL",
    "start_date": "2024-01-01",
    "end_date": "2024-01-31",
    "query_text": "earnings report revenue growth",
    "top_k": 5
  }
}
```

### 7. **calculate_sentiment_price_correlation**

Analyze correlation between sentiment and price:

```json
{
  "tool_name": "calculate_sentiment_price_correlation",
  "parameters": {
    "price_changes": [1.5, -0.8, 2.3],
    "sentiment_scores": [0.7, -0.4, 0.8],
    "symbol": "MSFT"
  }
}
```

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         LLM (GPT-4, etc.)                       │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                     MCP Server (FastAPI)                         │
│                    POST /call - Tool Routing                     │
└─────────────────────────┬───────────────────────────────────────┘
                          │
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
    ┌─────────┐    ┌──────────┐    ┌──────────┐
    │  Stock  │    │   News   │    │   RAG    │
    │  Tools  │    │  Tools   │    │  Tools   │
    └────┬────┘    └────┬─────┘    └────┬─────┘
         │              │                │
         ▼              ▼                ▼
    ┌─────────────────────────────────────────┐
    │         Backend API (FastAPI)           │
    │  /api/stocks  /api/news  /api/price     │
    └─────────────────────────────────────────┘
                          │
                          ▼
              ┌───────────────────────┐
              │  Supabase PostgreSQL  │
              │  + pgvector extension │
              └───────────────────────┘
```

## Monitoring

### Check Server Health

```bash
curl http://localhost:8001/health
```

Returns:
- Backend API status
- Vector DB status
- RAG system status

### View Logs

```bash
# MCP server logs
tail -f logs/mcp_server_*.log

# Ingestion logs
tail -f logs/ingestion_*.log
```

### Database Statistics

```bash
curl -X POST http://localhost:8001/call \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"tool_name": "get_rag_stats", "parameters": {}}'
```

## Troubleshooting

### Server won't start

1. Check environment variables in `.env`
2. Verify Supabase connection: `python -c "from rag.vectordb import get_vector_db; get_vector_db()"`
3. Check logs in `logs/mcp_server_*.log`

### No RAG results

1. Ensure vector DB is populated: `python scripts/ingest_historical.py`
2. Check Supabase SQL Editor: `SELECT COUNT(*) FROM news_embeddings;`
3. Verify OpenAI API key is valid

### Backend API errors

1. Ensure backend is running on `BACKEND_API_URL`
2. Test endpoints manually: `curl http://localhost:8000/api/stocks`
3. Check backend API key if required

### Low-quality embeddings

1. Ensure news articles have substantive content (not just titles)
2. Check `prepare_text_for_embedding()` in `rag/embeddings.py`
3. Consider using different embedding model (currently: text-embedding-3-small)

## Next Steps

1. **Connect to LLM**: Use tools in your LLM application (ChatGPT, Claude, etc.)
2. **Customize Prompts**: Modify `server/prompts.py` for your use case
3. **Add Tools**: Create new tools in `server/tools/`
4. **Tune RAG**: Adjust `RAG_TOP_K`, similarity threshold in `config.py`
5. **Scale**: Configure rate limiting, caching, multi-worker deployment

## Production Deployment

### Security

- Use strong `MCP_API_KEY`
- Enable HTTPS
- Add rate limiting (FastAPI middleware)
- Use environment-specific configs

### Performance

- Increase uvicorn workers: `uvicorn server.main:app --workers 4`
- Configure pgvector HNSW index parameters (m, ef_construction)
- Implement caching for frequent queries
- Use async/await throughout

### Monitoring

- Add structured logging (JSON)
- Integrate with monitoring tools (Datadog, Sentry)
- Track tool usage metrics
- Monitor OpenAI API costs

## Support

For issues or questions:
1. Check logs in `logs/` directory
2. Review documentation in `docs/`
3. Test individual components using `client/examples.py`
