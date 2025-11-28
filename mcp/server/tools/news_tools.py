"""
News & Sentiment Tools - Wrapper around your /api/news endpoint
"""

import requests
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import logging

from server.config import BACKEND_API_URL, BACKEND_API_KEY

logger = logging.getLogger(__name__)


def get_news_sentiment(
    symbol: str,
    start_date: str,
    end_date: str,
    top_n: int = 10,
    sentiment_filter: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Get news articles and sentiment scores for a stock in a time period.
    
    Args:
        symbol: Stock symbol (e.g., "AAPL")
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        top_n: Maximum number of articles to return (default: 10)
        sentiment_filter: Filter by sentiment: "positive", "negative", "neutral" (optional)
    
    Returns:
        List of news articles with sentiment scores, sorted by relevance and date
    """
    try:
        # Call your /api/news endpoint
        url = f"{BACKEND_API_URL}/news"
        params = {
            "stock_symbol": symbol,
            "limit": top_n * 2,  # Fetch more, then filter by date
            "page": 1
        }
        
        if sentiment_filter:
            params["sentiment"] = sentiment_filter
        
        headers = {}
        if BACKEND_API_KEY:
            headers["Authorization"] = f"Bearer {BACKEND_API_KEY}"
        
        response = requests.get(url, params=params, headers=headers, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        news_items = data.get("data", [])
        
        # Filter by date range
        filtered_news = []
        for item in news_items:
            pub_date = item.get("published_at", "")[:10]  # Extract YYYY-MM-DD
            if start_date <= pub_date <= end_date:
                filtered_news.append({
                    "id": item.get("id"),
                    "title": item.get("title"),
                    "summary": item.get("content", "")[:300],  # First 300 chars
                    "url": item.get("url"),
                    "source": item.get("source"),
                    "published_at": item.get("published_at"),
                    "sentiment": item.get("sentiment"),
                    "sentiment_score": item.get("impact_score", 0.0),
                    "stock_symbol": item.get("stock_symbol"),
                    "sector": item.get("sector"),
                })
        
        # Sort by date (most recent first)
        filtered_news.sort(key=lambda x: x.get("published_at", ""), reverse=True)
        
        # Limit to top_n
        result = filtered_news[:top_n]
        
        # Calculate aggregate sentiment
        if result:
            avg_sentiment = sum(item.get("sentiment_score", 0) for item in result) / len(result)
        else:
            avg_sentiment = 0.0
        
        logger.info(f"Retrieved {len(result)} news articles for {symbol} ({start_date} to {end_date}), avg sentiment: {avg_sentiment:.2f}")
        
        return result
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching news for {symbol}: {e}")
        return [{"error": str(e)}]
    except Exception as e:
        logger.error(f"Unexpected error in get_news_sentiment: {e}")
        return [{"error": str(e)}]


def get_sentiment_aggregate(
    symbol: str,
    start_date: str,
    end_date: str
) -> Dict[str, Any]:
    """
    Get aggregated sentiment statistics for a period.
    
    Returns:
        Dict with avg_sentiment, positive_count, negative_count, neutral_count, total_articles
    """
    try:
        # Fetch all news for the period
        all_news = get_news_sentiment(symbol, start_date, end_date, top_n=100)
        
        if not all_news or "error" in all_news[0]:
            return {"error": "Failed to fetch news"}
        
        total = len(all_news)
        if total == 0:
            return {
                "symbol": symbol,
                "period": f"{start_date} to {end_date}",
                "total_articles": 0,
                "avg_sentiment": 0.0,
                "positive_count": 0,
                "negative_count": 0,
                "neutral_count": 0
            }
        
        # Calculate statistics
        sentiment_scores = [item.get("sentiment_score", 0) for item in all_news]
        avg_sentiment = sum(sentiment_scores) / total
        
        positive = sum(1 for item in all_news if item.get("sentiment") == "positive")
        negative = sum(1 for item in all_news if item.get("sentiment") == "negative")
        neutral = sum(1 for item in all_news if item.get("sentiment") == "neutral")
        
        result = {
            "symbol": symbol,
            "period": f"{start_date} to {end_date}",
            "total_articles": total,
            "avg_sentiment": round(avg_sentiment, 3),
            "positive_count": positive,
            "negative_count": negative,
            "neutral_count": 0,
            "sentiment_breakdown": {
                "positive_pct": round(positive / total * 100, 1),
                "negative_pct": round(negative / total * 100, 1),
                "neutral_pct": round(neutral / total * 100, 1)
            }
        }
        
        logger.info(f"Sentiment aggregate for {symbol}: {result['avg_sentiment']:.2f} ({total} articles)")
        return result
        
    except Exception as e:
        logger.error(f"Error calculating sentiment aggregate: {e}")
        return {"error": str(e)}


# Tool Schema for MCP
NEWS_TOOLS_SCHEMA = [
    {
        "name": "get_news_sentiment",
        "description": "Get news articles with sentiment analysis for a stock in a specific time period",
        "parameters": {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "Stock symbol (e.g., AAPL, TSLA)"
                },
                "start_date": {
                    "type": "string",
                    "description": "Start date in YYYY-MM-DD format"
                },
                "end_date": {
                    "type": "string",
                    "description": "End date in YYYY-MM-DD format"
                },
                "top_n": {
                    "type": "integer",
                    "description": "Maximum number of articles to return (default: 10)",
                    "default": 10,
                    "minimum": 1,
                    "maximum": 50
                },
                "sentiment_filter": {
                    "type": "string",
                    "description": "Filter by sentiment: positive, negative, or neutral",
                    "enum": ["positive", "negative", "neutral"]
                }
            },
            "required": ["symbol", "start_date", "end_date"]
        }
    },
    {
        "name": "get_sentiment_aggregate",
        "description": "Get aggregated sentiment statistics (average, counts) for a period",
        "parameters": {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "Stock symbol"
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
