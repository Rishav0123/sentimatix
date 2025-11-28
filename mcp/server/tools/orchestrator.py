"""
High-Level Orchestrator Tool - Explain Price Changes

This tool orchestrates multiple sub-tools to provide comprehensive analysis.
"""

from typing import Dict, Any
from datetime import datetime, timedelta
import logging

from server.tools.stock_tools import get_stock_summary, get_historical_prices
from server.tools.news_tools import get_news_sentiment, get_sentiment_aggregate
from server.tools.rag_tools import get_rag_evidence
from server.tools.correlation import calculate_sentiment_price_correlation

logger = logging.getLogger(__name__)


async def explain_price_change(
    symbol: str,
    start_date: str,
    end_date: str
) -> Dict[str, Any]:
    """
    Comprehensive orchestration tool that calls all relevant tools to explain price changes.
    
    This is the main entry point for the "Why did X change?" use case.
    
    Args:
        symbol: Stock symbol (e.g., "AAPL")
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
    
    Returns:
        Aggregated data from all tools for LLM to synthesize
    """
    try:
        logger.info(f"Orchestrating price change explanation for {symbol} ({start_date} to {end_date})")
        
        # Calculate period in days
        start = datetime.fromisoformat(start_date)
        end = datetime.fromisoformat(end_date)
        period_days = (end - start).days
        
        # 1. Get stock price summary
        logger.info("Step 1/5: Fetching stock summary...")
        stock_summary = get_stock_summary(symbol, period_days)
        
        # 2. Get historical prices for correlation
        logger.info("Step 2/5: Fetching historical prices...")
        historical_prices = get_historical_prices(symbol, start_date, end_date, aggregation_period=1)
        
        # 3. Get news and sentiment
        logger.info("Step 3/5: Fetching news and sentiment...")
        news_sentiment = get_news_sentiment(symbol, start_date, end_date, top_n=10)
        sentiment_aggregate = get_sentiment_aggregate(symbol, start_date, end_date)
        
        # 4. Get RAG evidence (semantic search for explanations)
        logger.info("Step 4/5: Performing RAG semantic search...")
        query_text = f"reasons for {symbol} price change drop decline fall movement"
        rag_evidence = get_rag_evidence(symbol, start_date, end_date, query_text, top_k=6)
        
        # 5. Calculate correlation between sentiment and price using daily aggregated sentiment
        logger.info("Step 5/5: Calculating correlation with daily sentiment aggregation...")
        correlation_result = None
        try:
            if historical_prices and len(historical_prices) > 2 and news_sentiment:
                # Build date -> avg sentiment map
                sentiment_by_date = {}
                for item in news_sentiment:
                    date_key = item.get("published_at", "")[:10]
                    if date_key:
                        sentiment_by_date.setdefault(date_key, []).append(item.get("sentiment_score", 0.0))
                daily_sentiment = {d: (sum(vals) / len(vals)) for d, vals in sentiment_by_date.items() if vals}
                
                # Align on price dates
                price_changes = []
                sentiment_series = []
                for p in historical_prices:
                    d = p.get("date")
                    if not d:
                        continue
                    sc = daily_sentiment.get(d)
                    if sc is None:
                        continue  # only consider days with sentiment data
                    price_changes.append(p.get("change_percent", 0))
                    sentiment_series.append(sc)
                if len(price_changes) >= 3 and len(sentiment_series) >= 3:
                    correlation_result = calculate_sentiment_price_correlation(
                        price_changes,
                        sentiment_series,
                        symbol
                    )
        except Exception as e:
            logger.warning(f"Could not calculate correlation: {e}")
            correlation_result = {"error": str(e)}
        
        # Aggregate all results
        result = {
            "symbol": symbol,
            "period": {
                "start_date": start_date,
                "end_date": end_date,
                "days": period_days
            },
            "stock_summary": stock_summary,
            "historical_prices": historical_prices[:14],  # Last 2 weeks for brevity
            "news_sentiment": news_sentiment,
            "sentiment_aggregate": sentiment_aggregate,
            "rag_evidence": rag_evidence,
            "correlation": correlation_result,
            "timestamp": datetime.now().isoformat(),
            "tool_status": {
                "stock_summary": "ok" if "error" not in stock_summary else "error",
                "historical_prices": "ok" if historical_prices and "error" not in historical_prices[0] else "error",
                "news_sentiment": "ok" if news_sentiment and "error" not in news_sentiment[0] else "error",
                "rag_evidence": "ok" if rag_evidence and "error" not in rag_evidence[0] else "error",
                "correlation": "ok" if correlation_result and "error" not in correlation_result else "error"
            }
        }
        
        logger.info(f"Orchestration complete for {symbol}. Tools status: {result['tool_status']}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error in explain_price_change orchestration: {e}")
        return {
            "error": str(e),
            "symbol": symbol,
            "period": {"start_date": start_date, "end_date": end_date}
        }


# Tool Schema for MCP
ORCHESTRATOR_TOOLS_SCHEMA = [
    {
        "name": "explain_price_change",
        "description": "HIGH-LEVEL ORCHESTRATOR: Automatically gathers all relevant data (price, news, sentiment, RAG evidence, correlation) to explain why a stock price changed. Use this as a one-stop tool for comprehensive analysis.",
        "parameters": {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "Stock symbol (e.g., AAPL, TSLA, NVDA)"
                },
                "start_date": {
                    "type": "string",
                    "description": "Start date in YYYY-MM-DD format"
                },
                "end_date": {
                    "type": "string",
                    "description": "End date in YYYY-MM-DD format"
                }
            },
            "required": ["symbol", "start_date", "end_date"]
        }
    }
]
