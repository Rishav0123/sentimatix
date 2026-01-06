"""
Data Models for Enhanced Stock Analysis System

This module defines the data structures used for enhanced stock analysis
and comparison responses, ensuring consistent formatting and structure.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime


@dataclass
class StockInfo:
    """Basic stock information"""
    symbol: str
    name: str
    current_price: str  # Formatted with currency symbol
    period: str  # Human-readable period description


@dataclass
class Performance:
    """Stock performance metrics"""
    change_percent: float
    change_value: str  # Formatted with currency and sign
    direction: str  # "up", "down", "flat"
    volatility: str  # "low", "moderate", "high"
    trend_indicator: str  # Emoji indicator (📈, 📉, ➡️)


@dataclass
class SentimentBreakdown:
    """Sentiment distribution breakdown"""
    positive: int
    negative: int
    neutral: int


@dataclass
class SentimentSummary:
    """Aggregated sentiment analysis"""
    overall_score: float  # Normalized to -100 to +100 range
    interpretation: str  # "Very Positive", "Positive", "Neutral", "Negative", "Very Negative"
    confidence: str  # "high", "moderate", "low"
    article_count: int
    breakdown: SentimentBreakdown


@dataclass
class NewsEvent:
    """Individual news event with structured information"""
    title: str
    date: str  # YYYY-MM-DD format
    source: str
    relevance_score: float  # 0-100 scale
    quality: str  # "EXCELLENT", "GOOD", "FAIR", "POOR"
    impact: str  # "positive", "negative", "neutral"
    summary: Optional[str] = None
    url: Optional[str] = None


@dataclass
class AnalysisInsights:
    """Generated insights and recommendations"""
    bottom_line: str  # 1-2 sentence summary
    key_drivers: List[str]  # Main factors affecting performance
    risk_factors: List[str]  # Identified risks
    recommendation: str  # Investment recommendation
    confidence_level: str  # "high", "moderate", "low"
    market_themes: List[str] = field(default_factory=list) # 4-5 key summary points


@dataclass
class CorrelationData:
    """Correlation analysis results"""
    sentiment_price: float  # Correlation coefficient
    strength: str  # "strong", "moderate", "weak", "none"
    interpretation: str  # Plain language explanation
    trading_signal: Optional[str] = None  # Trading recommendation based on correlation


@dataclass
class StockAnalysis:
    """Complete single stock analysis result"""
    stock_info: StockInfo
    performance: Performance
    sentiment_summary: SentimentSummary
    key_events: List[NewsEvent]
    insights: AnalysisInsights
    correlation: Optional[CorrelationData] = None
    technical_analysis: Optional[Dict[str, Any]] = None


@dataclass
class StockRanking:
    """Individual stock ranking in comparison"""
    symbol: str
    rank: int
    performance: Performance
    sentiment: Dict[str, Any]  # Simplified sentiment data for comparison
    key_strength: str
    key_weakness: str


@dataclass
class ComparisonInsights:
    """Insights from multi-stock comparison"""
    performance_leader: Dict[str, str]  # symbol and reason
    sentiment_leader: Dict[str, str]  # symbol and reason
    key_differences: List[str]  # Notable differences between stocks


@dataclass
class Recommendation:
    """Investment recommendation with rationale"""
    symbol: str
    rating: str  # "BUY", "HOLD", "SELL"
    rationale: str
    confidence: str  # "high", "moderate", "low"


@dataclass
class ComparisonSummary:
    """Summary of comparison analysis"""
    period: str
    stocks_analyzed: int
    best_performer: str
    worst_performer: str


@dataclass
class ComparisonResult:
    """Complete multi-stock comparison result"""
    comparison_summary: ComparisonSummary
    stock_comparison: List[StockRanking]
    comparative_insights: ComparisonInsights
    recommendation_ranking: List[Recommendation]


@dataclass
class ErrorResponse:
    """Structured error response"""
    success: bool = False
    error_type: str = "unknown"
    message: str = "An error occurred"
    details: Optional[Dict[str, Any]] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class SuccessResponse:
    """Structured success response wrapper"""
    success: bool = True
    data: Any = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Optional[Dict[str, Any]] = None


# Helper functions for creating common response structures
def create_error_response(error_type: str, message: str, details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Create a standardized error response"""
    error = ErrorResponse(
        error_type=error_type,
        message=message,
        details=details
    )
    return {
        "success": False,
        "error": error.error_type,
        "message": error.message,
        "details": error.details,
        "timestamp": error.timestamp
    }


def create_success_response(data: Any, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Create a standardized success response"""
    response = SuccessResponse(data=data, metadata=metadata)
    return {
        "success": True,
        "data": response.data,
        "timestamp": response.timestamp,
        "metadata": response.metadata
    }


# Constants for formatting and validation
class SentimentThresholds:
    """Sentiment score thresholds for interpretation"""
    VERY_POSITIVE = 60
    POSITIVE = 20
    NEUTRAL_HIGH = 10
    NEUTRAL_LOW = -10
    NEGATIVE = -20
    VERY_NEGATIVE = -60


class RelevanceThresholds:
    """News relevance score thresholds"""
    HIGH_RELEVANCE = 70
    MODERATE_RELEVANCE = 40
    LOW_RELEVANCE = 20


class PerformanceThresholds:
    """Performance change thresholds"""
    SIGNIFICANT_MOVEMENT = 5.0  # Percentage change considered significant
    HIGH_VOLATILITY = 3.0  # Daily volatility threshold for "high"
    MODERATE_VOLATILITY = 1.5  # Daily volatility threshold for "moderate"


class QualityIndicators:
    """News quality indicators"""
    EXCELLENT = "EXCELLENT"
    GOOD = "GOOD"
    FAIR = "FAIR"
    POOR = "POOR"


# Visual indicators for formatting
class VisualIndicators:
    """Emoji and visual indicators for data presentation"""
    UP_ARROW = "📈"
    DOWN_ARROW = "📉"
    FLAT_ARROW = "➡️"
    MONEY = "💰"
    NEWS = "📰"
    WARNING = "⚠️"
    POSITIVE = "✅"
    NEGATIVE = "❌"
    NEUTRAL = "➖"
    STAR = "⭐"
    FIRE = "🔥"
    CHART = "📊"