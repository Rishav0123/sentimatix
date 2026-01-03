"""
Insight Generator Component

This module generates actionable insights and recommendations from raw analysis data,
transforming technical metrics into plain-language interpretations and investment guidance.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import statistics

from .enhanced_models import (
    AnalysisInsights, CorrelationData, Recommendation,
    SentimentThresholds, PerformanceThresholds, RelevanceThresholds
)

logger = logging.getLogger(__name__)


class InsightGenerator:
    """
    Base class for generating actionable insights from stock analysis data.
    
    Handles:
    - Bottom line summary generation
    - Key driver identification from news and price data
    - Risk factor assessment
    - Investment recommendations with confidence levels
    - Correlation interpretation and trading signals
    """
    
    def __init__(self):
        """Initialize the Insight Generator."""
        self.logger = logger
    
    def generate_bottom_line(self, analysis_data: Dict[str, Any]) -> str:
        """
        Generate a clear 1-2 sentence bottom line summary.
        
        Args:
            analysis_data: Complete analysis data including price, sentiment, and news
            
        Returns:
            Concise bottom line summary
        """
        try:
            symbol = analysis_data.get("symbol", "Stock")
            
            # Extract key metrics
            performance = analysis_data.get("performance", {})
            change_percent = performance.get("change_percent", 0)
            direction = performance.get("direction", "flat")
            
            sentiment = analysis_data.get("sentiment_summary", {})
            sentiment_score = sentiment.get("overall_score", 0)
            sentiment_interpretation = sentiment.get("interpretation", "neutral")
            
            # Generate movement description
            if abs(change_percent) >= PerformanceThresholds.SIGNIFICANT_MOVEMENT:
                movement_desc = f"significant {direction}ward movement"
            elif abs(change_percent) >= 1.0:
                movement_desc = f"moderate {direction}ward movement"
            else:
                movement_desc = "stable performance"
            
            # Generate sentiment description
            if sentiment_score >= SentimentThresholds.POSITIVE:
                sentiment_desc = "positive sentiment"
            elif sentiment_score <= SentimentThresholds.NEGATIVE:
                sentiment_desc = "negative sentiment"
            else:
                sentiment_desc = "neutral sentiment"
            
            # Identify key drivers from news
            key_events = analysis_data.get("key_events", [])
            driver_desc = ""
            if key_events:
                high_relevance_events = [e for e in key_events if e.get("relevance_score", 0) >= RelevanceThresholds.HIGH_RELEVANCE]
                if high_relevance_events:
                    # Extract common themes from high-relevance news
                    themes = self._extract_news_themes(high_relevance_events)
                    if themes:
                        driver_desc = f" driven by {themes[0].lower()}"
            
            # Construct bottom line
            bottom_line = f"{symbol} showed {movement_desc} with {sentiment_desc}{driver_desc}."
            
            # Add second sentence with outlook if significant factors present
            outlook_factors = []
            
            # Check for risk factors
            volatility = performance.get("volatility", "low")
            if volatility == "high":
                outlook_factors.append("high volatility")
            
            # Check correlation strength
            correlation = analysis_data.get("correlation", {})
            if correlation and correlation.get("strength") == "strong":
                outlook_factors.append("strong sentiment-price correlation")
            
            if outlook_factors:
                outlook = f" Monitor {' and '.join(outlook_factors)} for trading opportunities."
                bottom_line += outlook
            
            return bottom_line
            
        except Exception as e:
            self.logger.error(f"Error generating bottom line: {e}")
            return f"{analysis_data.get('symbol', 'Stock')} analysis completed with mixed signals."
    
    def identify_key_drivers(self, news_data: List[Dict[str, Any]], price_data: Dict[str, Any]) -> List[str]:
        """
        Extract main factors affecting stock performance from news and price data.
        
        Args:
            news_data: List of news events
            price_data: Price performance data
            
        Returns:
            List of key driving factors
        """
        try:
            drivers = []
            
            # Analyze news for key themes
            if news_data:
                themes = self._extract_news_themes(news_data)
                drivers.extend(themes[:3])  # Top 3 themes
            
            # Analyze price patterns
            change_percent = price_data.get("change_percent", 0)
            volatility = price_data.get("volatility", "low")
            
            if abs(change_percent) >= PerformanceThresholds.SIGNIFICANT_MOVEMENT:
                if change_percent > 0:
                    drivers.append("Strong price momentum")
                else:
                    drivers.append("Price correction pressure")
            
            if volatility == "high":
                drivers.append("Increased market volatility")
            
            # Remove duplicates and limit to top 5
            unique_drivers = list(dict.fromkeys(drivers))[:5]
            
            return unique_drivers if unique_drivers else ["Market dynamics"]
            
        except Exception as e:
            self.logger.error(f"Error identifying key drivers: {e}")
            return ["Market dynamics"]
    
    def assess_risk_factors(self, volatility: str, sentiment_data: Dict[str, Any], 
                          correlation_data: Optional[Dict[str, Any]] = None) -> List[str]:
        """
        Identify risk factors based on volatility, sentiment, and correlation data.
        
        Args:
            volatility: Volatility level ("low", "moderate", "high")
            sentiment_data: Sentiment analysis results
            correlation_data: Correlation analysis results (optional)
            
        Returns:
            List of identified risk factors
        """
        try:
            risk_factors = []
            
            # Volatility-based risks
            if volatility == "high":
                risk_factors.append("High price volatility")
            elif volatility == "moderate":
                risk_factors.append("Moderate price swings")
            
            # Sentiment-based risks
            sentiment_score = sentiment_data.get("overall_score", 0)
            confidence = sentiment_data.get("confidence", "low")
            
            if sentiment_score <= SentimentThresholds.NEGATIVE:
                risk_factors.append("Negative market sentiment")
            
            if confidence == "low":
                risk_factors.append("Limited sentiment data reliability")
            
            # Correlation-based risks
            if correlation_data:
                correlation_strength = correlation_data.get("strength", "none")
                correlation_value = correlation_data.get("sentiment_price", 0)
                
                if correlation_strength == "strong" and correlation_value < -0.7:
                    risk_factors.append("Strong negative sentiment-price correlation")
            
            # Market structure risks (placeholder for future enhancement)
            # Could add sector-specific risks, market cap risks, etc.
            
            return risk_factors[:4]  # Limit to top 4 risk factors
            
        except Exception as e:
            self.logger.error(f"Error assessing risk factors: {e}")
            return ["General market risk"]
    
    def create_recommendation(self, performance: Dict[str, Any], sentiment: Dict[str, Any], 
                            correlation: Optional[Dict[str, Any]] = None) -> Recommendation:
        """
        Generate investment recommendation with rationale and confidence level.
        
        Args:
            performance: Performance metrics
            sentiment: Sentiment analysis results
            correlation: Correlation analysis results (optional)
            
        Returns:
            Recommendation object with rating, rationale, and confidence
        """
        try:
            symbol = performance.get("symbol", "STOCK")
            change_percent = performance.get("change_percent", 0)
            volatility = performance.get("volatility", "low")
            
            sentiment_score = sentiment.get("overall_score", 0)
            sentiment_confidence = sentiment.get("confidence", "low")
            
            # Scoring system for recommendation
            score = 0
            factors = []
            
            # Performance scoring
            if change_percent > PerformanceThresholds.SIGNIFICANT_MOVEMENT:
                score += 2
                factors.append("strong positive momentum")
            elif change_percent > 1.0:
                score += 1
                factors.append("positive momentum")
            elif change_percent < -PerformanceThresholds.SIGNIFICANT_MOVEMENT:
                score -= 2
                factors.append("significant decline")
            elif change_percent < -1.0:
                score -= 1
                factors.append("negative momentum")
            
            # Sentiment scoring
            if sentiment_score >= SentimentThresholds.POSITIVE:
                score += 2
                factors.append("positive sentiment")
            elif sentiment_score >= SentimentThresholds.NEUTRAL_HIGH:
                score += 1
                factors.append("favorable sentiment")
            elif sentiment_score <= SentimentThresholds.NEGATIVE:
                score -= 2
                factors.append("negative sentiment")
            elif sentiment_score <= SentimentThresholds.NEUTRAL_LOW:
                score -= 1
                factors.append("weak sentiment")
            
            # Volatility adjustment
            if volatility == "high":
                score -= 1
                factors.append("high volatility risk")
            
            # Correlation consideration
            if correlation:
                correlation_strength = correlation.get("strength", "none")
                if correlation_strength == "strong":
                    factors.append("strong sentiment-price correlation")
            
            # Determine recommendation
            if score >= 3:
                rating = "BUY"
                action_rationale = "Strong fundamentals and positive momentum"
            elif score >= 1:
                rating = "HOLD"
                action_rationale = "Mixed signals with slight positive bias"
            elif score <= -3:
                rating = "SELL"
                action_rationale = "Weak fundamentals and negative momentum"
            elif score <= -1:
                rating = "HOLD"
                action_rationale = "Mixed signals with slight negative bias"
            else:
                rating = "HOLD"
                action_rationale = "Neutral outlook with balanced factors"
            
            # Determine confidence level
            confidence_factors = 0
            if sentiment_confidence == "high":
                confidence_factors += 1
            if abs(change_percent) >= 2.0:  # Clear price signal
                confidence_factors += 1
            if len(factors) >= 3:  # Multiple supporting factors
                confidence_factors += 1
            
            if confidence_factors >= 2:
                confidence = "high"
            elif confidence_factors >= 1:
                confidence = "moderate"
            else:
                confidence = "low"
            
            # Build rationale
            if factors:
                rationale = f"{action_rationale} based on {', '.join(factors[:3])}"
            else:
                rationale = action_rationale
            
            return Recommendation(
                symbol=symbol,
                rating=rating,
                rationale=rationale,
                confidence=confidence
            )
            
        except Exception as e:
            self.logger.error(f"Error creating recommendation: {e}")
            return Recommendation(
                symbol=performance.get("symbol", "STOCK"),
                rating="HOLD",
                rationale="Unable to determine clear direction",
                confidence="low"
            )
    
    def interpret_correlation(self, correlation_value: float, sample_size: int = 0) -> CorrelationData:
        """
        Generate plain-language interpretation of correlation strength and trading signals.
        
        Args:
            correlation_value: Correlation coefficient (-1 to 1)
            sample_size: Number of data points used for correlation
            
        Returns:
            CorrelationData with interpretation and trading signals
        """
        try:
            abs_correlation = abs(correlation_value)
            
            # Determine strength
            if abs_correlation >= 0.8:
                strength = "strong"
            elif abs_correlation >= 0.5:
                strength = "moderate"
            elif abs_correlation >= 0.3:
                strength = "weak"
            else:
                strength = "none"
            
            # Generate interpretation
            if strength == "none":
                interpretation = "Sentiment and price show no meaningful correlation"
                trading_signal = None
            elif correlation_value > 0:
                interpretation = f"Sentiment and price move in the same direction ({strength} positive correlation)"
                if strength == "strong":
                    trading_signal = "Follow sentiment trends for directional trades"
                else:
                    trading_signal = "Sentiment may provide directional guidance"
            else:
                interpretation = f"Sentiment and price move in opposite directions ({strength} negative correlation)"
                if strength == "strong":
                    trading_signal = "Consider contrarian strategy - negative sentiment may signal buying opportunity"
                else:
                    trading_signal = "Monitor sentiment for potential contrarian signals"
            
            # Adjust confidence based on sample size
            if sample_size > 0 and sample_size < 10:
                interpretation += " (limited data - use with caution)"
            
            return CorrelationData(
                sentiment_price=round(correlation_value, 3),
                strength=strength,
                interpretation=interpretation,
                trading_signal=trading_signal
            )
            
        except Exception as e:
            self.logger.error(f"Error interpreting correlation: {e}")
            return CorrelationData(
                sentiment_price=0.0,
                strength="none",
                interpretation="Unable to determine correlation",
                trading_signal=None
            )
    
    def generate_analysis_insights(self, analysis_data: Dict[str, Any], extensive_news: Optional[List[Dict[str, Any]]] = None) -> AnalysisInsights:
        """
        Generate complete insights package from analysis data.
        
        Args:
            analysis_data: Complete analysis data
            extensive_news: Larger list of news articles for theme extraction
            
        Returns:
            AnalysisInsights object with all generated insights
        """
        try:
            # Generate bottom line
            bottom_line = self.generate_bottom_line(analysis_data)
            
            # Identify key drivers
            news_data = analysis_data.get("key_events", [])
            performance = analysis_data.get("performance", {})
            key_drivers = self.identify_key_drivers(news_data, performance)
            
            # Extract market themes from extensive news if available, otherwise from key_events
            theme_source = extensive_news if extensive_news else news_data
            market_themes = self._extract_news_themes(theme_source)
            
            # Assess risk factors
            volatility = performance.get("volatility", "low")
            sentiment = analysis_data.get("sentiment_summary", {})
            correlation = analysis_data.get("correlation")
            risk_factors = self.assess_risk_factors(volatility, sentiment, correlation)
            
            # Create recommendation
            recommendation = self.create_recommendation(performance, sentiment, correlation)
            
            return AnalysisInsights(
                bottom_line=bottom_line,
                key_drivers=key_drivers,
                risk_factors=risk_factors,
                recommendation=recommendation.rating,
                confidence_level=recommendation.confidence,
                market_themes=market_themes
            )
            
        except Exception as e:
            self.logger.error(f"Error generating analysis insights: {e}")
            return AnalysisInsights(
                bottom_line="Analysis completed with mixed results",
                key_drivers=["Market dynamics"],
                risk_factors=["General market risk"],
                recommendation="HOLD",
                confidence_level="low"
            )
    
    def _extract_news_themes(self, news_events: List[Dict[str, Any]]) -> List[str]:
        """
        Extract common themes and generate a 4-5 point summary from news events.
        """
        try:
            if not news_events:
                return ["No significant news themes identified."]
                
            theme_summaries = []
            
            # 1. Earnings and Financial Results
            earnings_news = [e for e in news_events if any(k in e.get("title", "").lower() for k in ["earnings", "quarterly", "results", "profit", "profitability", "pat"])]
            if earnings_news:
                # Group by sentiment
                pos = len([e for e in earnings_news if e.get("impact") == "positive"])
                neg = len([e for e in earnings_news if e.get("impact") == "negative"])
                if pos > neg:
                    theme_summaries.append(f"Strong earnings performance reported with {pos} positive updates regarding quarterly growth and profitability.")
                elif neg > pos:
                    theme_summaries.append(f"Mixed-to-negative earnings results observed with concerns over margins and revenue growth in {len(earnings_news)} articles.")
                else:
                    theme_summaries.append(f"Quarterly results were a focal point with {len(earnings_news)} articles discussing recent financial updates and performance metrics.")

            # 2. Analyst Ratings and Price Targets
            analyst_news = [e for e in news_events if any(k in e.get("title", "").lower() for k in ["buy", "sell", "target", "rating", "neutral", "recommend", "broker", "brokerage"])]
            if analyst_news:
                # Find most mentioned target if possible, or just summarize sentiment
                buys = len([e for e in analyst_news if "buy" in e.get("title", "").lower()])
                if buys > len(analyst_news) / 2:
                    theme_summaries.append(f"Bullish analyst sentiment with {buys} 'Buy' recommendations and positive price target revisions.")
                else:
                    theme_summaries.append(f"Active analyst coverage with analysts debated the stock's valuation and adjusting price targets based on market conditions.")

            # 3. Market and Price Action
            market_news = [e for e in news_events if any(k in e.get("title", "").lower() for k in ["price", "movement", "trading", "volume", "shares", "live", "stock update"])]
            if market_news:
                theme_summaries.append(f"High trading activity and significant price volatility tracked across {len(market_news)} recent market updates.")

            # 4. Corporate and Strategic Developments
            corp_news = [e for e in news_events if any(k in e.get("title", "").lower() for k in ["acquisition", "dividend", "merger", "partnership", "collaboration", "management", "contract"])]
            if corp_news:
                top_corp = corp_news[0].get("title", "")
                if len(top_corp) > 80: top_corp = top_corp[:77] + "..."
                theme_summaries.append(f"Strategic corporate updates including: {top_corp}")

            # 5. Generic/Industry context
            if len(theme_summaries) < 4:
                theme_summaries.append("Broader market trends and sector-specific news influenced general investor sentiment during this period.")

            # Limit to 5 points
            return theme_summaries[:5]
            
        except Exception as e:
            self.logger.error(f"Error extracting news themes: {e}")
            return ["Consistent market interest observed with mixed news sentiment."]
