# Sentimatix MCP Connection Guide

The Sentimatix MCP server (`mcp_stdio.py`) speaks the official Model Context Protocol
over **stdio** (for desktop clients) or **SSE/HTTP** (for web clients).

---

## ✅ Status

| Check | Result |
|---|---|
| MCP SDK installed | `mcp 1.25.0` ✅ |
| Server import | OK ✅ |
| SSE server boots | `http://0.0.0.0:8003/sse` ✅ |
| stdio handshake | `initialize` → `protocolVersion 2024-11-05` ✅ |
| Tools registered | 13 tools ✅ |

---

## 1. Claude Desktop (stdio — recommended)

The config has already been written to:
```
C:\Users\risha\AppData\Roaming\Claude\claude_desktop_config.json
```

**Steps:**
1. Install Claude Desktop from https://claude.ai/download
2. Quit Claude Desktop completely (system tray → Quit)
3. Reopen Claude Desktop
4. In any chat, type: `What tools do you have?`  
   → Claude will list all 13 Sentimatix tools

**To manually update the config path later:**
```json
{
  "mcpServers": {
    "sentimatix": {
      "command": "python",
      "args": ["d:/sentimatix/apps/apps/mcp/mcp_stdio.py"],
      "env": {
        "BACKEND_API_URL": "https://sentimatix-production.up.railway.app/api",
        "LOG_LEVEL": "WARNING"
      }
    }
  }
}
```

---

## 2. SSE / HTTP Mode (web clients, n8n, Glama)

```bash
# Start the SSE server
cd d:\sentimatix\apps\mcp
python mcp_stdio.py --sse

# Or on a custom port
python mcp_stdio.py --sse --port=8004
```

The server will listen at:
- **SSE endpoint:** `http://localhost:8003/sse`
- **POST endpoint:** `http://localhost:8003/messages/`

---

## 3. Tools Available (13 total)

| Tool | Category | Description |
|---|---|---|
| `explain_price_change` | 🎯 Orchestrator | Why did a stock move? (all-in-one) |
| `analyze_stock_enhanced` | 📊 Analysis | Deep single-stock research |
| `compare_stocks` | 📊 Analysis | Side-by-side comparison |
| `get_stock_summary` | 💹 Price | Price metrics for a period |
| `get_historical_prices` | 💹 Price | Daily OHLCV time series |
| `get_news_sentiment` | 📰 News | Articles + NLP sentiment scores |
| `get_sentiment_aggregate` | 📰 News | Avg sentiment, +/- counts |
| `get_technical_analysis` | 📈 Technical | RSI, MACD, Bollinger Bands |
| `calculate_correlation` | 🔗 Correlation | Pearson correlation between 2 stocks |
| `calculate_sentiment_price_correlation` | 🔗 Correlation | Sentiment vs price signal |
| `get_rag_evidence` | 🔍 RAG | Vector search over news corpus |
| `get_rag_stats` | 🔍 RAG | DB stats (doc count, index info) |

---

## 4. Submit to Directories

### Smithery.ai
1. Push `mcp_stdio.py` + `smithery.yaml` to a public GitHub repo
2. Go to https://smithery.ai/new
3. Paste your GitHub URL
4. The `smithery.yaml` is already configured

### PulseMCP
1. Go to https://pulsemcp.com/submit
2. Fill in:
   - **Name:** Sentimatix — Indian Stock Sentiment MCP
   - **GitHub:** your repo URL
   - **Description:** Real-time NSE/BSE stock sentiment, news analysis and technical indicators via MCP. 13 tools covering price, news, RAG and correlation.

### Glama
1. Go to https://glama.ai/apps/mcp/servers
2. Click "Submit a server"
3. Use the SSE URL when deployed: `https://your-domain.com/sse`

---

## 5. Quick Test (command line)

```python
# test_mcp.py — run from d:\sentimatix\apps\apps\mcp\
import subprocess, json, time

proc = subprocess.Popen(
    ['python', 'mcp_stdio.py'],
    stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL
)

msg = json.dumps({
    "jsonrpc": "2.0", "id": 1, "method": "initialize",
    "params": {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {"name": "test", "version": "1.0"}
    }
})
proc.stdin.write((msg + '\n').encode())
proc.stdin.flush()
time.sleep(2)
proc.stdin.close()
print(proc.stdout.read(2048).decode())
proc.terminate()
```

**Expected output:**
```json
{"jsonrpc":"2.0","id":1,"result":{"protocolVersion":"2024-11-05","capabilities":{"tools":{}},"serverInfo":{"name":"sentimatix","version":"1.25.0"}}}
```

---

## 6. File Structure

```
d:\sentimatix\apps\apps\mcp\
├── mcp_stdio.py              ← TRUE MCP server (stdio + SSE) ✅ NEW
├── smithery.yaml             ← Smithery.ai directory config  ✅ NEW
├── claude_desktop_config.json← Copy of Claude Desktop config ✅ NEW
├── run_server.py             ← Old FastAPI HTTP server (keep for web portal)
└── server/
    └── tools/
        ├── orchestrator.py
        ├── stock_tools.py
        ├── news_tools.py
        ├── technical_analysis.py
        ├── enhanced_analysis.py
        ├── correlation.py
        └── rag_tools.py
```
