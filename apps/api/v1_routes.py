from fastapi import APIRouter, Depends, HTTPException, Query, Security, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, List
import os
from datetime import datetime, timedelta
from supabase import create_client, Client
from mixpanel import Mixpanel
import logging
from rapidapi_auth import get_rapidapi_tier, is_rapidapi_request


logger = logging.getLogger(__name__)

# Mixpanel analytics integration initialized
MIXPANEL_TOKEN = os.getenv("MIXPANEL_TOKEN")
mp = Mixpanel(MIXPANEL_TOKEN) if MIXPANEL_TOKEN else None

def track_api_call(user_id: str, endpoint: str, tier: str, properties: dict = None):
    if mp:
        props = properties or {}
        props.update({"endpoint": endpoint, "tier": tier})
        try:
            mp.track(user_id, 'api_request_made', props)
        except Exception as e:
            logger.error(f"Mixpanel tracking error: {e}")

# Initialize Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

from models import (
    V1NewsResponse, V1EntityResponse, V1SentimentResponse, V1SectorSentimentResponse
)

v1_router = APIRouter(prefix="/api/v1", tags=["API v1"])

# auto_error=False so RapidAPI requests (no Bearer token) are not auto-rejected
security = HTTPBearer(auto_error=False)

def get_api_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
):
    """
    Dual-auth dependency: supports both RapidAPI proxy requests and
    existing Supabase Bearer token requests in parallel.
    """
    # --- Path 1: RapidAPI Proxy Request ---
    # RapidAPI injects X-RapidAPI-Proxy-Secret; no Bearer token is present.
    if is_rapidapi_request(request):
        tier = get_rapidapi_tier(request)  # validates secret, raises 403 if invalid
        rapidapi_user = request.headers.get("x-rapidapi-user", "rapidapi_anonymous")
        # Return a synthetic user dict compatible with the rest of the codebase
        return {
            "id": f"rapidapi_{rapidapi_user}",
            "email": f"{rapidapi_user}@rapidapi",
            "tier": tier,
            "source": "rapidapi"
        }

    # --- Path 2: Existing Supabase Bearer Token ---
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Authentication required. Provide a Bearer token or use the RapidAPI marketplace."
        )
    token = credentials.credentials
    try:
        response = supabase.table('users').select('*').eq('authentication_key', token).execute()
        if not response.data:
            raise HTTPException(status_code=401, detail="Invalid API Key")
        return response.data[0]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Auth error: {str(e)}")
        raise HTTPException(status_code=401, detail="Authentication failed")

def get_user_tier(user: dict = Depends(get_api_user)):
    # Defaults to 'free' if 'tier' column is missing or null
    return user.get('tier') or 'free'

# ---------------------------------------------------------
# 1. GET /api/v1/news (The Core Product)
# ---------------------------------------------------------
@v1_router.get(
    "/news",
    response_model=V1NewsResponse,
    summary="Search Indian Financial News",
    description="""
    Retrieves a paginated list of financial news articles for NSE-listed companies. 
    Use this endpoint to get real-time sentiment, market-sensitive alerts, and 
    company-specific news. AIs should use this to understand the 'why' behind stock price movements.
    """
)
async def get_news(
    symbols: Optional[str] = Query(None, description="Comma-separated NSE tickers e.g. 'RELIANCE,TCS'. Tickers are automatically suffixed with .NS if missing.", examples={"default": {"value": "RELIANCE,HDFCBANK"}}),
    sectors: Optional[str] = Query(None, description="Comma-separated industry sectors e.g. 'Banking,IT Services'", examples={"default": {"value": "Banking,Automobile"}}),
    sentiment: Optional[str] = Query(None, description="Filter by categorical sentiment: positive, negative, neutral, or conflicted", examples={"default": {"value": "positive"}}),
    published_before: Optional[str] = Query(None, description="Filter articles published before this date (YYYY-MM-DD)", examples={"default": {"value": "2024-01-01"}}),
    published_after: Optional[str] = Query(None, description="Filter articles published after this date (YYYY-MM-DD)", examples={"default": {"value": "2024-01-01"}}),
    only_market_sensitive: bool = Query(False, description="If true, only returns high-impact news (e.g., M&A, Dividends, Earnings). Requires Pro+ tier."),
    limit: int = Query(10, description="Number of results to return per page. Max 100 for Pro, 1000 for Enterprise.", ge=1, le=1000),
    page: int = Query(1, description="Pagination page number", ge=1),
    user: dict = Depends(get_api_user),
    tier: str = Depends(get_user_tier)
):
    try:
        track_api_call(user.get('id', 'unknown'), '/api/v1/news', tier, {"symbols": symbols, "sentiment": sentiment})
        # Tier Enforcements
        if tier == 'free':
            limit = min(limit, 3)
            # Force published_after to be at most 7 days ago
            seven_days_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
            if not published_after or published_after < seven_days_ago:
                published_after = seven_days_ago
        else:
            limit = min(limit, 1000 if tier == 'enterprise' else 100)

        query = supabase.table('news').select('*')
        count_query = supabase.table('news').select('id', count='estimated')

        if symbols:
            sym_list = [s.strip().upper() + '.NS' if not s.endswith('.NS') else s.strip().upper() for s in symbols.split(',')]
            query = query.in_('yfin_symbol', sym_list)
            count_query = count_query.in_('yfin_symbol', sym_list)
            
        if sectors:
            sec_list = [s.strip() for s in sectors.split(',')]
            query = query.in_('sector', sec_list)
            count_query = count_query.in_('sector', sec_list)

        if sentiment:
            query = query.eq('sentiment', sentiment.lower())
            count_query = count_query.eq('sentiment', sentiment.lower())

        if published_after:
            query = query.gte('published_at', f"{published_after}T00:00:00Z")
            count_query = count_query.gte('published_at', f"{published_after}T00:00:00Z")
            
        if published_before:
            query = query.lte('published_at', f"{published_before}T23:59:59Z")
            count_query = count_query.lte('published_at', f"{published_before}T23:59:59Z")
            
        if only_market_sensitive and tier in ['pro', 'enterprise']:
            query = query.eq('is_volatile', True)
            count_query = count_query.eq('is_volatile', True)

        # Execute Count
        count_res = count_query.execute()
        found = count_res.count if count_res and hasattr(count_res, 'count') and count_res.count is not None else 0

        # Execute Query
        offset = (page - 1) * limit
        query = query.order('published_at', desc=True).range(offset, offset + limit - 1)
        response = query.execute()
        news_data = response.data if response and hasattr(response, 'data') and isinstance(response.data, list) else []

        if not news_data:
            return {
                "meta": {
                    "found": found,
                    "returned": 0,
                    "limit": limit,
                    "page": page,
                    "total_pages": (found + limit - 1) // limit if found > 0 else 1
                },
                "data": []
            }

        # Populate dynamic entities for all tiers
        stock_cache = {}
        if news_data:
            unique_symbols = list(set(n.get('yfin_symbol') for n in news_data if n.get('yfin_symbol')))
            if unique_symbols:
                # Selecting * to avoid 500 if specific columns like 'exchange' or 'country' are missing in production
                stocks_res = supabase.table('stocks').select('*').in_('yfin_symbol', unique_symbols).execute()
                if stocks_res and hasattr(stocks_res, 'data') and isinstance(stocks_res.data, list):
                    stock_cache = {s['yfin_symbol']: s for s in stocks_res.data if s.get('yfin_symbol')}

        formatted_news = []
        for n in news_data:
            content = n.get('content') or ''
            snippet = content[:200] + '...' if tier == 'free' and len(content) > 200 else content
            
            item = {
                "uuid": n.get('id'),
                "title": n.get('title'),
                "snippet": snippet,
                "url": n.get('url'),
                "source": n.get('source'),
                "published_at": n.get('published_at'),
                "sentiment": n.get('sentiment')
            }
            
            if tier in ['pro', 'enterprise']:
                item["sentiment_score"] = n.get('sentiment_score')
                item["confidence"] = n.get('confidence')
                item["is_market_sensitive"] = n.get('is_volatile')
                
            symbol = n.get('yfin_symbol')
            if symbol and symbol in stock_cache:
                stock_info = stock_cache[symbol]
                item["entities"] = [{
                    "symbol": stock_info.get('yfin_symbol'),
                    "name": stock_info.get('stock_name'),
                    "sector": stock_info.get('sector'),
                    "country": stock_info.get('country'),
                    "exchange": stock_info.get('exchange')
                }]
            else:
                item["entities"] = []
            
            formatted_news.append(item)

        total_pages = (found + limit - 1) // limit if found > 0 else 1

        return {
            "meta": {
                "found": found,
                "returned": len(formatted_news),
                "limit": limit,
                "page": page,
                "total_pages": total_pages
            },
            "data": formatted_news
        }
    except Exception as e:
        logger.error(f"Error in /v1/news: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# ---------------------------------------------------------
# 2. GET /api/v1/entities
# ---------------------------------------------------------
@v1_router.get(
    "/entities",
    response_model=V1EntityResponse,
    summary="List Supported Stocks & Entities",
    description="""
    Returns a directory of all NSE-listed stocks supported by the Sentimatix platform.
    AIs should use this to map company names to their correct ticker symbols or to discover stocks within a specific sector.
    """
)
async def get_entities(
    sector: Optional[str] = Query(None, description="Filter entities by industry sector", examples={"default": {"value": "Banking"}}),
    exchange: Optional[str] = Query("NSE", description="Filter by stock exchange. Currently only NSE is supported."),
    search: Optional[str] = Query(None, description="Fuzzy search by company name or ticker symbol", examples={"default": {"value": "Reliance"}}),
    user: dict = Depends(get_api_user),
    tier: str = Depends(get_user_tier)
):
    try:
        track_api_call(user.get('id', 'unknown'), '/api/v1/entities', tier, {"sector": sector, "exchange": exchange})
        query = supabase.table('stocks').select('*').eq('is_active', True)
        
        if sector:
            query = query.eq('sector', sector)
        if exchange:
            query = query.eq('exchange', exchange)
        if search:
            # Simple ilike search on name or yfin_symbol
            query = query.or_(f"stock_name.ilike.%{search}%,yfin_symbol.ilike.%{search}%")
            
        response = query.execute()
        stocks = response.data if response and hasattr(response, 'data') and isinstance(response.data, list) else []

        formatted_stocks = []
        for s in stocks:
            item = {
                "symbol": s.get('yfin_symbol'),
                "name": s.get('stock_name'),
                "sector": s.get('sector'),
                "exchange": s.get('exchange'),
                "country": s.get('country')
            }
            if tier in ['pro', 'enterprise']:
                item["sentiment_7d"] = s.get('sentiment_7d')
                item["sentiment_30d"] = s.get('sentiment_30d')
            formatted_stocks.append(item)

        return {"data": formatted_stocks}
    except Exception as e:
        logger.error(f"Error in /v1/entities: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# ---------------------------------------------------------
# 3. GET /api/v1/sentiment (Pro+)
# ---------------------------------------------------------
@v1_router.get(
    "/sentiment",
    response_model=V1SentimentResponse,
    summary="Get Aggregated Stock Sentiment",
    description="""
    Retrieves the aggregated sentiment scores for specific stocks over a 7-day or 30-day period.
    The 'sentiment_label' provides a quick 'Bullish' or 'Bearish' signal based on news volume and scoring.
    Requires Pro or Enterprise tier.
    """
)
async def get_sentiment(
    symbols: str = Query(..., description="Comma-separated NSE tickers", examples={"default": {"value": "RELIANCE,TCS,INFY"}}),
    period: str = Query("7d", description="Lookback window for aggregation: '7d' or '30d'", examples={"default": {"value": "7d"}}),
    user: dict = Depends(get_api_user),
    tier: str = Depends(get_user_tier)
):
    if tier == 'free':
        raise HTTPException(status_code=403, detail="Sentiment endpoint requires Pro or Enterprise tier.")
        
    try:
        track_api_call(user.get('id', 'unknown'), '/api/v1/sentiment', tier, {"symbols": symbols, "period": period})
        sym_list = [s.strip().upper() + '.NS' if not s.endswith('.NS') else s.strip().upper() for s in symbols.split(',')]
        response = supabase.table('stocks').select('*').in_('yfin_symbol', sym_list).execute()
        stocks = response.data if response and hasattr(response, 'data') else []

        formatted_sentiment = []
        for s in stocks:
            sent_7d = s.get('sentiment_7d')
            sent_30d = s.get('sentiment_30d')
            
            # Determine active sentiment based on period request, default to 7d
            active_sent = sent_30d if period == '30d' else sent_7d
            
            # Determine label
            label = "Neutral"
            if active_sent is not None:
                if active_sent > 20: label = "Bullish"
                elif active_sent > 5: label = "Slightly Bullish"
                elif active_sent < -20: label = "Bearish"
                elif active_sent < -5: label = "Slightly Bearish"

            formatted_sentiment.append({
                "symbol": s.get('yfin_symbol'),
                "name": s.get('stock_name'),
                "sector": s.get('sector'),
                "sentiment_7d": sent_7d,
                "sentiment_30d": sent_30d,
                "sentiment_label": label,
                "updated_at": s.get('sentiment_updated_at')
            })
            
        return {"data": formatted_sentiment}
    except Exception as e:
        logger.error(f"Error in /v1/sentiment: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# ---------------------------------------------------------
# 4. GET /api/v1/sentiment/sectors (Pro+)
# ---------------------------------------------------------
@v1_router.get(
    "/sentiment/sectors",
    response_model=V1SectorSentimentResponse,
    summary="Get Market Sector Sentiment",
    description="""
    Analyzes the 'mood' of entire market sectors (e.g., Banking, IT, Auto) by aggregating 
    sentiment across all stocks within those sectors. AIs should use this for top-down market analysis.
    """
)
async def get_sector_sentiment(
    sectors: Optional[str] = Query(None, description="Comma-separated sectors. If empty, returns top sectors.", examples={"default": {"value": "Banking,IT Services"}}),
    period: str = Query("7d", description="Lookback window for aggregation: '7d' or '30d'", examples={"default": {"value": "7d"}}),
    user: dict = Depends(get_api_user),
    tier: str = Depends(get_user_tier)
):
    try:
        track_api_call(user.get('id', 'unknown'), '/api/v1/sentiment/sectors', tier, {"sectors": sectors, "period": period})
        # Calculate start date based on period
        days = 30 if period == '30d' else 7
        start_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        query = supabase.table('news').select('yfin_symbol, sentiment, sentiment_score').gte('published_at', start_date)
        response = query.execute()
        news_data = response.data if response and hasattr(response, 'data') and isinstance(response.data, list) else []

        # Fetch sectors from stocks table
        stock_sectors = {}
        unique_symbols = list(set(n.get('yfin_symbol') for n in news_data if n.get('yfin_symbol')))
        if unique_symbols:
            stocks_res = supabase.table('stocks').select('yfin_symbol, sector').in_('yfin_symbol', unique_symbols).execute()
            if stocks_res and hasattr(stocks_res, 'data') and isinstance(stocks_res.data, list):
                stock_sectors = {s['yfin_symbol']: s.get('sector') for s in stocks_res.data if s.get('sector')}

        allowed_free_sectors = ['banking', 'it services', 'automobile', 'pharmaceuticals', 'fmcg']

        if tier == 'free':
            if sectors:
                sec_list = [s.strip().lower() for s in sectors.split(',') if s.strip().lower() in allowed_free_sectors]
            else:
                sec_list = allowed_free_sectors
        else:
            sec_list = [s.strip().lower() for s in sectors.split(',')] if sectors else None

        sector_stats = {}
        for item in news_data:
            symbol = item.get('yfin_symbol')
            sec = stock_sectors.get(symbol)
            if not sec: continue
            
            # Apply sector filter if specified (or restricted by free tier)
            if sec_list is not None and sec.lower() not in sec_list: continue
            
            if sec not in sector_stats:
                sector_stats[sec] = {
                    'total_score': 0, 'count': 0, 
                    'positive': 0, 'negative': 0, 'neutral': 0, 'conflicted': 0
                }
                
            sent_str = str(item.get('sentiment', '')).lower()
            if sent_str == 'positive': sector_stats[sec]['positive'] += 1
            elif sent_str == 'negative': sector_stats[sec]['negative'] += 1
            elif sent_str == 'conflicted': sector_stats[sec]['conflicted'] += 1
            else: sector_stats[sec]['neutral'] += 1
            
            score = item.get('sentiment_score')
            if score is not None:
                sector_stats[sec]['total_score'] += float(score)
                sector_stats[sec]['count'] += 1

        formatted_sectors = []
        for sec, stats in sector_stats.items():
            if stats['count'] == 0: continue
            avg_score = stats['total_score'] / stats['count']
            
            label = "Neutral"
            if avg_score > 0.2: label = "Bullish"
            elif avg_score < -0.2: label = "Bearish"
            
            formatted_sectors.append({
                "sector": sec,
                "avg_sentiment_score": round(avg_score, 4),
                "sentiment_label": label,
                "total_articles": stats['positive'] + stats['negative'] + stats['neutral'] + stats['conflicted']
            })

        return {
            "period": period,
            "data": formatted_sectors
        }
    except Exception as e:
        logger.error(f"Error in /v1/sentiment/sectors: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

