# Sentimatix

[![smithery badge](https://smithery.ai/badge/rishavdutta-kgp/sentimatix)](https://smithery.ai/servers/rishavdutta-kgp/sentimatix)

**Real-time Indian stock market sentiment intelligence for AI agents and retail traders.**

Sentimatix provides live NSE/BSE news sentiment, aggregated stock & sector signals, and a Model Context Protocol (MCP) server that plugs directly into Claude, Cursor, and other AI agents.

---

## 🧩 What's Inside

| App | Description |
|-----|-------------|
| [`apps/api`](apps/api) | FastAPI REST API — news, sentiment, entities, sector signals |
| [`apps/mcp`](apps/mcp) | MCP Server — 10 tools for AI agents (Claude Desktop, Cursor) |
| [`apps/dashboard`](apps/dashboard) | Next.js developer portal & API key management |
| [`apps/streamlit`](apps/streamlit) | Streamlit analytics dashboard |
| [`workers/`](workers) | Background NLP pipeline — sentiment scoring, stock price sync |

---

## ⚡ Quick Start — MCP (Claude Desktop)

Add to your `claude_desktop_config.json`:

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

No API key required for the free tier.

---

## 🛠️ MCP Tools

| Tool | Description |
|------|-------------|
| `explain_price_change` | Why did a stock move? News + price + technicals |
| `analyze_stock_enhanced` | Deep single-stock research report |
| `compare_stocks` | Side-by-side comparison of two NSE stocks |
| `get_news_sentiment` | Articles with NLP sentiment scores |
| `get_sentiment_aggregate` | Aggregated sentiment over 7d / 30d |
| `get_technical_analysis` | RSI, MACD, Bollinger Bands |
| `calculate_correlation` | Pearson correlation between two stocks |
| `get_rag_evidence` | Semantic search over the news corpus |

Full docs: [`apps/mcp/README.md`](apps/mcp/README.md)

---

## 📡 REST API

Base URL: `https://sentimatix-production.up.railway.app`

| Endpoint | Description |
|----------|-------------|
| `GET /api/v1/news` | Financial news with sentiment labels |
| `GET /api/v1/entities` | Directory of all supported NSE stocks |
| `GET /api/v1/sentiment` | Aggregated sentiment scores per stock |
| `GET /api/v1/sentiment/sectors` | Sector-level sentiment heatmap |

Interactive docs: [https://sentimatix-production.up.railway.app/docs](https://sentimatix-production.up.railway.app/docs)

---

## 🔗 Links

- [Smithery Registry](https://smithery.ai/servers/rishavdutta-kgp/sentimatix)
- [API Reference](https://sentimatix-production.up.railway.app/docs)
- [Developer Portal](https://sentimatix-production.up.railway.app)
