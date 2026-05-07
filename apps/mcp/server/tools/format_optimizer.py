"""
Format Optimizer Component

This module handles the transformation of raw data into user-friendly,
visually appealing formats with consistent styling and visual indicators.
"""

import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP

from .enhanced_models import (
    Performance, SentimentSummary, SentimentBreakdown, NewsEvent,
    SentimentThresholds, RelevanceThresholds, PerformanceThresholds,
    QualityIndicators, VisualIndicators
)

logger = logging.getLogger(__name__)


class FormatOptimizer:
    """
    Base class for formatting raw data into user-friendly presentations.
    
    Handles:
    - Price and percentage formatting with visual indicators
    - Sentiment score normalization and interpretation
    - Time period formatting to human-readable strings
    - News event structuring and quality assessment
    - Visual hierarchy and emoji indicators
    """
    
    def __init__(self, currency_symbol: str = "₹"):
        """
        Initialize the Format Optimizer.
        
        Args:
            currency_symbol: Currency symbol to use for price formatting (default: ₹ for INR)
        """
        self.currency_symbol = currency_symbol
        self.logger = logger
    
    def format_price_change(self, current_price: float, change_value: float, change_percent: float) -> Performance:
        """
        Format price change data with visual indicators.
        
        Args:
            current_price: Current stock price
            change_value: Absolute change in price
            change_percent: Percentage change
            
        Returns:
            Performance object with formatted data and visual indicators
        """
        try:
            # Determine direction and trend indicator
            if change_percent > 0.1:
                direction = "up"
                trend_indicator = VisualIndicators.UP_ARROW
                sign = "+"
            elif change_percent < -0.1:
                direction = "down"
                trend_indicator = VisualIndicators.DOWN_ARROW
                sign = ""  # Negative sign already included
            else:
                direction = "flat"
                trend_indicator = VisualIndicators.FLAT_ARROW
                sign = "+" if change_value >= 0 else ""
            
            # Format change value with currency symbol and sign
            formatted_change = f"{self.currency_symbol}{sign}{abs(change_value):.2f}"
            if change_value < 0:
                formatted_change = f"-{formatted_change}"
            
            # Determine volatility level based on absolute percentage change
            abs_change = abs(change_percent)
            if abs_change >= PerformanceThresholds.HIGH_VOLATILITY:
                volatility = "high"
            elif abs_change >= PerformanceThresholds.MODERATE_VOLATILITY:
                volatility = "moderate"
            else:
                volatility = "low"
            
            return Performance(
                change_percent=round(change_percent, 2),
                change_value=formatted_change,
                direction=direction,
                volatility=volatility,
                trend_indicator=trend_indicator
            )
            
        except Exception as e:
            self.logger.error(f"Error formatting price change: {e}")
            return Performance(
                change_percent=0.0,
                change_value=f"{self.currency_symbol}0.00",
                direction="flat",
                volatility="low",
                trend_indicator=VisualIndicators.FLAT_ARROW
            )
    
    def format_sentiment_score(self, raw_score: float, article_count: int = 0) -> SentimentSummary:
        """
        Normalize and format sentiment scores to human-readable format.
        
        Args:
            raw_score: Raw sentiment score (can be in various ranges)
            article_count: Number of articles used for sentiment calculation
            
        Returns:
            SentimentSummary with normalized score and interpretation
        """
        try:
            # Normalize score to -100 to +100 range
            normalized_score = self._normalize_sentiment_score(raw_score)
            
            # Generate interpretation based on thresholds
            if normalized_score >= SentimentThresholds.VERY_POSITIVE:
                interpretation = "Very Positive"
            elif normalized_score >= SentimentThresholds.POSITIVE:
                interpretation = "Positive"
            elif normalized_score >= SentimentThresholds.NEUTRAL_HIGH:
                interpretation = "Slightly Positive"
            elif normalized_score >= SentimentThresholds.NEUTRAL_LOW:
                interpretation = "Neutral"
            elif normalized_score >= SentimentThresholds.NEGATIVE:
                interpretation = "Slightly Negative"
            elif normalized_score >= SentimentThresholds.VERY_NEGATIVE:
                interpretation = "Negative"
            else:
                interpretation = "Very Negative"
            
            # Determine confidence level based on article count
            if article_count >= 10:
                confidence = "high"
            elif article_count >= 5:
                confidence = "moderate"
            else:
                confidence = "low"
            
            # Create placeholder breakdown (will be populated by actual data)
            breakdown = SentimentBreakdown(positive=0, negative=0, neutral=0)
            
            return SentimentSummary(
                overall_score=round(normalized_score, 1),
                interpretation=interpretation,
                confidence=confidence,
                article_count=article_count,
                breakdown=breakdown
            )
            
        except Exception as e:
            self.logger.error(f"Error formatting sentiment score: {e}")
            return SentimentSummary(
                overall_score=0.0,
                interpretation="Neutral",
                confidence="low",
                article_count=0,
                breakdown=SentimentBreakdown(positive=0, negative=0, neutral=0)
            )
    
    def format_time_period(self, start_date: str, end_date: str) -> str:
        """
        Convert date ranges to human-readable format.
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            
        Returns:
            Human-readable time period description
        """
        try:
            start = datetime.fromisoformat(start_date)
            end = datetime.fromisoformat(end_date)
            delta = end - start
            days = delta.days
            
            # Generate human-readable description
            if days <= 1:
                return "Today"
            elif days <= 7:
                return f"Last {days} days"
            elif days <= 14:
                return "Last 2 weeks"
            elif days <= 30:
                return "Last month"
            elif days <= 90:
                return "Last 3 months"
            elif days <= 180:
                return "Last 6 months"
            elif days <= 365:
                return "Last year"
            else:
                years = days // 365
                return f"Last {years} year{'s' if years > 1 else ''}"
                
        except Exception as e:
            self.logger.error(f"Error formatting time period: {e}")
            return f"{start_date} to {end_date}"
    
    def format_news_event(self, raw_news: Dict[str, Any]) -> NewsEvent:
        """
        Structure and format news event data.
        
        Args:
            raw_news: Raw news data from API
            
        Returns:
            Structured NewsEvent object
        """
        try:
            # Extract and clean title
            title = raw_news.get("title", "").strip()
            if not title:
                title = raw_news.get("headline", "News Update").strip()
            
            # Format date
            date_str = raw_news.get("published_at", "")
            if date_str:
                try:
                    # Extract just the date part (YYYY-MM-DD)
                    date_str = date_str[:10]
                except:
                    date_str = datetime.now().strftime("%Y-%m-%d")
            else:
                date_str = datetime.now().strftime("%Y-%m-%d")
            
            # Get source
            source = raw_news.get("source", raw_news.get("publisher", "Unknown Source"))
            
            # Calculate relevance score
            relevance_score = float(raw_news.get("relevance_score", 0))
            if relevance_score == 0:
                # Fallback relevance calculation if not provided
                relevance_score = self._calculate_relevance_score(raw_news)
            
            # Determine quality based on relevance and source
            if relevance_score >= RelevanceThresholds.HIGH_RELEVANCE:
                quality = QualityIndicators.EXCELLENT
            elif relevance_score >= RelevanceThresholds.MODERATE_RELEVANCE:
                quality = QualityIndicators.GOOD
            elif relevance_score >= RelevanceThresholds.LOW_RELEVANCE:
                quality = QualityIndicators.FAIR
            else:
                quality = QualityIndicators.POOR
            
            # Determine impact from sentiment
            sentiment_score = raw_news.get("sentiment_score", 0)
            if sentiment_score > 0.1:
                impact = "positive"
            elif sentiment_score < -0.1:
                impact = "negative"
            else:
                impact = "neutral"
            
            # Get summary
            summary = raw_news.get("summary", raw_news.get("content", ""))
            if summary and len(summary) > 300:
                summary = summary[:297] + "..."
            
            return NewsEvent(
                title=title,
                date=date_str,
                source=source,
                relevance_score=round(relevance_score, 1),
                quality=quality,
                impact=impact,
                summary=summary,
                url=raw_news.get("url", raw_news.get("link"))
            )
            
        except Exception as e:
            self.logger.error(f"Error formatting news event: {e}")
            return NewsEvent(
                title="News Update",
                date=datetime.now().strftime("%Y-%m-%d"),
                source="Unknown Source",
                relevance_score=0.0,
                quality=QualityIndicators.POOR,
                impact="neutral"
            )
    
    def apply_visual_indicators(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add emoji and visual indicators to data for improved scannability.
        
        Args:
            data: Data dictionary to enhance with visual indicators
            
        Returns:
            Enhanced data with visual indicators
        """
        try:
            enhanced_data = data.copy()
            
            # Add section indicators
            if "performance" in enhanced_data:
                enhanced_data["performance_icon"] = VisualIndicators.CHART
            
            if "sentiment_summary" in enhanced_data:
                sentiment = enhanced_data["sentiment_summary"]
                score = sentiment.get("overall_score", 0)
                if score > 20:
                    enhanced_data["sentiment_icon"] = VisualIndicators.POSITIVE
                elif score < -20:
                    enhanced_data["sentiment_icon"] = VisualIndicators.NEGATIVE
                else:
                    enhanced_data["sentiment_icon"] = VisualIndicators.NEUTRAL
            
            if "key_events" in enhanced_data:
                enhanced_data["news_icon"] = VisualIndicators.NEWS
            
            if "insights" in enhanced_data:
                insights = enhanced_data["insights"]
                if "risk_factors" in insights and insights["risk_factors"]:
                    enhanced_data["risk_icon"] = VisualIndicators.WARNING
            
            return enhanced_data
            
        except Exception as e:
            self.logger.error(f"Error applying visual indicators: {e}")
            return data
    
    def _normalize_sentiment_score(self, raw_score: float) -> float:
        """
        Normalize sentiment score to -100 to +100 range.
        
        Args:
            raw_score: Raw sentiment score in unknown range
            
        Returns:
            Normalized score in -100 to +100 range
        """
        try:
            # Handle different input ranges
            if abs(raw_score) <= 1:
                # Score is already in -1 to 1 range, scale to -100 to 100
                return raw_score * 100
            elif 0 <= raw_score <= 100:
                # Score is in 0-100 range, convert to -100 to 100
                return (raw_score - 50) * 2
            elif -100 <= raw_score <= 100:
                # Score is already in -100 to 100 range
                return raw_score
            else:
                # Unknown range, clamp to reasonable bounds
                return max(-100, min(100, raw_score))
                
        except Exception as e:
            self.logger.error(f"Error normalizing sentiment score: {e}")
            return 0.0
    
    def _calculate_relevance_score(self, news_item: Dict[str, Any]) -> float:
        """
        Calculate relevance score for news item if not provided.
        
        Args:
            news_item: Raw news data
            
        Returns:
            Calculated relevance score (0-100)
        """
        try:
            score = 0.0
            
            # Check for stock symbol match
            if news_item.get("stock_symbol") and news_item.get("stock_symbol") != "N/A":
                score += 50
            
            # Check title and content for relevance indicators
            title = news_item.get("title", "").lower()
            content = news_item.get("content", "").lower()
            
            # Financial keywords boost relevance
            financial_keywords = [
                "earnings", "revenue", "profit", "loss", "quarterly", "annual",
                "stock", "share", "market", "trading", "investment", "dividend",
                "acquisition", "merger", "ipo", "results", "guidance"
            ]
            
            for keyword in financial_keywords:
                if keyword in title:
                    score += 10
                elif keyword in content:
                    score += 5
            
            # Source credibility boost
            source = news_item.get("source", "").lower()
            credible_sources = [
                "reuters", "bloomberg", "economic times", "business standard",
                "moneycontrol", "livemint", "financial express", "cnbc"
            ]
            
            for credible_source in credible_sources:
                if credible_source in source:
                    score += 15
                    break
            
            return min(100, score)
            
        except Exception as e:
            self.logger.error(f"Error calculating relevance score: {e}")
            return 0.0
    
    def format_currency(self, amount: float, precision: int = 2) -> str:
        """
        Format currency amount with proper symbol and separators.
        
        Args:
            amount: Amount to format
            precision: Decimal places (default: 2)
            
        Returns:
            Formatted currency string
        """
        try:
            # Use Decimal for precise formatting
            decimal_amount = Decimal(str(amount)).quantize(
                Decimal('0.01'), rounding=ROUND_HALF_UP
            )
            
            # Format with thousands separators
            formatted = f"{decimal_amount:,.{precision}f}"
            
            return f"{self.currency_symbol}{formatted}"
            
        except Exception as e:
            self.logger.error(f"Error formatting currency: {e}")
            return f"{self.currency_symbol}0.00"
    
    def format_percentage(self, value: float, precision: int = 2, include_sign: bool = True) -> str:
        """
        Format percentage with proper sign and precision.
        
        Args:
            value: Percentage value
            precision: Decimal places (default: 2)
            include_sign: Whether to include + sign for positive values
            
        Returns:
            Formatted percentage string
        """
        try:
            formatted = f"{value:.{precision}f}%"
            
            if include_sign and value > 0:
                formatted = f"+{formatted}"
            
            return formatted
            
        except Exception as e:
            self.logger.error(f"Error formatting percentage: {e}")
            return "0.00%"