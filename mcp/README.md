# Stockify MCP + RAG System

Complete implementation of **Model Context Protocol (MCP)** with **Retrieval-Augmented Generation (RAG)** for intelligent stock analysis.

## 🏗️ Architecture Overview

```
User Query → LLM (ChatGPT/Claude) → MCP Server → Tools
                                         ↓
                                    ┌────────────────┐
                                    │ RAG Pipeline   │ ← Vector DB (Supabase)
                                    │ Stock API      │ ← /api/stocks
                                    │ News API       │ ← /api/news
                                    │ Price API      │ ← /api/stocks/{id}
                                    └────────────────┘
                                         ↓
                                    Synthesized Answer + Citations
```

## 📁 Project Structure

```
mcp/
├── server/                    # MCP Server (FastAPI)
│   ├── main.py               # MCP server entry point
│   ├── tools/                # Tool implementations
│   │   ├── stock_tools.py    # Stock price & summary tools
│   │   ├── news_tools.py     # News & sentiment tools
│   │   ├── rag_tools.py      # RAG evidence retrieval
│   │   └── correlation.py    # Correlation calculations
│   ├── config.py             # Configuration
│   └── prompts.py            # LLM prompt templates
├── rag/                      # RAG Pipeline
│   ├── embeddings.py         # Generate embeddings
│   ├── vectordb.py           # Vector DB operations (Supabase)
│   ├── ingestion.py          # Ingest news → embeddings
│   └── retrieval.py          # Semantic search
├── client/                   # Client examples
│   ├── chat_interface.py     # Example chat client
│   └── examples.py           # Usage examples
├── scripts/                  # Utilities
│   ├── setup_vectordb.sql    # SQL to setup vector extension
│   └── ingest_historical.py  # One-time historical ingestion
├── requirements.txt
└── .env.example
```

## 🚀 Quick Start

### 1. Install Dependencies
```bash
cd mcp
pip install -r requirements.txt
```

### 2. Setup Environment
```bash
cp .env.example .env
# Edit .env with your credentials
```

### 3. Setup Vector Database
```bash
# Run SQL setup in Supabase
psql -h your-db -f scripts/setup_vectordb.sql
```

### 4. Ingest Historical Data
```bash
python scripts/ingest_historical.py
```

### 5. Start MCP Server
```bash
python server/main.py
```

### 6. Test with Client
```bash
python client/examples.py
```

## 🛠️ Available Tools

| Tool | Description | Example |
|------|-------------|---------|
| `get_stock_summary` | Price metrics for period | `(AAPL, 7 days)` |
| `get_historical_prices` | Time-series price data | `(AAPL, 2025-11-01, 2025-11-14)` |
| `get_news_sentiment` | News + sentiment for symbol | `(AAPL, last 7 days)` |
| `get_rag_evidence` | Semantic search historical context | `(AAPL, "earnings miss")` |
| `calculate_correlation` | Correlate sentiment vs price | `(AAPL sentiment, AAPL price)` |
| `get_technical_analysis` | Indicators (RSI, MACD, BB) | `(AAPL, 100 days)` |
| `explain_price_change` | Full analysis orchestrator | `(AAPL, last 7 days)` |

## 📊 Example Query Flow

**User:** "Why did AAPL drop in the last 7 days?"

**MCP Workflow:**
1. ✅ `get_stock_summary("AAPL", 7)` → `-4.2% decline`
2. ✅ `get_historical_prices("AAPL", ...)` → `Chart data`
3. ✅ `get_news_sentiment("AAPL", ...)` → `10 news items, avg sentiment: -0.3`
4. ✅ `get_rag_evidence("AAPL", "price drop reasons")` → `6 relevant articles`
5. 🤖 **LLM Synthesis:**

```
AAPL declined 4.2% ($180 → $172) between Nov 7-14, 2025.

Top 3 Reasons (with evidence):
1. iPhone sales miss in China - "Apple Q4 guidance below estimates" 
   (Bloomberg, Nov 10, sentiment: -0.6) — HIGH IMPACT
   
2. Sector-wide tech selloff after Fed minutes 
   (Reuters, Nov 12, sentiment: -0.4) — MEDIUM IMPACT
   
3. Analyst downgrade from Morgan Stanley 
   (MarketWatch, Nov 13, sentiment: -0.5) — MEDIUM IMPACT

Confidence: HIGH
Supporting correlation: Price changes correlate -0.72 with sentiment

Sources:
- [Bloomberg] Apple Q4 Earnings Miss... (2025-11-10)
- [Reuters] Tech stocks tumble as... (2025-11-12)
- [MarketWatch] Morgan Stanley cuts... (2025-11-13)
```

## 🔧 Configuration

For detailed configuration instructions, see [Configuration Guide](docs/CONFIGURATION.md).

Quick setup - edit your `.env` file:
```bash
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your_anon_key_here
SUPABASE_SERVICE_KEY=your_service_role_key_here  # Required for RAG
OPENAI_API_KEY=your_openai_api_key_here
BACKEND_API_URL=http://localhost:8000/api
```

**⚠️ Important**: The RAG system requires a valid `SUPABASE_SERVICE_KEY` to function properly.

## 📈 Monitoring

Logs are stored in `logs/mcp_server_YYYYMMDD.log`

Monitor:
- Tool call frequency
- RAG retrieval quality (relevance scores)
- API latency
- LLM token usage

## 🔐 Security

- API key required for all tool calls
- Rate limiting: 100 req/min per user
- Input validation on all parameters
- Sandbox execution for calculations

## 📚 Documentation

See individual module documentation:
- [Configuration Guide](docs/CONFIGURATION.md) - Complete setup and troubleshooting
- [RAG Pipeline](rag/README.md) - Vector database and semantic search
- [MCP Server](server/README.md) - Server implementation details
- [Client Usage](client/README.md) - Client examples and integration
