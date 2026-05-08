# Sentimatix MCP Server

[![smithery badge](https://smithery.ai/badge/rishavdutta-kgp/sentimatix)](https://smithery.ai/servers/rishavdutta-kgp/sentimatix)

Real-time Indian stock market intelligence via the **Model Context Protocol (MCP)**. Plug Sentimatix directly into Claude Desktop, Cursor, or any MCP-compatible AI agent to get live NSE/BSE sentiment, news, and technical analysis.

## 🏗️ Architecture

```
User Query → Claude/AI Agent → MCP Server → Tools
                                   ↓
                              ┌─────────────────────┐
                              │ News Sentiment API  │ ← Sentimatix /api/v1/news
                              │ Stock Price API     │ ← Sentimatix /api/v1/stocks
                              │ Sector Sentiment    │ ← Sentimatix /api/v1/sentiment
                              │ RAG Evidence        │ ← Supabase Vector DB
                              └─────────────────────┘
                                   ↓
                              Synthesized Market Intelligence
```

## 🛠️ Available Tools (10 total)

| Tool | Description | Example |
|------|-------------|---------|
| `explain_price_change` | **Orchestrator** — explains why a stock moved using price, news + sentiment | `(RELIANCE, 7 days)` |
| `analyze_stock_enhanced` | Deep single-stock research report | `(HDFCBANK, detailed)` |
| `compare_stocks` | Side-by-side comparison of two NSE stocks | `(TCS vs INFY)` |
| `get_stock_summary` | Price metrics: change%, high, low, volume | `(TATAMOTORS, 7 days)` |
| `get_historical_prices` | Daily OHLCV time-series data | `(SBIN, 2024-01-01, 2024-03-01)` |
| `get_news_sentiment` | News articles with NLP sentiment scores | `(ZOMATO, last 7 days)` |
| `get_sentiment_aggregate` | Aggregated sentiment stats for a period | `(ADANIENT, 30 days)` |
| `get_technical_analysis` | RSI, MACD, Bollinger Bands, support/resistance | `(ITC, 90 days)` |
| `calculate_correlation` | Pearson correlation between two NSE stocks | `(RELIANCE, TCS)` |
| `get_rag_evidence` | Semantic search over the news corpus | `(INFY, "earnings beat")` |

## 🚀 Quick Start (Claude Desktop)

Add this to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "sentimatix": {
      "command": "python",
      "args": ["path/to/apps/mcp/mcp_stdio.py"],
      "env": {
        "BACKEND_API_URL": "https://sentimatix-production.up.railway.app/api"
      }
    }
  }
}
```

No API key is required for the default free tier.

## 📊 Example Query Flow

**User:** "Why did Reliance drop in the last 7 days?"

**MCP Workflow:**
1. ✅ `get_stock_summary("RELIANCE", 7)` → `-3.1% decline`
2. ✅ `get_news_sentiment("RELIANCE", ...)` → `12 news items, avg sentiment: -0.4`
3. ✅ `get_rag_evidence("RELIANCE", "price drop reasons")` → `5 relevant articles`
4. ✅ `get_technical_analysis("RELIANCE")` → `RSI: 38 (Oversold), MACD: Bearish`
5. 🤖 **LLM Synthesis:**

```
RELIANCE declined 3.1% (₹2,850 → ₹2,762) over the last 7 days.

Top Reasons (with evidence):
1. Weak Q4 refining margins — reported by Economic Times (sentiment: -0.5)
2. Sector-wide FII selling in Oil & Gas — MoneyControl (sentiment: -0.3)
3. RSI at 38 confirms oversold territory; key support at ₹2,740

Confidence: HIGH
```

## 🔧 Environment Variables

```bash
BACKEND_API_URL=https://sentimatix-production.up.railway.app/api
SUPABASE_URL=https://your-project.supabase.co       # For RAG features
SUPABASE_KEY=your_anon_key                           # For RAG features
OPENAI_API_KEY=your_openai_key                       # For AI synthesis
```

## 📚 Full Documentation

- [Connection Guide](MCP_CONNECTION_GUIDE.md) — Claude Desktop, Cursor setup
- [Quick Start](QUICKSTART.md) — Step-by-step installation
- [REST API Docs](https://sentimatix-production.up.railway.app/docs) — Full OpenAPI reference
