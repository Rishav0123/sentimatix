"""
Correlation Analysis Tool - Calculate correlations between metrics
"""

from typing import Dict, Any, List, Optional
import logging
import numpy as np

logger = logging.getLogger(__name__)


def calculate_correlation(
    series_a: List[float],
    series_b: List[float],
    series_a_name: str = "Series A",
    series_b_name: str = "Series B"
) -> Dict[str, Any]:
    """
    Calculate correlation between two time series.
    
    Args:
        series_a: First time series (e.g., price changes)
        series_b: Second time series (e.g., sentiment scores)
        series_a_name: Name of first series (for reporting)
        series_b_name: Name of second series (for reporting)
    
    Returns:
        Dict with correlation coefficient, p-value, strength, and interpretation
    """
    try:
        if len(series_a) != len(series_b):
            return {"error": "Series must have equal length"}
        
        if len(series_a) < 3:
            return {"error": "Need at least 3 data points for correlation"}
        
        # Convert to numpy arrays
        a = np.array(series_a)
        b = np.array(series_b)
        
        # Guard against zero variance to prevent NaNs
        if np.std(a) == 0 or np.std(b) == 0:
            return {
                "series_a_name": series_a_name,
                "series_b_name": series_b_name,
                "correlation_coefficient": None,
                "r_squared": None,
                "direction": "none",
                "strength": "NO_VARIANCE",
                "data_points": len(series_a),
                "interpretation": f"Insufficient variance in one or both series to compute correlation between {series_a_name} and {series_b_name}.",
                "statistical_significance": "NOT_APPLICABLE"
            }

        # Calculate Pearson correlation safely
        correlation_matrix = np.corrcoef(a, b)
        correlation = correlation_matrix[0, 1]
        
        # Calculate R-squared
        r_squared = correlation ** 2
        
        # Interpret strength
        strength = _interpret_correlation_strength(abs(correlation))
        direction = "positive" if correlation > 0 else "negative" if correlation < 0 else "none"
        
        result = {
            "series_a_name": series_a_name,
            "series_b_name": series_b_name,
            "correlation_coefficient": round(correlation, 3),
            "r_squared": round(r_squared, 3),
            "direction": direction,
            "strength": strength,
            "data_points": len(series_a),
            "interpretation": _generate_interpretation(correlation, series_a_name, series_b_name),
            "statistical_significance": _assess_significance(correlation, len(series_a))
        }
        
        logger.info(f"Correlation between {series_a_name} and {series_b_name}: {correlation:.3f} ({strength})")
        
        return result
        
    except Exception as e:
        logger.error(f"Error calculating correlation: {e}")
        return {"error": str(e)}


def calculate_sentiment_price_correlation(
    price_changes: List[float],
    sentiment_scores: List[float],
    symbol: str = "Stock"
) -> Dict[str, Any]:
    """
    Specialized correlation calculation for sentiment vs price.
    
    Args:
        price_changes: List of daily/period price change percentages
        sentiment_scores: List of corresponding sentiment scores
        symbol: Stock symbol (for reporting)
    
    Returns:
        Dict with correlation analysis and actionable insights
    """
    try:
        result = calculate_correlation(
            series_a=price_changes,
            series_b=sentiment_scores,
            series_a_name=f"{symbol} Price Change %",
            series_b_name=f"{symbol} Sentiment Score"
        )
        
        if "error" in result:
            return result
        
        # Add sentiment-specific insights
        correlation = result["correlation_coefficient"]
        
        # Actionable insights
        if abs(correlation) > 0.7:
            result["actionable_insight"] = f"Strong {result['direction']} correlation suggests sentiment is a reliable indicator for {symbol}"
            result["recommendation"] = "Monitor sentiment closely for trading signals"
        elif abs(correlation) > 0.4:
            result["actionable_insight"] = f"Moderate {result['direction']} correlation - sentiment has some predictive value"
            result["recommendation"] = "Use sentiment as one of multiple indicators"
        else:
            result["actionable_insight"] = "Weak correlation - sentiment alone may not predict price movements"
            result["recommendation"] = "Consider other fundamental and technical factors"
        
        # Detect anomalies (sentiment-price divergence)
        divergences = _detect_divergences(price_changes, sentiment_scores)
        if divergences:
            result["divergence_periods"] = divergences
            result["divergence_count"] = len(divergences)
        
        return result
        
    except Exception as e:
        logger.error(f"Error in sentiment-price correlation: {e}")
        return {"error": str(e)}


def _interpret_correlation_strength(abs_corr: float) -> str:
    """Interpret correlation coefficient strength"""
    if abs_corr >= 0.9:
        return "VERY_STRONG"
    elif abs_corr >= 0.7:
        return "STRONG"
    elif abs_corr >= 0.5:
        return "MODERATE"
    elif abs_corr >= 0.3:
        return "WEAK"
    else:
        return "VERY_WEAK"


def _generate_interpretation(corr: float, name_a: str, name_b: str) -> str:
    """Generate human-readable interpretation"""
    abs_corr = abs(corr)
    strength = _interpret_correlation_strength(abs_corr)
    direction = "positive" if corr > 0 else "negative"
    
    if strength in ["VERY_STRONG", "STRONG"]:
        return f"There is a {strength.lower().replace('_', ' ')} {direction} relationship between {name_a} and {name_b}. When one increases, the other tends to {'increase' if corr > 0 else 'decrease'} as well."
    elif strength == "MODERATE":
        return f"There is a moderate {direction} relationship. {name_a} and {name_b} show some tendency to move {'together' if corr > 0 else 'in opposite directions'}."
    else:
        return f"There is little to no clear relationship between {name_a} and {name_b}. They appear to move independently."


def _assess_significance(corr: float, n: int) -> str:
    """Assess statistical significance (simple rule of thumb)"""
    # For small samples, need stronger correlation
    if n < 10:
        threshold = 0.6
    elif n < 30:
        threshold = 0.4
    else:
        threshold = 0.3
    
    if abs(corr) >= threshold:
        return "LIKELY_SIGNIFICANT"
    else:
        return "NOT_SIGNIFICANT"


def _detect_divergences(
    series_a: List[float],
    series_b: List[float],
    threshold: float = 1.5
) -> List[Dict[str, Any]]:
    """Detect periods where sentiment and price diverge significantly"""
    divergences = []
    
    try:
        for i in range(len(series_a)):
            # Normalize both series
            a_norm = series_a[i]
            b_norm = series_b[i]
            
            # Check for significant divergence
            if a_norm > threshold and b_norm < -threshold:
                divergences.append({
                    "index": i,
                    "type": "bullish_price_bearish_sentiment",
                    "price_change": round(a_norm, 2),
                    "sentiment": round(b_norm, 2)
                })
            elif a_norm < -threshold and b_norm > threshold:
                divergences.append({
                    "index": i,
                    "type": "bearish_price_bullish_sentiment",
                    "price_change": round(a_norm, 2),
                    "sentiment": round(b_norm, 2)
                })
        
        return divergences
        
    except Exception as e:
        logger.warning(f"Error detecting divergences: {e}")
        return []


# Tool Schema for MCP
CORRELATION_TOOLS_SCHEMA = [
    {
        "name": "calculate_correlation",
        "description": "Calculate statistical correlation between two time series (e.g., price vs sentiment, price vs volume)",
        "parameters": {
            "type": "object",
            "properties": {
                "series_a": {
                    "type": "array",
                    "items": {"type": "number"},
                    "description": "First time series data (e.g., daily price changes)"
                },
                "series_b": {
                    "type": "array",
                    "items": {"type": "number"},
                    "description": "Second time series data (e.g., sentiment scores)"
                },
                "series_a_name": {
                    "type": "string",
                    "description": "Name of first series for reporting",
                    "default": "Series A"
                },
                "series_b_name": {
                    "type": "string",
                    "description": "Name of second series for reporting",
                    "default": "Series B"
                }
            },
            "required": ["series_a", "series_b"]
        }
    },
    {
        "name": "calculate_sentiment_price_correlation",
        "description": "Specialized correlation analysis between sentiment scores and price changes with actionable insights",
        "parameters": {
            "type": "object",
            "properties": {
                "price_changes": {
                    "type": "array",
                    "items": {"type": "number"},
                    "description": "Price change percentages over time"
                },
                "sentiment_scores": {
                    "type": "array",
                    "items": {"type": "number"},
                    "description": "Corresponding sentiment scores"
                },
                "symbol": {
                    "type": "string",
                    "description": "Stock symbol for reporting",
                    "default": "Stock"
                }
            },
            "required": ["price_changes", "sentiment_scores"]
        }
    }
]
