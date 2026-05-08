"""
Sentimatix MCP Server (stdio transport)
========================================
A true Model Context Protocol server using the official Anthropic MCP SDK.

This server speaks MCP JSON-RPC over stdio, making it compatible with:
  - Claude Desktop (claude_desktop_config.json)
  - Smithery.ai, PulseMCP, Glama directories
  - Any MCP-compliant AI agent

Usage:
    python mcp_stdio.py           # stdio mode (default, for clients)
    python mcp_stdio.py --sse     # SSE/HTTP mode on port 8003

Client config (claude_desktop_config.json):
{
  "mcpServers": {
    "sentimatix": {
      "command": "python",
      "args": ["d:/sentimatix/apps/apps/mcp/mcp_stdio.py"],
      "env": {}
    }
  }
}
"""

import sys
import os
import json
import asyncio
import logging
from pathlib import Path
from typing import Any, Optional

# ── Path bootstrap ──────────────────────────────────────────────────────────
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

# ── Load .env early so config.py can read it ────────────────────────────────
from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

# ── Suppress noisy loggers when running in stdio mode ───────────────────────
# MCP clients communicate over stdout; any stray print/log to stdout breaks it.
logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(ROOT / "logs" / "mcp_stdio.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger("sentimatix_mcp")

# ── MCP SDK ─────────────────────────────────────────────────────────────────
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

# ── Tool imports ─────────────────────────────────────────────────────────────
from server.tools.stock_tools import get_stock_summary, get_historical_prices
from server.tools.news_tools import get_news_sentiment, get_sentiment_aggregate
from server.tools.rag_tools import get_rag_evidence, get_rag_stats
from server.tools.correlation import calculate_correlation, calculate_sentiment_price_correlation
from server.tools.orchestrator import explain_price_change
from server.tools.enhanced_analysis import analyze_stock_enhanced, compare_stocks
from server.tools.technical_analysis import get_technical_analysis

# ── Create MCP server instance ───────────────────────────────────────────────
mcp = Server("sentimatix")

# ═══════════════════════════════════════════════════════════════════════════
# TOOL DEFINITIONS
# ═══════════════════════════════════════════════════════════════════════════

@mcp.list_tools()
async def list_tools() -> list[types.Tool]:
    """Return the full list of tools exposed by this server."""
    return [
        # ── Orchestrator ────────────────────────────────────────────────
        types.Tool(
            name="explain_price_change",
            description=(
                "HIGH-LEVEL ORCHESTRATOR for Indian stocks (NSE/BSE). "
                "Automatically gathers price data, news sentiment, RAG evidence, "
                "correlation and technical analysis to explain WHY a stock price changed. "
                "Use this as your first tool for any 'why did X change?' question. "
                "Symbols: use NSE tickers like RELIANCE, TCS, HDFCBANK, INFY, SBIN."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {"type": "string", "description": "NSE stock symbol e.g. TCS, RELIANCE, HDFCBANK"},
                    "start_date": {"type": "string", "description": "Start date YYYY-MM-DD"},
                    "end_date": {"type": "string", "description": "End date YYYY-MM-DD"},
                },
                "required": ["symbol", "start_date", "end_date"],
            },
        ),
        # ── Enhanced Analysis ────────────────────────────────────────────
        types.Tool(
            name="analyze_stock_enhanced",
            description=(
                "Deep single-stock analysis with AI-generated insights, technical signals, "
                "sentiment trends and key events. Good for detailed research reports."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {"type": "string", "description": "NSE stock symbol"},
                    "start_date": {"type": "string", "description": "Start date YYYY-MM-DD"},
                    "end_date": {"type": "string", "description": "End date YYYY-MM-DD"},
                    "analysis_type": {
                        "type": "string",
                        "enum": ["quick", "detailed", "comprehensive"],
                        "default": "detailed",
                        "description": "Depth of analysis",
                    },
                },
                "required": ["symbol", "start_date", "end_date"],
            },
        ),
        types.Tool(
            name="compare_stocks",
            description=(
                "Compare two NSE stocks side-by-side: price performance, sentiment, "
                "technical indicators and relative strength."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol1": {"type": "string", "description": "First NSE stock symbol"},
                    "symbol2": {"type": "string", "description": "Second NSE stock symbol"},
                    "start_date": {"type": "string", "description": "Start date YYYY-MM-DD"},
                    "end_date": {"type": "string", "description": "End date YYYY-MM-DD"},
                },
                "required": ["symbol1", "symbol2", "start_date", "end_date"],
            },
        ),
        # ── Stock Price Tools ────────────────────────────────────────────
        types.Tool(
            name="get_stock_summary",
            description=(
                "Get price summary for an NSE stock over a period: "
                "current price, change%, high, low, average volume, volatility."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {"type": "string", "description": "NSE stock symbol e.g. RELIANCE"},
                    "period_days": {
                        "type": "integer",
                        "default": 7,
                        "minimum": 1,
                        "maximum": 365,
                        "description": "Days to look back (default 7)",
                    },
                },
                "required": ["symbol"],
            },
        ),
        types.Tool(
            name="get_historical_prices",
            description="Get daily OHLCV time-series data for charting and analysis.",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {"type": "string", "description": "NSE stock symbol"},
                    "start_date": {"type": "string", "description": "Start date YYYY-MM-DD"},
                    "end_date": {"type": "string", "description": "End date YYYY-MM-DD"},
                    "aggregation_period": {
                        "type": "integer",
                        "enum": [1, 7, 15, 30],
                        "default": 1,
                        "description": "1=daily, 7=weekly, 30=monthly",
                    },
                },
                "required": ["symbol", "start_date", "end_date"],
            },
        ),
        # ── News & Sentiment ─────────────────────────────────────────────
        types.Tool(
            name="get_news_sentiment",
            description=(
                "Fetch news articles with NLP sentiment scores for an Indian stock. "
                "Returns headlines, source, published date, sentiment label and score."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {"type": "string", "description": "NSE stock symbol"},
                    "start_date": {"type": "string", "description": "Start date YYYY-MM-DD"},
                    "end_date": {"type": "string", "description": "End date YYYY-MM-DD"},
                    "top_n": {
                        "type": "integer",
                        "default": 10,
                        "minimum": 1,
                        "maximum": 50,
                        "description": "Max articles to return",
                    },
                    "sentiment_filter": {
                        "type": "string",
                        "enum": ["positive", "negative", "neutral"],
                        "description": "Filter by sentiment label (optional)",
                    },
                },
                "required": ["symbol", "start_date", "end_date"],
            },
        ),
        types.Tool(
            name="get_sentiment_aggregate",
            description=(
                "Get aggregated sentiment stats for a period: average score, "
                "positive/negative/neutral counts and percentage breakdown."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {"type": "string", "description": "NSE stock symbol"},
                    "start_date": {"type": "string", "description": "Start date YYYY-MM-DD"},
                    "end_date": {"type": "string", "description": "End date YYYY-MM-DD"},
                },
                "required": ["symbol", "start_date", "end_date"],
            },
        ),
        # ── Technical Analysis ───────────────────────────────────────────
        types.Tool(
            name="get_technical_analysis",
            description=(
                "Compute technical indicators for an NSE stock: RSI, MACD, "
                "Bollinger Bands, moving averages, support/resistance levels and signals."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {"type": "string", "description": "NSE stock symbol"},
                    "period_days": {
                        "type": "integer",
                        "default": 90,
                        "description": "Days of history for indicator calculation",
                    },
                },
                "required": ["symbol"],
            },
        ),
        # ── Correlation ──────────────────────────────────────────────────
        types.Tool(
            name="calculate_correlation",
            description="Calculate Pearson correlation between two NSE stocks over a period.",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol1": {"type": "string", "description": "First NSE symbol"},
                    "symbol2": {"type": "string", "description": "Second NSE symbol"},
                    "start_date": {"type": "string", "description": "Start date YYYY-MM-DD"},
                    "end_date": {"type": "string", "description": "End date YYYY-MM-DD"},
                },
                "required": ["symbol1", "symbol2", "start_date", "end_date"],
            },
        ),
        types.Tool(
            name="calculate_sentiment_price_correlation",
            description=(
                "Measure how strongly news sentiment correlates with price movement "
                "for an NSE stock — useful for signal research."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {"type": "string", "description": "NSE stock symbol"},
                    "start_date": {"type": "string", "description": "Start date YYYY-MM-DD"},
                    "end_date": {"type": "string", "description": "End date YYYY-MM-DD"},
                },
                "required": ["symbol", "start_date", "end_date"],
            },
        ),
        # ── RAG ─────────────────────────────────────────────────────────
        types.Tool(
            name="get_rag_evidence",
            description=(
                "Semantic vector search over the Sentimatix news corpus. "
                "Returns the most relevant historical news chunks for a free-text query."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {"type": "string", "description": "NSE stock symbol"},
                    "start_date": {"type": "string", "description": "Start date YYYY-MM-DD"},
                    "end_date": {"type": "string", "description": "End date YYYY-MM-DD"},
                    "query": {"type": "string", "description": "Natural language search query"},
                    "top_k": {
                        "type": "integer",
                        "default": 5,
                        "minimum": 1,
                        "maximum": 20,
                        "description": "Number of results to return",
                    },
                },
                "required": ["symbol", "start_date", "end_date", "query"],
            },
        ),
        types.Tool(
            name="get_rag_stats",
            description="Return stats about the Sentimatix RAG vector database (document count, index info).",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
    ]


# ═══════════════════════════════════════════════════════════════════════════
# TOOL CALL HANDLER
# ═══════════════════════════════════════════════════════════════════════════

def _to_text(result: Any) -> str:
    """Serialise any result to a JSON string for MCP TextContent."""
    try:
        return json.dumps(result, ensure_ascii=False, indent=2, default=str)
    except Exception:
        return str(result)


@mcp.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    """Dispatch tool calls to the underlying Sentimatix tool functions."""
    logger.info(f"Tool call: {name} args={list(arguments.keys())}")

    try:
        result: Any = None

        # ── Orchestrator ────────────────────────────────────────────────
        if name == "explain_price_change":
            result = await explain_price_change(**arguments)

        # ── Enhanced Analysis ────────────────────────────────────────────
        elif name == "analyze_stock_enhanced":
            result = await analyze_stock_enhanced(**arguments)
        elif name == "compare_stocks":
            result = await compare_stocks(**arguments)

        # ── Stock Price Tools ────────────────────────────────────────────
        elif name == "get_stock_summary":
            result = get_stock_summary(**arguments)
        elif name == "get_historical_prices":
            result = get_historical_prices(**arguments)

        # ── News & Sentiment ─────────────────────────────────────────────
        elif name == "get_news_sentiment":
            result = get_news_sentiment(**arguments)
        elif name == "get_sentiment_aggregate":
            result = get_sentiment_aggregate(**arguments)

        # ── Technical Analysis ───────────────────────────────────────────
        elif name == "get_technical_analysis":
            result = await get_technical_analysis(**arguments)

        # ── Correlation ──────────────────────────────────────────────────
        elif name == "calculate_correlation":
            result = calculate_correlation(**arguments)
        elif name == "calculate_sentiment_price_correlation":
            result = calculate_sentiment_price_correlation(**arguments)

        # ── RAG ─────────────────────────────────────────────────────────
        elif name == "get_rag_evidence":
            result = get_rag_evidence(**arguments)
        elif name == "get_rag_stats":
            result = get_rag_stats()

        else:
            result = {"error": f"Unknown tool: {name}"}

        logger.info(f"Tool {name} completed successfully")
        return [types.TextContent(type="text", text=_to_text(result))]

    except Exception as exc:
        logger.exception(f"Error executing tool {name}")
        error_payload = {"error": str(exc), "tool": name, "arguments": arguments}
        return [types.TextContent(type="text", text=_to_text(error_payload))]


# ═══════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════

async def run_stdio():
    """Run as stdio MCP server (default — for Claude Desktop / Smithery)."""
    async with stdio_server() as (read_stream, write_stream):
        await mcp.run(read_stream, write_stream, mcp.create_initialization_options())


async def run_sse(port: int = 8003):
    """Run as HTTP server with both Streamable HTTP (/mcp) and SSE (/sse) transports."""
    from mcp.server.sse import SseServerTransport
    from starlette.applications import Starlette
    from starlette.routing import Mount, Route
    from starlette.responses import JSONResponse, PlainTextResponse
    from starlette.middleware import Middleware
    from starlette.middleware.cors import CORSMiddleware
    import uvicorn

    sse = SseServerTransport("/messages/")

    async def handle_sse(request):
        async with sse.connect_sse(request.scope, request.receive, request._send) as streams:
            await mcp.run(streams[0], streams[1], mcp.create_initialization_options())

    async def health(request):
        return PlainTextResponse("ok")

    # Enriched Tools List for Maximum Smithery Quality Score
    TOOLS_LIST = [
        {
            "name": "explain_price_change", 
            "description": "Analyzes and explains the driving factors behind an NSE stock's price movement over a specific timeframe. It synthesizes recent financial news, entity-level sentiment scores, and technical indicators to provide a comprehensive narrative of market behavior.", 
            "inputSchema": {
                "type": "object", 
                "properties": {
                    "symbol": {"type": "string", "description": "The stock ticker symbol on the National Stock Exchange of India (e.g., RELIANCE, TCS)."}, 
                    "start_date": {"type": "string", "description": "The start date of the analysis period in YYYY-MM-DD format."}, 
                    "end_date": {"type": "string", "description": "The end date of the analysis period in YYYY-MM-DD format."}
                }, 
                "required": ["symbol", "start_date", "end_date"]
            }
        },
        {
            "name": "analyze_stock_enhanced", 
            "description": "Generates a deep, AI-driven single-stock research report. Combines historical price data, moving averages, and news sentiment into a structured analysis to evaluate the overall health and momentum of the equity.", 
            "inputSchema": {
                "type": "object", 
                "properties": {
                    "symbol": {"type": "string", "description": "The stock ticker symbol on the National Stock Exchange of India (e.g., INFY, HDFCBANK)."}, 
                    "start_date": {"type": "string", "description": "The start date for data collection in YYYY-MM-DD format."}, 
                    "end_date": {"type": "string", "description": "The end date for data collection in YYYY-MM-DD format."}
                }, 
                "required": ["symbol", "start_date", "end_date"]
            }
        },
        {
            "name": "compare_stocks", 
            "description": "Performs a side-by-side quantitative and qualitative comparison of two NSE stocks. Useful for pair trading analysis or sector peer evaluation based on price performance and media sentiment.", 
            "inputSchema": {
                "type": "object", 
                "properties": {
                    "symbol1": {"type": "string", "description": "The primary stock ticker symbol (e.g., TATAMOTORS)."}, 
                    "symbol2": {"type": "string", "description": "The secondary stock ticker symbol for comparison (e.g., MARUTI)."}, 
                    "start_date": {"type": "string", "description": "The start date in YYYY-MM-DD format."}, 
                    "end_date": {"type": "string", "description": "The end date in YYYY-MM-DD format."}
                }, 
                "required": ["symbol1", "symbol2", "start_date", "end_date"]
            }
        },
        {
            "name": "get_stock_summary", 
            "description": "Fetches fundamental price metrics and recent performance summaries for an NSE-listed stock. Returns the latest closing price, percentage change, daily high/low, and trading volume.", 
            "inputSchema": {
                "type": "object", 
                "properties": {
                    "symbol": {"type": "string", "description": "The NSE stock ticker symbol."}, 
                    "period_days": {"type": "integer", "description": "The number of days to look back for the summary metrics (e.g., 7, 30, 90)."}
                }, 
                "required": ["symbol"]
            }
        },
        {
            "name": "get_historical_prices", 
            "description": "Retrieves the daily Open, High, Low, Close, and Volume (OHLCV) time-series data for an Indian equity. Essential for charting and custom technical analysis.", 
            "inputSchema": {
                "type": "object", 
                "properties": {
                    "symbol": {"type": "string", "description": "The NSE stock ticker symbol."}, 
                    "start_date": {"type": "string", "description": "Start date (YYYY-MM-DD)."}, 
                    "end_date": {"type": "string", "description": "End date (YYYY-MM-DD)."}
                }, 
                "required": ["symbol", "start_date", "end_date"]
            }
        },
        {
            "name": "get_news_sentiment", 
            "description": "Fetches recent financial news articles specifically mentioning the target Indian stock, complete with proprietary NLP sentiment scores (ranging from strongly negative to strongly positive) for each article.", 
            "inputSchema": {
                "type": "object", 
                "properties": {
                    "symbol": {"type": "string", "description": "The NSE stock ticker symbol."}, 
                    "start_date": {"type": "string", "description": "Start date (YYYY-MM-DD)."}, 
                    "end_date": {"type": "string", "description": "End date (YYYY-MM-DD)."}
                }, 
                "required": ["symbol", "start_date", "end_date"]
            }
        },
        {
            "name": "get_sentiment_aggregate", 
            "description": "Calculates the aggregated market mood and sentiment statistics for an NSE stock over a specified period. Useful for tracking sentiment shifts over time.", 
            "inputSchema": {
                "type": "object", 
                "properties": {
                    "symbol": {"type": "string", "description": "The NSE stock ticker symbol."}, 
                    "start_date": {"type": "string", "description": "Start date (YYYY-MM-DD)."}, 
                    "end_date": {"type": "string", "description": "End date (YYYY-MM-DD)."}
                }, 
                "required": ["symbol", "start_date", "end_date"]
            }
        },
        {
            "name": "get_technical_analysis", 
            "description": "Calculates and returns key technical indicators for an NSE stock, including Relative Strength Index (RSI), Moving Average Convergence Divergence (MACD), Bollinger Bands, and support/resistance levels.", 
            "inputSchema": {
                "type": "object", 
                "properties": {
                    "symbol": {"type": "string", "description": "The NSE stock ticker symbol."}, 
                    "period_days": {"type": "integer", "description": "The lookback period in days for calculating the indicators (standard is 14 for RSI)."}
                }, 
                "required": ["symbol"]
            }
        },
        {
            "name": "calculate_correlation", 
            "description": "Computes the Pearson correlation coefficient between the daily returns of two NSE stocks over a specific period to measure their statistical relationship.", 
            "inputSchema": {
                "type": "object", 
                "properties": {
                    "symbol1": {"type": "string", "description": "First NSE stock ticker symbol."}, 
                    "symbol2": {"type": "string", "description": "Second NSE stock ticker symbol."}, 
                    "start_date": {"type": "string", "description": "Start date (YYYY-MM-DD)."}, 
                    "end_date": {"type": "string", "description": "End date (YYYY-MM-DD)."}
                }, 
                "required": ["symbol1", "symbol2", "start_date", "end_date"]
            }
        },
        {
            "name": "get_rag_evidence", 
            "description": "Performs a semantic search over the Sentimatix financial news corpus. Retrieves specific quotes and evidence related to a query for a particular NSE stock to ground AI responses in factual reporting.", 
            "inputSchema": {
                "type": "object", 
                "properties": {
                    "symbol": {"type": "string", "description": "The NSE stock ticker symbol."}, 
                    "query": {"type": "string", "description": "The natural language question or topic to search the news corpus for (e.g., 'Q3 earnings report results')."}
                }, 
                "required": ["symbol", "query"]
            }
        }
    ]

    async def server_card(request):
        """Smithery server-card.json — correct format per Smithery spec."""
        card = {
            "serverInfo": {
                "name": "Sentimatix",
                "version": "1.0.0"
            },
            "systemPrompt": "You are a quantitative research agent utilizing the Sentimatix MCP to analyze Indian equities. Always ensure you are querying valid National Stock Exchange of India (NSE) ticker symbols. Provide data-driven, objective analysis using the sentiment and technical indicators returned by the tools.",
            "authentication": {
                "required": False
            },
            "configSchema": {
                "type": "object",
                "properties": {
                    "preferred_currency": {
                        "type": "string",
                        "description": "Optional: The preferred currency for financial outputs (defaults to INR).",
                        "default": "INR"
                    }
                }
            },
            "tools": TOOLS_LIST,
            "resources": [],
            "prompts": []
        }
        return JSONResponse(card)

    async def handle_mcp_http(request):
        """MCP JSON-RPC over HTTP — handles Smithery scanning protocol."""
        from starlette.responses import JSONResponse
        try:
            body = await request.json()
        except Exception:
            return JSONResponse({"jsonrpc": "2.0", "error": {"code": -32700, "message": "Parse error"}, "id": None}, status_code=400)

        method = body.get("method", "")
        req_id = body.get("id")

        if method == "initialize":
            return JSONResponse({
                "jsonrpc": "2.0", "id": req_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "serverInfo": {"name": "Sentimatix", "version": "1.0.0"},
                    "capabilities": {"tools": {}}
                }
            })
        elif method == "notifications/initialized":
            return JSONResponse({"jsonrpc": "2.0", "id": req_id, "result": {}})
        elif method == "tools/list":
            return JSONResponse({
                "jsonrpc": "2.0", "id": req_id,
                "result": {"tools": TOOLS_LIST}
            })
        elif method == "resources/list":
            return JSONResponse({"jsonrpc": "2.0", "id": req_id, "result": {"resources": []}})
        elif method == "prompts/list":
            return JSONResponse({"jsonrpc": "2.0", "id": req_id, "result": {"prompts": []}})
        else:
            return JSONResponse({
                "jsonrpc": "2.0", "id": req_id,
                "error": {"code": -32601, "message": f"Method not found: {method}"}
            })

    routes = [
        Route("/", endpoint=health),
        Route("/health", endpoint=health),
        Route("/mcp", endpoint=handle_mcp_http, methods=["POST", "OPTIONS"]),
        Route("/sse", endpoint=handle_sse),
        Route("/.well-known/mcp/server-card.json", endpoint=server_card),
        Mount("/messages/", app=sse.handle_post_message),
    ]

    middleware = [
        Middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
    ]

    starlette_app = Starlette(routes=routes, middleware=middleware)
    config = uvicorn.Config(starlette_app, host="0.0.0.0", port=port, log_level="info")
    server = uvicorn.Server(config)
    print(f"[Sentimatix MCP] Server listening on http://0.0.0.0:{port} (HTTP: /mcp, SSE: /sse)", file=sys.stderr)
    await server.serve()



def main():
    # Ensure log directory exists
    (ROOT / "logs").mkdir(exist_ok=True)

    if "--sse" in sys.argv:
        # Read port from env (Railway sets $PORT dynamically) or from --port= arg
        port = int(os.environ.get("PORT", 8003))
        for arg in sys.argv:
            if arg.startswith("--port="):
                port = int(arg.split("=")[1])
        asyncio.run(run_sse(port))
    else:
        asyncio.run(run_stdio())

if __name__ == "__main__":
    main()
