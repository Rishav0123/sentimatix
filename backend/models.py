from typing import List, Dict, Any, Optional




# Place these at the end of the file, after NewsItem is defined:

from pydantic import BaseModel

class MetaData(BaseModel):
    found: int
    returned: int
    limit: int
    page: int

class NewsListResponse(BaseModel):
    meta: MetaData
    data: List['NewsItem']
from pydantic import BaseModel
from typing import Optional, List

class StockPrice(BaseModel):
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: int
    change: Optional[float] = None
    change_percent: Optional[float] = None

class StockInfo(BaseModel):
    symbol: str
    name: str
    last_price: float
    change: float
    change_percent: float
    volume: int

class MarketIndex(BaseModel):
    symbol: str
    name: str
    value: float
    change: float
    change_percent: float

class StockSummary(BaseModel):
    symbol: str
    name: str
    last_price: float
    change: float
    change_percent: float
    volume: int
    sentiment_score: Optional[float] = None
    sector: Optional[str] = None
    country: Optional[str] = None

class TechnicalIndicators(BaseModel):
    rsi: float
    macd: float
    sma: float
    ema: float

class ModelMetrics(BaseModel):
    accuracy: float
    precision: float
    recall: float
    f1_score: float

class Prediction(BaseModel):
    id: str
    stock_symbol: str
    predicted_price: float
    predicted_change: float
    confidence: float
    current_price: float
    direction: str
    prediction_date: str
    model_metrics: ModelMetrics
    technical_indicators: TechnicalIndicators

class NewsItem(BaseModel):
    id: str
    title: str
    content: str
    url: str
    source: str
    stock_symbol: str
    published_at: str
    sentiment: str
    impact_score: float
    country: Optional[str] = None
    sector: Optional[str] = None
    type: Optional[str] = None
    stock_name: Optional[str] = None

class MarketOverview(BaseModel):
    indices: List[MarketIndex]
    top_gainers: List[StockSummary]
    top_losers: List[StockSummary]
    most_active: List[StockSummary]
    timestamp: str

class SentimentTrend(BaseModel):
    date: str
    sentiment: str
    score: float
