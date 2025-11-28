"""
Stock Price Tools - Wrapper around your existing /api/stocks endpoints
"""

import requests
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import logging

from server.config import BACKEND_API_URL, BACKEND_API_KEY
from server.tools.symbol_utils import normalize_symbol

logger = logging.getLogger(__name__)


def get_stock_summary(symbol: str, period_days: int = 7) -> Dict[str, Any]:
    """
    Get stock price summary for a given period.
    
    Args:
        symbol: Stock symbol (e.g., "AAPL", "TSLA")
        period_days: Number of days to analyze (default: 7)
    
    Returns:
        Dict with price metrics: change_pct, open, close, high, low, avg_volume, volatility
    """
    try:
        # Use symbol-based prices endpoint, compute metrics locally.
        display_symbol, _yfin_symbol = normalize_symbol(symbol)

        url = f"{BACKEND_API_URL}/stocks/prices/{display_symbol}"
        params = {"days": max(1, int(period_days))}
        headers = {}
        if BACKEND_API_KEY:
            headers["Authorization"] = f"Bearer {BACKEND_API_KEY}"

        # Increased timeout for larger history windows (was 15)
        response = requests.get(url, params=params, headers=headers, timeout=30)
        response.raise_for_status()

        prices = response.json() or []
        if isinstance(prices, dict) and prices.get("error"):
            return {"error": prices.get("error")}
        if not isinstance(prices, list) or len(prices) == 0:
            return {"error": f"No price data for {display_symbol}"}

        # Ensure sorted by date ascending
        prices_sorted = sorted(prices, key=lambda p: p.get("date", ""))
        first = prices_sorted[0]
        last = prices_sorted[-1]

        first_open = float(first.get("open", 0) or 0)
        last_close = float(last.get("close", 0) or 0)
        high = max(float(p.get("high", 0) or 0) for p in prices_sorted)
        # Avoid zeros in low where missing
        lows = [float(p.get("low", 0) or 0) for p in prices_sorted]
        lows = [x for x in lows if x > 0]
        low = min(lows) if lows else 0.0
        avg_volume = int(sum(int(float(p.get("volume", 0) or 0)) for p in prices_sorted) / len(prices_sorted))

        change = last_close - first_open
        change_percent = (change / first_open * 100) if first_open else 0.0

        summary = {
            "symbol": display_symbol,
            "period_days": int(period_days),
            "current_price": last_close,
            "open_price": first_open,
            "change": round(change, 2),
            "change_percent": round(change_percent, 2),
            "high": round(high, 2),
            "low": round(low, 2),
            "avg_volume": avg_volume,
            "volatility": _calculate_volatility(prices_sorted),
            "last_updated": last.get("date"),
            "data_points": len(prices_sorted)
        }

        logger.info(f"Retrieved stock summary for {display_symbol}: {summary['change_percent']:.2f}% change")
        return summary

    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching stock summary for {symbol}: {e}")
        return {"error": str(e)}
    except Exception as e:
        logger.error(f"Unexpected error in get_stock_summary: {e}")
        return {"error": str(e)}


def get_historical_prices(
    symbol: str,
    start_date: str,
    end_date: str,
    aggregation_period: int = 1
) -> List[Dict[str, Any]]:
    """
    Get time-series price data for charting and analysis.
    
    Args:
        symbol: Stock symbol
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        aggregation_period: Days to aggregate (1=daily, 7=weekly, 30=monthly)
    
    Returns:
        List of price records with date, open, high, low, close, volume, change_pct
    """
    try:
        # Calculate history days from dates, then use symbol-based endpoint
        start = datetime.fromisoformat(start_date)
        end = datetime.fromisoformat(end_date)
        history_days = max(1, (end - start).days)

        display_symbol, _ = normalize_symbol(symbol)
        url = f"{BACKEND_API_URL}/stocks/prices/{display_symbol}"
        params = {"days": history_days}
        headers = {}
        if BACKEND_API_KEY:
            headers["Authorization"] = f"Bearer {BACKEND_API_KEY}"

        # Increased timeout to mitigate longer-range queries
        response = requests.get(url, params=params, headers=headers, timeout=30)
        response.raise_for_status()
        prices = response.json() or []
        # Progressive enhancement: if long range requested and few points returned, attempt extended fetch
        if history_days > 20 and len(prices) < int(history_days * 0.5):
            try:
                extra_days = history_days + 10
                logger.info(f"Historical prices sparse ({len(prices)} points for {history_days} days). Attempting extended fetch ({extra_days} days)...")
                extra_params = {"days": extra_days}
                extra_resp = requests.get(url, params=extra_params, headers=headers, timeout=30)
                extra_resp.raise_for_status()
                extra_prices = extra_resp.json() or []
                # Merge by date
                by_date = {p.get("date"): p for p in prices if p.get("date")}
                for ep in extra_prices:
                    d = ep.get("date")
                    if d and d not in by_date:
                        by_date[d] = ep
                prices = sorted(by_date.values(), key=lambda p: p.get("date", ""))
                logger.info(f"Extended fetch produced {len(prices)} unique price points.")
            except Exception as ef:
                logger.warning(f"Extended fetch failed: {ef}")
        if not isinstance(prices, list):
            return [{"error": "Unexpected response format from backend prices endpoint"}]

        # Filter by date range (backend returns last N days; filter to exact range)
        filtered = [p for p in prices if start_date <= p.get("date", "") <= end_date]

        # Optionally aggregate client-side if requested period > 1
        if aggregation_period and aggregation_period > 1 and len(filtered) > 0:
            agg: List[Dict[str, Any]] = []
            i = 0
            # Ensure sorted by date ascending
            filtered.sort(key=lambda p: p.get("date", ""))
            while i < len(filtered):
                chunk = filtered[i:min(i + aggregation_period, len(filtered))]
                first_open = float(chunk[0].get("open", 0) or 0)
                last_close = float(chunk[-1].get("close", 0) or 0)
                agg_point = {
                    "date": chunk[-1].get("date"),
                    "open": first_open,
                    "high": max(float(p.get("high", 0) or 0) for p in chunk),
                    "low": min([float(p.get("low", 0) or 0) for p in chunk if float(p.get("low", 0) or 0) > 0]) if any(float(p.get("low", 0) or 0) > 0 for p in chunk) else 0.0,
                    "close": last_close,
                    "volume": sum(int(float(p.get("volume", 0) or 0)) for p in chunk),
                    "change": round(last_close - first_open, 2),
                    "change_percent": round(((last_close - first_open) / first_open * 100) if first_open else 0.0, 2)
                }
                agg.append(agg_point)
                i += aggregation_period
            filtered = agg

        logger.info(f"Retrieved {len(filtered)} price records for {display_symbol} ({start_date} to {end_date})")
        return filtered

    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching historical prices for {symbol}: {e}")
        return [{"error": str(e)}]
    except Exception as e:
        logger.error(f"Unexpected error in get_historical_prices: {e}")
        return [{"error": str(e)}]


def _get_stock_id_from_symbol(symbol: str) -> Optional[str]:
    """
    Deprecated: Previously mapped symbol -> stock_id via /api/stocks list.
    The backend list does not expose IDs; price endpoints accept symbols directly.
    Kept for backward compatibility if backend adds an ID lookup later.
    """
    return None


def _calculate_volatility(price_history: List[Dict[str, Any]]) -> float:
    """Calculate simple volatility (standard deviation of daily returns)"""
    try:
        if len(price_history) < 2:
            return 0.0
        
        returns = []
        for i in range(1, len(price_history)):
            prev_close = price_history[i-1].get("close", 0)
            curr_close = price_history[i].get("close", 0)
            if prev_close > 0:
                ret = (curr_close - prev_close) / prev_close
                returns.append(ret)
        
        if not returns:
            return 0.0
        
        # Calculate standard deviation
        mean_ret = sum(returns) / len(returns)
        variance = sum((r - mean_ret) ** 2 for r in returns) / len(returns)
        volatility = variance ** 0.5
        
        return round(volatility * 100, 2)  # Convert to percentage
        
    except Exception as e:
        logger.error(f"Error calculating volatility: {e}")
        return 0.0


# Tool Schema for MCP
STOCK_TOOLS_SCHEMA = [
    {
        "name": "get_stock_summary",
        "description": "Get stock price summary metrics for a given period (price change, high, low, volume, volatility)",
        "parameters": {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "Stock symbol (e.g., AAPL, TSLA, NVDA)"
                },
                "period_days": {
                    "type": "integer",
                    "description": "Number of days to analyze (default: 7)",
                    "default": 7,
                    "minimum": 1,
                    "maximum": 365
                }
            },
            "required": ["symbol"]
        }
    },
    {
        "name": "get_historical_prices",
        "description": "Get time-series historical price data for charting and detailed analysis",
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
                },
                "aggregation_period": {
                    "type": "integer",
                    "description": "Days to aggregate: 1=daily, 7=weekly, 30=monthly",
                    "default": 1,
                    "enum": [1, 7, 15, 30]
                }
            },
            "required": ["symbol", "start_date", "end_date"]
        }
    }
]
