"""
Technical Analysis Tools
"""

import math
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

def calculate_sma(prices: List[float], period: int) -> List[Optional[float]]:
    """
    Calculate Simple Moving Average (SMA)
    """
    if len(prices) < period:
        return [None] * len(prices)
    
    sma_values = [None] * (period - 1)
    for i in range(len(prices) - period + 1):
        window = prices[i : i + period]
        sma_values.append(sum(window) / period)
        
    return sma_values

def calculate_ema(prices: List[float], period: int) -> List[Optional[float]]:
    """
    Calculate Exponential Moving Average (EMA)
    """
    if len(prices) < period:
        return [None] * len(prices)

    ema_values = [None] * (period - 1)
    # Initial SMA as the first EMA
    initial_sma = sum(prices[:period]) / period
    ema_values.append(initial_sma)
    
    multiplier = 2 / (period + 1)
    
    for i in range(period, len(prices)):
        current_price = prices[i]
        prev_ema = ema_values[-1]
        new_ema = (current_price - prev_ema) * multiplier + prev_ema
        ema_values.append(new_ema)
        
    return ema_values

def calculate_rsi(prices: List[float], period: int = 14) -> List[Optional[float]]:
    """
    Calculate Relative Strength Index (RSI)
    """
    if len(prices) < period + 1:
        return [None] * len(prices)
        
    gains = []
    losses = []
    
    # Calculate price changes
    for i in range(1, len(prices)):
        change = prices[i] - prices[i-1]
        if change > 0:
            gains.append(change)
            losses.append(0.0)
        else:
            gains.append(0.0)
            losses.append(abs(change))
            
    # Calculate initial averages
    rsi_values = [None] * period
    
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    
    if avg_loss == 0:
        rsi_values.append(100.0)
    else:
        rs = avg_gain / avg_loss
        rsi_values.append(100 - (100 / (1 + rs)))
        
    # Smoothed calculation for subsequent values
    for i in range(period, len(gains)):
        avg_gain = ((avg_gain * (period - 1)) + gains[i]) / period
        avg_loss = ((avg_loss * (period - 1)) + losses[i]) / period
        
        if avg_loss == 0:
            rsi_values.append(100.0)
        else:
            rs = avg_gain / avg_loss
            rsi_values.append(100 - (100 / (1 + rs)))
            
    return rsi_values

def calculate_macd(prices: List[float], fast_period: int = 12, slow_period: int = 26, signal_period: int = 9) -> Dict[str, List[Optional[float]]]:
    """
    Calculate MACD (Moving Average Convergence Divergence)
    """
    ema_fast = calculate_ema(prices, fast_period)
    ema_slow = calculate_ema(prices, slow_period)
    
    macd_line = []
    for i in range(len(prices)):
        if ema_fast[i] is not None and ema_slow[i] is not None:
            macd_line.append(ema_fast[i] - ema_slow[i])
        else:
            macd_line.append(None)
            
    # Calculate Signal Line (EMA of MACD Line)
    # Filter out None values to calculate signal line, then pad
    valid_macd = [m for m in macd_line if m is not None]
    
    if len(valid_macd) < signal_period:
        signal_line = [None] * len(prices)
        histogram = [None] * len(prices)
    else:
        valid_signal = calculate_ema(valid_macd, signal_period)
        
        # Pad signal line to match original length
        # The first (slow_period - 1) indices of macd_line are None.
        # Then valid_signal starts having values at index (signal_period - 1) relative to valid_macd.
        # So we need to pad (slow_period - 1) + (signal_period - 1) Nones?
        # Actually simplest to just map back.
        
        signal_line = [None] * (len(prices) - len(valid_signal)) + valid_signal
        
        histogram = []
        for i in range(len(prices)):
            if macd_line[i] is not None and signal_line[i] is not None:
                histogram.append(macd_line[i] - signal_line[i])
            else:
                histogram.append(None)
                
    return {
        "macd_line": macd_line,
        "signal_line": signal_line,
        "histogram": histogram
    }

def calculate_bollinger_bands(prices: List[float], period: int = 20, std_dev_multiplier: float = 2.0) -> Dict[str, List[Optional[float]]]:
    """
    Calculate Bollinger Bands
    """
    sma = calculate_sma(prices, period)
    upper_band = [None] * len(prices)
    lower_band = [None] * len(prices)
    
    for i in range(period - 1, len(prices)):
        window = prices[i - period + 1 : i + 1]
        
        # Calculate standard deviation
        mean = sum(window) / period
        variance = sum((x - mean) ** 2 for x in window) / period
        std_dev = math.sqrt(variance)
        
        if sma[i] is not None:
            upper_band[i] = sma[i] + (std_dev * std_dev_multiplier)
            lower_band[i] = sma[i] - (std_dev * std_dev_multiplier)
            
    return {
        "middle_band": sma,
        "upper_band": upper_band,
        "lower_band": lower_band
    }

def calculate_atr(highs: List[float], lows: List[float], closes: List[float], period: int = 14) -> List[Optional[float]]:
    """
    Calculate Average True Range (ATR)
    """
    if len(closes) < period + 1:
        return [None] * len(closes)
        
    true_ranges = [highs[0] - lows[0]] # First TR is High - Low
    
    for i in range(1, len(closes)):
        h = highs[i]
        l = lows[i]
        prev_c = closes[i-1]
        
        tr1 = h - l
        tr2 = abs(h - prev_c)
        tr3 = abs(l - prev_c)
        
        true_ranges.append(max(tr1, tr2, tr3))
        
    atr_values = [None] * (period - 1)
    
    # Initial ATR is SMA of TR
    initial_atr = sum(true_ranges[:period]) / period
    atr_values.append(initial_atr)
    
    # Smooth thereafter
    for i in range(period, len(true_ranges)):
        current_tr = true_ranges[i]
        prev_atr = atr_values[-1]
        new_atr = ((prev_atr * (period - 1)) + current_tr) / period
        atr_values.append(new_atr)
        
    return atr_values


# --- MCP Tool Wrapper ---

from server.tools.stock_tools import get_historical_prices

async def get_technical_analysis(symbol: str, period_days: int = 100) -> Dict[str, Any]:
    """
    Get technical analysis indicators for a stock.
    Returns RSI, MACD, Bollinger Bands, and Moving Averages.
    """
    try:
        # Fetch historical data
        # We need enough data to calculate indicators.
        # e.g. for EMA(26), we need at least 26 days, preferably more to stabilize.
        # Default fetching 100 days (approx 3-4 months)
        
        end_date_dt = datetime.now()
        start_date_dt = end_date_dt - timedelta(days=period_days + 50) # Fetch extra buffer
        
        start_date = start_date_dt.strftime("%Y-%m-%d")
        end_date = end_date_dt.strftime("%Y-%m-%d")
        
        prices_data = get_historical_prices(symbol, start_date, end_date)
        
        if not prices_data or (isinstance(prices_data, list) and len(prices_data) > 0 and "error" in prices_data[0]):
             return {"error": f"Failed to fetch price data for {symbol}"}
             
        # Extract series
        # Ensure sorted by date ascending
        prices_data.sort(key=lambda x: x.get("date", ""))
        
        closes = [float(p.get("close", 0) or 0) for p in prices_data]
        highs = [float(p.get("high", 0) or 0) for p in prices_data]
        lows = [float(p.get("low", 0) or 0) for p in prices_data]
        dates = [p.get("date") for p in prices_data]
        
        if len(closes) < 30:
             return {"error": "Insufficient data points for technical analysis"}
             
        # Calculate Indicators
        rsi = calculate_rsi(closes)
        macd = calculate_macd(closes)
        bb = calculate_bollinger_bands(closes)
        sma_50 = calculate_sma(closes, 50)
        ema_20 = calculate_ema(closes, 20)
        atr = calculate_atr(highs, lows, closes)
        
        # Get latest values
        latest_idx = -1
        
        result = {
            "symbol": symbol,
            "date": dates[latest_idx],
            "price": closes[latest_idx],
            "indicators": {
                "rsi": {
                    "value": round(rsi[latest_idx], 2) if rsi[latest_idx] is not None else None,
                    "condition": "Overbought" if rsi[latest_idx] and rsi[latest_idx] > 70 else "Oversold" if rsi[latest_idx] and rsi[latest_idx] < 30 else "Neutral"
                },
                "macd": {
                    "line": round(macd["macd_line"][latest_idx], 2) if macd["macd_line"][latest_idx] is not None else None,
                    "signal": round(macd["signal_line"][latest_idx], 2) if macd["signal_line"][latest_idx] is not None else None,
                    "histogram": round(macd["histogram"][latest_idx], 2) if macd["histogram"][latest_idx] is not None else None,
                    "trend": "Bullish" if macd["histogram"][latest_idx] and macd["histogram"][latest_idx] > 0 else "Bearish"
                },
                "bollinger_bands": {
                    "upper": round(bb["upper_band"][latest_idx], 2) if bb["upper_band"][latest_idx] is not None else None,
                    "middle": round(bb["middle_band"][latest_idx], 2) if bb["middle_band"][latest_idx] is not None else None,
                    "lower": round(bb["lower_band"][latest_idx], 2) if bb["lower_band"][latest_idx] is not None else None,
                    "width_pct": round(((bb["upper_band"][latest_idx] - bb["lower_band"][latest_idx]) / bb["middle_band"][latest_idx] * 100), 2) if bb["upper_band"][latest_idx] else None
                },
                "moving_averages": {
                    "sma_50": round(sma_50[latest_idx], 2) if sma_50[latest_idx] is not None else None,
                    "ema_20": round(ema_20[latest_idx], 2) if ema_20[latest_idx] is not None else None,
                    "price_vs_sma50": "Above" if sma_50[latest_idx] and closes[latest_idx] > sma_50[latest_idx] else "Below"
                },
                "volatility": {
                    "atr": round(atr[latest_idx], 2) if atr[latest_idx] is not None else None
                }
            }
        }
        
        return result

    except Exception as e:
        logger.error(f"Error in technical analysis: {e}")
        return {"error": str(e)}

# Tool Schema
TECHNICAL_ANALYSIS_SCHEMA = [
    {
        "name": "get_technical_analysis",
        "description": "Get technical analysis indicators (RSI, MACD, Bollinger Bands, Moving Averages) for a stock to determine trends and momentum.",
        "parameters": {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "Stock symbol (e.g., AAPL, TSLA)"
                },
                "period_days": {
                    "type": "integer",
                    "description": "Lookback period for data fetching (default 100 days needed for accurate indicators)",
                    "default": 100
                }
            },
            "required": ["symbol"]
        }
    }
]
