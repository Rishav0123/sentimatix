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
        # Call your /api/news endpoint with broader parameters
        url = f"{BACKEND_API_URL}/news"
        headers = {
            "X-API-Key": BACKEND_API_KEY,
            "Content-Type": "application/json"
        }
        
        # Create symbol variations for better matching
        symbol_clean = symbol.replace(".NS", "").upper()
        symbol_variations = [symbol, symbol_clean, f"{symbol_clean}.NS"]
        
        # Company name mapping for better news filtering
        company_names = {
            'TCS': ['TCS', 'Tata Consultancy Services', 'Tata Consultancy'],
            'INFY': ['Infosys', 'INFY'],
            'HDFCBANK': ['HDFC Bank', 'HDFC', 'Housing Development Finance Corporation'],
            'ICICIBANK': ['ICICI Bank', 'ICICI'],
            'RELIANCE': ['Reliance Industries', 'Reliance', 'RIL'],
            'WIPRO': ['Wipro'],
            'AXISBANK': ['Axis Bank', 'Axis'],
            'KOTAKBANK': ['Kotak Mahindra Bank', 'Kotak Bank', 'Kotak'],
            'SBIN': ['State Bank of India', 'SBI'],
            'NTPC': ['NTPC', 'National Thermal Power Corporation'],
            'ONGC': ['ONGC', 'Oil and Natural Gas Corporation'],
            'IOC': ['Indian Oil Corporation', 'Indian Oil', 'IOC'],
            'ITC': ['ITC'],
            'BHARTIARTL': ['Bharti Airtel', 'Airtel'],
            'HINDUNILVR': ['Hindustan Unilever', 'HUL'],
            'BAJFINANCE': ['Bajaj Finance'],
            'MARUTI': ['Maruti Suzuki', 'Maruti'],
            'ASIANPAINT': ['Asian Paints'],
            'NESTLEIND': ['Nestle India', 'Nestle'],
            'TITAN': ['Titan Company', 'Titan'],
            'SUNPHARMA': ['Sun Pharmaceutical', 'Sun Pharma'],
            'DRREDDY': ['Dr. Reddy\'s Laboratories', 'Dr Reddy'],
            'CIPLA': ['Cipla'],
            'DIVISLAB': ['Divi\'s Laboratories', 'Divis Lab'],
            'BRITANNIA': ['Britannia Industries', 'Britannia'],
            'TATASTEEL': ['Tata Steel'],
            'JSWSTEEL': ['JSW Steel'],
            'HINDALCO': ['Hindalco Industries', 'Hindalco'],
            'VEDL': ['Vedanta Limited', 'Vedanta'],
            'ADANIENT': ['Adani Enterprises'],
            'ADANIPORTS': ['Adani Ports', 'Adani Ports and SEZ'],
            'POWERGRID': ['Power Grid Corporation', 'PowerGrid'],
            'ULTRACEMCO': ['UltraTech Cement'],
            'GRASIM': ['Grasim Industries'],
            'SHREECEM': ['Shree Cement'],
            'EICHERMOT': ['Eicher Motors'],
            'BAJAJ-AUTO': ['Bajaj Auto'],
            'HEROMOTOCO': ['Hero MotoCorp'],
            'M&M': ['Mahindra & Mahindra', 'Mahindra'],
            'TATAMOTORS': ['Tata Motors'],
        }
        
        # Try multiple approaches to get news, prioritizing stock-specific results
        attempts = [
            {"stock_symbol": symbol_clean, "limit": max(100, top_n * 5), "page": 1},
            {"stock_symbol": symbol, "limit": max(100, top_n * 5), "page": 1},
            {"limit": max(200, top_n * 10), "page": 1},  # Get more general news to filter
        ]
        
        news_items = []
        for attempt_params in attempts:
            try:
                response = requests.get(url, params=attempt_params, headers=headers, timeout=15)
                response.raise_for_status()
                
                data = response.json()
                items = data.get("data", [])
                
                if items and len(items) > 0:
                    news_items = items
                    logger.info(f"Found {len(news_items)} news items with params: {attempt_params}")
                    break
            except Exception as e:
                logger.warning(f"News fetch attempt failed with params {attempt_params}: {e}")
                continue
        
        # If no symbol-specific results, get general news for content filtering
        if not news_items:
            try:
                # Increased limit for fallback to 500 to catch more potential matches
                response = requests.get(url, params={"limit": 500, "page": 1}, headers=headers, timeout=15)
                response.raise_for_status()
                data = response.json()
                news_items = data.get("data", [])
                logger.info(f"Fallback: Found {len(news_items)} general news items for content filtering")
            except Exception as e:
                logger.warning(f"Fallback news fetch failed: {e}")
                news_items = []
        
        # Filter by date range and relevance
        filtered_news = []
        company_keywords = company_names.get(symbol_clean, [symbol_clean])
        
        for item in news_items:
            pub_date = item.get("published_at", "")[:10]  # Extract YYYY-MM-DD
            if start_date <= pub_date <= end_date:
                # Handle both impact_score and sentiment_score fields
                sentiment_score = item.get("impact_score") or item.get("sentiment_score", 0.0)
                if sentiment_score is None:
                    sentiment_score = 0.0
                
                # Normalize sentiment score to [-1, 1] range
                normalized_sentiment = float(sentiment_score)
                if abs(normalized_sentiment) > 1:
                    normalized_sentiment = (normalized_sentiment - 50) / 50  # Convert 0-100 to -1 to 1
                    normalized_sentiment = max(-1, min(1, normalized_sentiment))  # Clamp to [-1, 1]
                
                # Ensure we have a title
                title = item.get("title") or item.get("headline") or "News Update"
                content = item.get("content") or item.get("description") or ""
                
                # Calculate relevance score based on company name mentions
                relevance_score = 0.0
                title_lower = title.lower()
                content_lower = content.lower()
                
                # Check if article has a database symbol assigned
                db_symbol = item.get("yfin_symbol")
                if db_symbol and db_symbol != "N/A" and db_symbol.replace(".NS", "").upper() == symbol_clean:
                    # Perfect database match
                    relevance_score = 100.0
                else:
                    # Content-based relevance scoring (fallback when db symbols not assigned)
                    score_accumulator = 0.0
                    for keyword in company_keywords:
                        keyword_lower = keyword.lower()
                        # Higher weight for title mentions
                        if keyword_lower in title_lower:
                            score_accumulator += 40.0
                        # Lower weight for content mentions
                        if keyword_lower in content_lower:
                            score_accumulator += 15.0
                    
                    # Boost relevance if stock symbol is mentioned
                    if symbol_clean.lower() in title_lower or symbol_clean.lower() in content_lower:
                        score_accumulator += 25.0
                    
                    # Additional boost for exact company name matches
                    for keyword in company_keywords:
                        if len(keyword) > 3:  # Only for substantial keywords
                            if keyword.lower() in title_lower:
                                score_accumulator += 20.0
                    
                    relevance_score = min(100.0, score_accumulator)
                
                # Get source with fallback
                source = item.get("source") or item.get("publisher") or "Unknown Source"
                
                filtered_news.append({
                    "id": item.get("id"),
                    "title": title,
                    "summary": content[:300] if content else "",  # First 300 chars
                    "url": item.get("url") or item.get("link"),
                    "source": source,
                    "published_at": item.get("published_at") or item.get("date"),
                    "sentiment": item.get("sentiment") or "neutral",
                    "sentiment_score": float(normalized_sentiment),
                    "stock_symbol": item.get("yfin_symbol") or symbol,
                    "sector": item.get("sector"),
                    "relevance_score": relevance_score,
                    "match_quality": "database" if (db_symbol and db_symbol != "N/A") else "content"
                })
        
        # Sort by relevance first, then by date (most recent first)
        filtered_news.sort(key=lambda x: (x.get("relevance_score", 0), x.get("published_at", "")), reverse=True)
        
        # Filter for relevant articles - be more selective
        highly_relevant = [item for item in filtered_news if item.get("relevance_score", 0) > 30]
        if highly_relevant:
            result = highly_relevant[:top_n]
            logger.info(f"Using {len(result)} highly relevant articles (relevance > 30)")
        else:
            # If no relevant articles, return most recent general news but mark as low relevance
            result = filtered_news[:top_n]
            logger.info(f"No highly relevant articles found, returning {len(result)} general articles")
            for item in result:
                item["match_quality"] = "general"
        
        # Calculate aggregate sentiment - handle missing sentiment scores and normalize
        if result:
            sentiment_scores = []
            for item in result:
                score = item.get("sentiment_score", 0)
                if score is not None:
                    # Score should already be normalized from above, but double-check
                    normalized_score = float(score)
                    if abs(normalized_score) > 1:
                        normalized_score = (normalized_score - 50) / 50
                        normalized_score = max(-1, min(1, normalized_score))
                    sentiment_scores.append(normalized_score)
            
            avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0.0
        else:
            avg_sentiment = 0.0
        
        logger.info(f"Retrieved {len(result)} news articles for {symbol} ({start_date} to {end_date}), avg sentiment: {avg_sentiment:.2f}, avg relevance: {sum(item.get('relevance_score', 0) for item in result) / len(result) if result else 0:.2f}")
        
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
        
        if not all_news or (len(all_news) > 0 and "error" in all_news[0]):
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
        
        # Calculate statistics - handle missing sentiment data and normalize scores
        sentiment_scores = []
        for item in all_news:
            score = item.get("sentiment_score", 0)
            if score is not None:
                # Normalize sentiment score to [-1, 1] range
                # Assuming raw scores are in range [0, 100] or similar
                normalized_score = float(score)
                
                # If score is > 1, assume it's in 0-100 range and normalize
                if abs(normalized_score) > 1:
                    normalized_score = (normalized_score - 50) / 50  # Convert 0-100 to -1 to 1
                    normalized_score = max(-1, min(1, normalized_score))  # Clamp to [-1, 1]
                
                sentiment_scores.append(normalized_score)
        
        avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0.0
        
        positive = sum(1 for item in all_news if item.get("sentiment") == "positive")
        negative = sum(1 for item in all_news if item.get("sentiment") == "negative")
        neutral = total - positive - negative  # Calculate neutral as remainder
        
        result = {
            "symbol": symbol,
            "period": f"{start_date} to {end_date}",
            "total_articles": total,
            "avg_sentiment": round(avg_sentiment, 3),
            "positive_count": positive,
            "negative_count": negative,
            "neutral_count": neutral,
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
