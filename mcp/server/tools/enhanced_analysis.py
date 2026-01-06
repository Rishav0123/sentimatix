"""
Enhanced Stock Analysis Tools

This module provides the new MCP tools for enhanced single stock analysis
and multi-stock comparison with improved formatting and actionable insights.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from .format_optimizer import FormatOptimizer
from .insight_generator import InsightGenerator
from .enhanced_models import (
    StockAnalysis, ComparisonResult, StockInfo, create_error_response, create_success_response
)
from server.utils.cache import cache_result

from .stock_tools import get_stock_summary, get_historical_prices
from .news_tools import get_news_sentiment, get_sentiment_aggregate
from .rag_tools import get_rag_evidence
from .correlation import calculate_sentiment_price_correlation
from .technical_analysis import get_technical_analysis

logger = logging.getLogger(__name__)


class EnhancedAnalysisEngine:
    """
    Main engine for enhanced stock analysis and comparison.
    
    Coordinates data fetching, formatting, and insight generation
    to provide user-friendly analysis results.
    """
    
    def __init__(self):
        """Initialize the enhanced analysis engine."""
        self.format_optimizer = FormatOptimizer()
        self.insight_generator = InsightGenerator()
        self.logger = logger
    
    @cache_result(ttl_seconds=300)
    async def analyze_stock_enhanced(
        self,
        symbol: str,
        period: str = "1m",
        analysis_type: str = "detailed",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Enhanced single stock analysis with improved formatting and insights.
        
        Args:
            symbol: Stock symbol (e.g., "HDFCBANK")
            period: Time period ("1d", "1w", "1m", "3m", "6m", "1y")
            analysis_type: Type of analysis ("quick", "detailed", "quarterly")
            start_date: Optional explicit start date (YYYY-MM-DD)
            end_date: Optional explicit end date (YYYY-MM-DD)
            
        Returns:
            Structured analysis result with formatted data and insights
        """
        try:
            self.logger.info(f"Starting enhanced analysis for {symbol}, period: {period}, range: {start_date} to {end_date}")
            
            # Validate inputs
            if not symbol or not isinstance(symbol, str):
                return create_error_response("validation_error", "Invalid symbol provided")
            
            if not start_date or not end_date:
                valid_periods = ["1d", "1w", "1m", "3m", "6m", "1y"]
                if period not in valid_periods:
                    return create_error_response("validation_error", f"Invalid period. Must be one of: {valid_periods}")
            
            # Determine date range
            if start_date and end_date:
                start_date_str = start_date
                end_date_str = end_date
                try:
                    start_dt = datetime.fromisoformat(start_date)
                    end_dt = datetime.fromisoformat(end_date)
                    period_days = (end_dt - start_dt).days
                except:
                    period_days = 30 # Default
            else:
                # Convert period to days for API calls
                period_days = self._period_to_days(period)
                
                # Calculate date range
                end_dt = datetime.now()
                start_dt = end_dt - timedelta(days=period_days)
                start_date_str = start_dt.strftime("%Y-%m-%d")
                end_date_str = end_dt.strftime("%Y-%m-%d")
            
            # Fetch data from existing tools
            stock_summary = get_stock_summary(symbol, period_days)
            if "error" in stock_summary:
                return create_error_response("data_error", f"Failed to fetch stock data: {stock_summary['error']}")
            
            # Fetch more news for theme extraction if needed (top 50)
            news_data_extensive = get_news_sentiment(symbol, start_date_str, end_date_str, top_n=50)
            if news_data_extensive and isinstance(news_data_extensive, list) and len(news_data_extensive) > 0 and "error" in news_data_extensive[0]:
                self.logger.warning(f"Extensive news data fetch failed: {news_data_extensive[0]['error']}")
                news_data_extensive = []
            
            # For display purposes, we still use the top_n=10 from the original logic if needed,
            # but we'll prioritize the intensive set for insights.
            news_data = news_data_extensive[:10]
            if news_data and isinstance(news_data, list) and len(news_data) > 0 and "error" in news_data[0]:
                self.logger.warning(f"News data fetch failed: {news_data[0]['error']}")
                news_data = []  # Continue without news data
            
            sentiment_aggregate = get_sentiment_aggregate(symbol, start_date_str, end_date_str)
            if "error" in sentiment_aggregate:
                self.logger.warning(f"Sentiment aggregate failed: {sentiment_aggregate['error']}")
                sentiment_aggregate = {"avg_sentiment": 0.0, "total_articles": 0}
            
            # Fetch RAG evidence for additional context
            rag_evidence = []
            try:
                # Use a specific query for RAG
                price_dir = "increase" if stock_summary.get("change_percent", 0) >= 0 else "decrease"
                rag_query = f"{symbol} stock price {price_dir} movement analysis reasons factors earnings news developments"
                rag_evidence = get_rag_evidence(symbol, start_date_str, end_date_str, rag_query, top_k=5)
                # Filter out error/status messages if any
                if rag_evidence and isinstance(rag_evidence, list) and "error" in rag_evidence[0]:
                    rag_evidence = []
            except Exception as e:
                self.logger.warning(f"RAG search failed: {e}")
            
            # Calculate correlation if we have sufficient data
            correlation_data = None
            try:
                correlation_result = calculate_sentiment_price_correlation(symbol, start_date_str, end_date_str)
                if correlation_result and "error" not in correlation_result:
                    correlation_data = correlation_result
            except Exception as e:
                self.logger.warning(f"Correlation calculation failed: {e}")
            
            # Fetch Technical Analysis
            technical_data = None
            try:
                # Use standard 100 days for TA
                ta_result = await get_technical_analysis(symbol, period_days=100)
                if ta_result and "error" not in ta_result:
                    technical_data = ta_result
            except Exception as e:
                self.logger.warning(f"Technical analysis failed: {e}")

            # Format the data using FormatOptimizer
            formatted_analysis = self._format_single_stock_analysis(
                symbol, stock_summary, news_data, sentiment_aggregate, correlation_data, rag_evidence, period, technical_data
            )
            
            # Generate insights using InsightGenerator
            # Pass extensive news data for better theme extraction
            insights = self.insight_generator.generate_analysis_insights(formatted_analysis, news_data_extensive)
            formatted_analysis["insights"] = insights.__dict__
            
            # Apply visual indicators
            formatted_analysis = self.format_optimizer.apply_visual_indicators(formatted_analysis)
            
            self.logger.info(f"Enhanced analysis completed for {symbol}")
            return create_success_response(formatted_analysis, {"analysis_type": analysis_type})
            
        except Exception as e:
            self.logger.error(f"Error in enhanced stock analysis: {e}")
            return create_error_response("processing_error", f"Analysis failed: {str(e)}")
    
    @cache_result(ttl_seconds=300)
    async def compare_stocks(
        self,
        symbols: List[str],
        period: str = "1m",
        comparison_type: str = "comprehensive"
    ) -> Dict[str, Any]:
        """
        Multi-stock comparison with side-by-side analysis and rankings.
        
        Args:
            symbols: List of 2-3 stock symbols
            period: Time period for comparison
            comparison_type: Type of comparison ("performance", "sentiment", "comprehensive")
            
        Returns:
            Structured comparison result with rankings and recommendations
        """
        try:
            self.logger.info(f"Starting stock comparison for {symbols}, period: {period}")
            
            # Validate inputs
            if not symbols or not isinstance(symbols, list):
                return create_error_response("validation_error", "Invalid symbols list provided")
            
            if len(symbols) < 2 or len(symbols) > 3:
                return create_error_response("validation_error", "Must provide 2-3 symbols for comparison")
            
            valid_periods = ["1d", "1w", "1m", "3m", "6m", "1y"]
            if period not in valid_periods:
                return create_error_response("validation_error", f"Invalid period. Must be one of: {valid_periods}")
            
            # Fetch analysis for each stock
            stock_analyses = []
            for symbol in symbols:
                analysis_result = await self.analyze_stock_enhanced(symbol, period, "detailed")
                if not analysis_result.get("success"):
                    self.logger.warning(f"Failed to analyze {symbol}: {analysis_result.get('message')}")
                    continue
                stock_analyses.append(analysis_result["data"])
            
            if len(stock_analyses) < 2:
                return create_error_response("data_error", "Insufficient data for comparison")
            
            # Generate comparison result
            comparison_result = self._generate_comparison_result(stock_analyses, period, comparison_type)
            
            self.logger.info(f"Stock comparison completed for {symbols}")
            return create_success_response(comparison_result, {"comparison_type": comparison_type})
            
        except Exception as e:
            self.logger.error(f"Error in stock comparison: {e}")
            return create_error_response("processing_error", f"Comparison failed: {str(e)}")
    
    def _format_single_stock_analysis(
        self,
        symbol: str,
        stock_summary: Dict[str, Any],
        news_data: List[Dict[str, Any]],
        sentiment_aggregate: Dict[str, Any],
        correlation_data: Optional[Dict[str, Any]],
        rag_evidence: List[Dict[str, Any]],
        period: str,
        technical_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Format single stock analysis data using FormatOptimizer."""
        try:
            # Format stock info
            numeric_price = stock_summary.get("current_price", 0)
            change_percent = stock_summary.get("change_percent", 0)
            stock_info = {
                "symbol": symbol,
                "name": f"{symbol} Limited",  # Placeholder
                "current_price": numeric_price,
                "formatted_price": self.format_optimizer.format_currency(numeric_price),
                "change_percent": change_percent,
                "period": self.format_optimizer.format_time_period(
                    (datetime.now() - timedelta(days=self._period_to_days(period))).strftime("%Y-%m-%d"),
                    datetime.now().strftime("%Y-%m-%d")
                )
            }
            
            # Format performance
            performance = self.format_optimizer.format_price_change(
                stock_summary.get("current_price", 0),
                stock_summary.get("change", 0),
                change_percent
            )
            performance_dict = performance.__dict__
            performance_dict["symbol"] = symbol
            
            # Format sentiment
            sentiment_summary = self.format_optimizer.format_sentiment_score(
                sentiment_aggregate.get("avg_sentiment", 0),
                sentiment_aggregate.get("total_articles", 0)
            )
            
            # Update sentiment breakdown with actual data
            sentiment_summary.breakdown.positive = sentiment_aggregate.get("positive_count", 0)
            sentiment_summary.breakdown.negative = sentiment_aggregate.get("negative_count", 0)
            sentiment_summary.breakdown.neutral = sentiment_aggregate.get("neutral_count", 0)
            
            # Backwards compatibility for frontend aliases
            sentiment_dict = sentiment_summary.__dict__
            sentiment_dict["avg_sentiment"] = sentiment_summary.overall_score / 100.0
            sentiment_dict["total_articles"] = sentiment_summary.article_count
            
            # Format news events
            key_events = []
            
            # Combine standard news and RAG evidence
            combined_news_sources = []
            if news_data:
                combined_news_sources.extend(news_data)
            
            if rag_evidence:
                # Convert RAG items to common format if needed (they are already similar)
                combined_news_sources.extend(rag_evidence)
            
            if combined_news_sources:
                # Filter and format top 5 most relevant news events
                # Use RelevanceThresholds.MODERATE_RELEVANCE (40) for better coverage
                relevant_news = [n for n in combined_news_sources if n.get("relevance_score", 0) >= 40]
                if not relevant_news:
                    relevant_news = combined_news_sources  # Use all news if none meet relevance threshold
                
                # Sort by relevance and then by date
                relevant_news.sort(key=lambda x: (x.get("relevance_score", 0), x.get("published_at", "")), reverse=True)
                
                for news_item in relevant_news[:5]:
                    formatted_event = self.format_optimizer.format_news_event(news_item)
                    key_events.append(formatted_event.__dict__)
            
            # Format correlation data
            correlation_formatted = None
            if correlation_data:
                correlation_value = correlation_data.get("correlation", 0)
                sample_size = correlation_data.get("data_points", 0)
                correlation_formatted = self.insight_generator.interpret_correlation(
                    correlation_value, sample_size
                ).__dict__
            
            return {
                "stock_info": stock_info,
                "performance": performance_dict,
                "sentiment_summary": sentiment_summary.__dict__,
                "key_events": key_events,
                "correlation": correlation_formatted,
                "technical_analysis": technical_data,
                "symbol": symbol  # For insight generation
            }
            
        except Exception as e:
            self.logger.error(f"Error formatting single stock analysis: {e}")
            raise
    
    def _generate_comparison_result(
        self,
        stock_analyses: List[Dict[str, Any]],
        period: str,
        comparison_type: str
    ) -> Dict[str, Any]:
        """Generate comparison result from individual stock analyses."""
        try:
            # Extract symbols and performance data
            symbols = [analysis["stock_info"]["symbol"] for analysis in stock_analyses]
            
            # Rank stocks by performance
            performance_rankings = []
            for i, analysis in enumerate(stock_analyses):
                performance = analysis["performance"]
                sentiment = analysis["sentiment_summary"]
                
                # Calculate composite score for ranking
                perf_score = performance["change_percent"]
                sent_score = sentiment["overall_score"] / 100  # Normalize to -1 to 1
                composite_score = perf_score + (sent_score * 2)  # Weight sentiment
                
                performance_rankings.append({
                    "symbol": analysis["stock_info"]["symbol"],
                    "composite_score": composite_score,
                    "performance": performance,
                    "sentiment": {
                        "score": sentiment["overall_score"],
                        "trend": "positive" if sentiment["overall_score"] > 0 else "negative" if sentiment["overall_score"] < 0 else "neutral"
                    },
                    "analysis": analysis
                })
            
            # Sort by composite score
            performance_rankings.sort(key=lambda x: x["composite_score"], reverse=True)
            
            # Assign ranks and identify strengths/weaknesses
            stock_comparison = []
            for rank, stock_data in enumerate(performance_rankings, 1):
                analysis = stock_data["analysis"]
                
                # Identify key strength and weakness
                key_strength = self._identify_key_strength(analysis)
                key_weakness = self._identify_key_weakness(analysis)
                
                stock_comparison.append({
                    "symbol": stock_data["symbol"],
                    "rank": rank,
                    "performance": stock_data["performance"],
                    "sentiment": stock_data["sentiment"],
                    "key_strength": key_strength,
                    "key_weakness": key_weakness
                })
            
            # Generate comparative insights
            best_performer = performance_rankings[0]["symbol"]
            worst_performer = performance_rankings[-1]["symbol"]
            
            comparative_insights = {
                "performance_leader": {
                    "symbol": best_performer,
                    "reason": self._get_performance_reason(performance_rankings[0]["analysis"])
                },
                "sentiment_leader": {
                    "symbol": self._get_sentiment_leader(stock_analyses),
                    "reason": "Highest positive sentiment score"
                }
            }
            
            # Generate recommendation rankings
            recommendation_ranking = []
            for stock_data in performance_rankings:
                analysis = stock_data["analysis"]
                insights = analysis.get("insights", {})
                
                recommendation_ranking.append({
                    "symbol": stock_data["symbol"],
                    "rating": insights.get("recommendation", "HOLD"),
                    "rationale": self._generate_comparison_rationale(stock_data, rank),
                    "confidence": insights.get("confidence_level", "moderate")
                })
            
            return {
                "comparison_summary": {
                    "period": self.format_optimizer.format_time_period(
                        (datetime.now() - timedelta(days=self._period_to_days(period))).strftime("%Y-%m-%d"),
                        datetime.now().strftime("%Y-%m-%d")
                    ),
                    "stocks_analyzed": len(stock_analyses),
                    "best_performer": best_performer,
                    "worst_performer": worst_performer
                },
                "stock_comparison": stock_comparison,
                "comparative_insights": comparative_insights,
                "recommendation_ranking": recommendation_ranking
            }
            
        except Exception as e:
            self.logger.error(f"Error generating comparison result: {e}")
            raise
    
    def _period_to_days(self, period: str) -> int:
        """Convert period string to number of days."""
        period_map = {
            "1d": 1,
            "1w": 7,
            "1m": 30,
            "3m": 90,
            "6m": 180,
            "1y": 365
        }
        return period_map.get(period, 30)
    
    def _identify_key_strength(self, analysis: Dict[str, Any]) -> str:
        """Identify the key strength of a stock from its analysis."""
        try:
            performance = analysis["performance"]
            sentiment = analysis["sentiment_summary"]
            
            if performance["change_percent"] > 5:
                return "Strong price momentum"
            elif sentiment["overall_score"] > 50:
                return "Very positive sentiment"
            elif performance["volatility"] == "low":
                return "Price stability"
            elif sentiment["article_count"] > 10:
                return "High media coverage"
            else:
                return "Balanced fundamentals"
                
        except Exception:
            return "Market presence"
    
    def _identify_key_weakness(self, analysis: Dict[str, Any]) -> str:
        """Identify the key weakness of a stock from its analysis."""
        try:
            performance = analysis["performance"]
            sentiment = analysis["sentiment_summary"]
            
            if performance["change_percent"] < -5:
                return "Significant price decline"
            elif sentiment["overall_score"] < -50:
                return "Very negative sentiment"
            elif performance["volatility"] == "high":
                return "High volatility risk"
            elif sentiment["confidence"] == "low":
                return "Limited sentiment data"
            else:
                return "Market uncertainty"
                
        except Exception:
            return "General market risk"
    
    def _get_performance_reason(self, analysis: Dict[str, Any]) -> str:
        """Get reason for performance leadership."""
        try:
            insights = analysis.get("insights", {})
            key_drivers = insights.get("key_drivers", [])
            
            if key_drivers:
                return key_drivers[0]
            else:
                return "Strong overall performance"
                
        except Exception:
            return "Market leadership"
    
    def _get_sentiment_leader(self, analyses: List[Dict[str, Any]]) -> str:
        """Identify the sentiment leader among stocks."""
        try:
            best_sentiment = -200
            leader = analyses[0]["stock_info"]["symbol"]
            
            for analysis in analyses:
                sentiment_score = analysis["sentiment_summary"]["overall_score"]
                if sentiment_score > best_sentiment:
                    best_sentiment = sentiment_score
                    leader = analysis["stock_info"]["symbol"]
            
            return leader
            
        except Exception:
            return analyses[0]["stock_info"]["symbol"]
    
    def _generate_comparison_rationale(self, stock_data: Dict[str, Any], rank: int) -> str:
        """Generate rationale for stock ranking in comparison."""
        try:
            symbol = stock_data["symbol"]
            performance = stock_data["performance"]
            sentiment = stock_data["sentiment"]
            
            if rank == 1:
                return f"Top performer with {performance['change_percent']:.1f}% gain and {sentiment['trend']} sentiment"
            elif rank == 2:
                return f"Solid performance with {performance['change_percent']:.1f}% change and stable outlook"
            else:
                return f"Underperformed with {performance['change_percent']:.1f}% change, monitor for recovery"
                
        except Exception:
            return "Mixed performance indicators"


# Create global instance
enhanced_engine = EnhancedAnalysisEngine()


# MCP Tool Functions
async def analyze_stock_enhanced(
    symbol: str, 
    period: str = "1m", 
    analysis_type: str = "detailed",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> Dict[str, Any]:
    """
    MCP tool for enhanced single stock analysis.
    
    Args:
        symbol: Stock symbol (e.g., "HDFCBANK")
        period: Time period ("1d", "1w", "1m", "3m", "6m", "1y")
        analysis_type: Type of analysis ("quick", "detailed", "quarterly")
        start_date: Optional start date
        end_date: Optional end date
        
    Returns:
        Enhanced analysis result with formatted data and insights
    """
    return await enhanced_engine.analyze_stock_enhanced(symbol, period, analysis_type, start_date, end_date)


async def compare_stocks(symbols: List[str], period: str = "1m", comparison_type: str = "comprehensive") -> Dict[str, Any]:
    """
    MCP tool for multi-stock comparison.
    
    Args:
        symbols: List of 2-3 stock symbols
        period: Time period for comparison
        comparison_type: Type of comparison ("performance", "sentiment", "comprehensive")
        
    Returns:
        Comparison result with rankings and recommendations
    """
    return await enhanced_engine.compare_stocks(symbols, period, comparison_type)


# Tool Schema for MCP
ENHANCED_ANALYSIS_TOOLS_SCHEMA = [
    {
        "name": "analyze_stock_enhanced",
        "description": "Enhanced single stock analysis with improved formatting, insights, and actionable recommendations",
        "parameters": {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "Stock symbol (e.g., HDFCBANK, RELIANCE, TCS)"
                },
                "period": {
                    "type": "string",
                    "description": "Analysis time period",
                    "enum": ["1d", "1w", "1m", "3m", "6m", "1y"],
                    "default": "1m"
                },
                "analysis_type": {
                    "type": "string",
                    "description": "Type of analysis to perform",
                    "enum": ["quick", "detailed", "quarterly"],
                    "default": "detailed"
                }
            },
            "required": ["symbol"]
        }
    },
    {
        "name": "compare_stocks",
        "description": "Multi-stock comparison with side-by-side analysis, rankings, and investment recommendations",
        "parameters": {
            "type": "object",
            "properties": {
                "symbols": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of 2-3 stock symbols to compare",
                    "minItems": 2,
                    "maxItems": 3
                },
                "period": {
                    "type": "string",
                    "description": "Comparison time period",
                    "enum": ["1d", "1w", "1m", "3m", "6m", "1y"],
                    "default": "1m"
                },
                "comparison_type": {
                    "type": "string",
                    "description": "Type of comparison to perform",
                    "enum": ["performance", "sentiment", "comprehensive"],
                    "default": "comprehensive"
                }
            },
            "required": ["symbols"]
        }
    }
]