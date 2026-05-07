from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

# --- Original Models (kept for backward compatibility) ---
# ... (lines 1-103) ...

class StockPrice(BaseModel):
    date: str = Field(..., description="Date of the price record in YYYY-MM-DD format")
    open: float = Field(..., description="Opening price of the session")
    high: float = Field(..., description="Highest price of the session")
    low: float = Field(..., description="Lowest price of the session")
    close: float = Field(..., description="Closing price of the session")
    volume: int = Field(..., description="Total shares traded in the session")
    change: Optional[float] = Field(None, description="Absolute price change from previous close")
    change_percent: Optional[float] = Field(None, description="Percentage price change from previous close")

# ... (I'll keep the rest of the existing models but add new ones at the bottom)

# --- V1 Specific Models (Optimized for AI/OpenAPI) ---

class V1Entity(BaseModel):
    symbol: str = Field(..., description="The NSE ticker symbol, e.g., RELIANCE.NS", example="RELIANCE.NS")
    name: str = Field(..., description="The full company name", example="Reliance Industries Limited")
    sector: Optional[str] = Field(None, description="The industry sector the company belongs to", example="Oil & Gas")
    exchange: Optional[str] = Field("NSE", description="The stock exchange where the entity is listed")
    country: Optional[str] = Field("India", description="Country of listing")
    sentiment_7d: Optional[float] = Field(None, description="Aggregated sentiment score over the last 7 days (-100 to 100)")
    sentiment_30d: Optional[float] = Field(None, description="Aggregated sentiment score over the last 30 days (-100 to 100)")

class V1NewsItem(BaseModel):
    uuid: str = Field(..., description="Unique identifier for the news article")
    title: str = Field(..., description="Title of the news article")
    snippet: str = Field(..., description="A short summary of the article. Free tier gets truncated snippets.")
    url: str = Field(..., description="Link to the original news source")
    source: str = Field(..., description="The publisher of the news, e.g., MoneyControl, Economic Times")
    published_at: str = Field(..., description="ISO 8601 timestamp of publication")
    sentiment: str = Field(..., description="Categorical sentiment label: positive, negative, neutral, or conflicted")
    sentiment_score: Optional[float] = Field(None, description="NLP-derived sentiment score from -1 (Extremely Bearish) to +1 (Extremely Bullish). Pro+ tier only.")
    confidence: Optional[float] = Field(None, description="AI confidence score in the sentiment analysis (0 to 1). Pro+ tier only.")
    is_market_sensitive: Optional[bool] = Field(None, description="True if the news contains high-volatility keywords like 'Dividend', 'Acquisition', or 'Quarterly Results'. Pro+ tier only.")
    entities: List[V1Entity] = Field(default_factory=list, description="List of stocks/entities mentioned in this article")

class V1NewsMeta(BaseModel):
    found: int = Field(..., description="Total number of articles matching the filter criteria")
    returned: int = Field(..., description="Number of articles returned in this specific response")
    limit: int = Field(..., description="The pagination limit used for the request")
    page: int = Field(..., description="The current page number")
    total_pages: int = Field(..., description="Total number of pages available")

class V1NewsResponse(BaseModel):
    meta: V1NewsMeta
    data: List[V1NewsItem]

class V1EntityResponse(BaseModel):
    data: List[V1Entity]

class V1SentimentResponse(BaseModel):
    data: List[Dict[str, Any]] = Field(..., description="List of sentiment objects for requested symbols")

class V1SectorSentimentItem(BaseModel):
    sector: str = Field(..., description="The name of the industry sector")
    avg_sentiment_score: float = Field(..., description="Weighted average sentiment score for the sector (-1 to 1)")
    sentiment_label: str = Field(..., description="Human-readable label: Bullish or Bearish")
    total_articles: int = Field(..., description="Number of articles analyzed to calculate this score")

class V1SectorSentimentResponse(BaseModel):
    period: str = Field(..., description="The time period analyzed (7d or 30d)")
    data: List[V1SectorSentimentItem]
