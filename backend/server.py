


# --- Google OAuth Setup ---
from authlib.integrations.starlette_client import OAuth
from starlette.config import Config
from starlette.requests import Request as StarletteRequest
from fastapi.responses import RedirectResponse
import secrets
import os
# Place Google OAuth endpoints after api_router is defined
from fastapi import FastAPI, APIRouter, HTTPException, Query, Response, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from supabase import create_client, Client
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

from models import (
    StockPrice, StockInfo, MarketIndex, StockSummary,
    TechnicalIndicators, ModelMetrics, Prediction,
    NewsItem, MarketOverview, SentimentTrend
)
import asyncio
import json
import logging
import uuid
import traceback
# Load environment variables from .env file
from dotenv import load_dotenv

# Import database functions
from database import (
    get_stock_prices,
    get_stock_sentiments,
    get_stock_predictions,
    get_latest_stock_prices,
    get_market_overview as get_market_data
)
load_dotenv()

# Google OAuth credentials from environment variables
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

# Supabase credentials from environment variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Starlette Config for Authlib
config = Config(environ={
    'GOOGLE_CLIENT_ID': GOOGLE_CLIENT_ID,
    'GOOGLE_CLIENT_SECRET': GOOGLE_CLIENT_SECRET,
    'SECRET_KEY': "1666",
})

oauth = OAuth(config)
oauth.register(
    name='google',
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)



# Create API router (must be defined before use)

api_router = APIRouter(prefix="/api")


# Create FastAPI app
app = FastAPI(
    title="Stock Analysis API",
    docs_url="/docs",
    openapi_url="/openapi.json"
)



# --- Auth Models ---
class SignupRequest(BaseModel):
    email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

class AuthResponse(BaseModel):
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    user: Optional[dict] = None
    error: Optional[str] = None
# Define API routes

# --- Signup Endpoint (POST /signin) ---



from fastapi import Response, Cookie

@api_router.post("/signup", response_model=AuthResponse, tags=["Auth"])
async def signup(signup_req: SignupRequest, response: Response):
    """User signup endpoint (creates a new user)"""
    try:
        admin = supabase.auth.admin
        user_exists = False
        users_page = admin.list_users()
        if hasattr(users_page, 'users'):
            user_list = users_page.users
        else:
            user_list = users_page.get('users', []) if isinstance(users_page, dict) else []
        for u in user_list:
            if u.get('email') == signup_req.email:
                user_exists = True
                break
        if user_exists:
            logger.info(f"Signup attempt for existing user: {signup_req.email}")
            return JSONResponse(status_code=400, content={"error": "Account already exists with this email."})

        result = supabase.auth.sign_up({"email": signup_req.email, "password": signup_req.password})
        logger.info(f"Supabase sign_up raw result: {result}")
        if hasattr(result, 'execute'):
            result = result.execute()
            logger.info(f"Supabase sign_up executed result: {result}")

        if result and isinstance(result, dict) and result.get("error"):
            error_message = result["error"].get("message", "Signup failed")
            logger.error(f"Supabase sign_up error: {result['error']}")
            return JSONResponse(status_code=400, content={"error": error_message,
                                                           "details": result["error"]})

        user = result.get("user") if isinstance(result, dict) else None
        session = result.get("session") if isinstance(result, dict) else None
        if session is None:
            logger.warning(f"Supabase sign_up session is None. Result: {result}")
            return JSONResponse(status_code=400, content={"error": "Email confirmation required.", "details": result})

        # Fetch authentication_key from users table
        access_token = None
        try:
            if user and user.get("email"):
                user_row = supabase.table('users').select('authentication_key').eq('email', user["email"]).single().execute()
                if user_row and hasattr(user_row, 'data') and user_row.data and 'authentication_key' in user_row.data:
                    access_token = user_row.data['authentication_key']
                elif user_row and isinstance(user_row, dict) and 'data' in user_row and user_row['data'] and 'authentication_key' in user_row['data']:
                    access_token = user_row['data']['authentication_key']
        except Exception as e:
            logger.error(f"Error fetching authentication_key from users table: {str(e)}")
            access_token = None
        if access_token:
            response.set_cookie(
                key="auth_key",
                value=access_token,
                httponly=True,
                secure=False,
                samesite="lax",
                max_age=60*60*24*7
            )
        return AuthResponse(
            access_token=session["access_token"] if session else None,
            refresh_token=session["refresh_token"] if session else None,
            user=user
        )
    except Exception as e:
        logger.error(f"Signup error: {str(e)}")
        raise HTTPException(status_code=400, detail="Signup failed")

# --- Login Endpoint (POST /login) ---

@api_router.post("/login", response_model=AuthResponse, tags=["Auth"])
async def login(login_req: LoginRequest, response: Response):
    """User login endpoint (returns session token)"""
    try:
        result = supabase.auth.sign_in_with_password({"email": login_req.email, "password": login_req.password})
        if result.get("error"):
            return AuthResponse(error=result["error"]["message"])
        user = result.get("user")
        session = result.get("session")

        # Fetch authentication_key from users table
        access_token = None
        try:
            if user and user.get("email"):
                user_row = supabase.table('users').select('authentication_key').eq('email', user["email"]).single().execute()
                if user_row and hasattr(user_row, 'data') and user_row.data and 'authentication_key' in user_row.data:
                    access_token = user_row.data['authentication_key']
                elif user_row and isinstance(user_row, dict) and 'data' in user_row and user_row['data'] and 'authentication_key' in user_row['data']:
                    access_token = user_row['data']['authentication_key']
        except Exception as e:
            logger.error(f"Error fetching authentication_key from users table: {str(e)}")
            access_token = None
        if access_token:
            response.set_cookie(
                key="auth_key",
                value=access_token,
                httponly=True,
                secure=False,
                samesite="lax",
                max_age=60*60*24*7
            )
        return AuthResponse(
            access_token=session["access_token"] if session else None,
            refresh_token=session["refresh_token"] if session else None,
            user=user
        )
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(status_code=401, detail="Login failed")
# --- Auth Check Endpoint ---
@api_router.get("/auth/check")
async def auth_check(auth_key: str = Cookie(None)):
    """Check if the user is authenticated by validating the auth_key cookie."""
    if not auth_key:
        return {"authenticated": False}
    # Check if auth_key exists in users table
    try:
        user_row = supabase.table('users').select('id').eq('authentication_key', auth_key).single().execute()
        if user_row and hasattr(user_row, 'data') and user_row.data and 'id' in user_row.data:
            return {"authenticated": True}
        elif user_row and isinstance(user_row, dict) and 'data' in user_row and user_row['data'] and 'id' in user_row['data']:
            return {"authenticated": True}
        else:
            return {"authenticated": False}
    except Exception as e:
        logger.error(f"Auth check error: {str(e)}")
        return {"authenticated": False}

# Root route for API health check
@app.get("/")
async def root():
    """API health check endpoint"""
    route_list = []
    for route in app.routes:
        if hasattr(route, "path") and hasattr(route, "methods"):
            # Exclude static files and internal routes
            if not route.path.startswith("/static") and not route.path.startswith("/openapi"):
                for method in route.methods:
                    if method in ("GET", "POST", "PUT", "DELETE", "PATCH"):
                        route_list.append(f"{method} {route.path}")
    return {
        "status": "ok",
        "message": "Stock Analysis API is running",
        "available_routes": sorted(route_list),
        "documentation": "/docs"
    }

# Add favicon handler to prevent 405 errors
@app.get("/favicon.ico")
async def favicon():
    """Return 204 No Content for favicon requests"""
    return Response(status_code=204)

# Add explicit OPTIONS handler for CORS preflight
@app.options("/{path:path}")
async def options_handler(path: str):
    """Handle CORS preflight requests"""
    return {"message": "OK"}

# Create Supabase client
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    # Test connection
    test_query = supabase.table('stock_prices').select('count').execute()
    logger.info(f"Successfully connected to Supabase. Data available: {test_query.data}")
except Exception as e:
    logger.error(f"Failed to initialize Supabase client: {str(e)}\nTraceback: {traceback.format_exc()}")
    raise




# Add CORS middleware FIRST
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:8080",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8080",
        "http://localhost:5173",  # Vite dev server
        "http://127.0.0.1:5173",  # Vite dev server
        "http://localhost:3001",  # Alternative React port
        "http://127.0.0.1:3001",  # Alternative React port
        "*"  # Allow all origins for development (remove in production)
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"],
    allow_headers=[
        "Accept",
        "Accept-Language",
        "Content-Language",
        "Content-Type",
        "Authorization",
        "X-Requested-With",
        "Origin",
        "Access-Control-Request-Method",
        "Access-Control-Request-Headers"
    ],
    expose_headers=["*"],
    max_age=86400,
)

# Add Session middleware (required for OAuth)
from starlette.middleware.sessions import SessionMiddleware
app.add_middleware(
    SessionMiddleware,
    secret_key='your-random-secret-key',
    same_site='lax',
    https_only=False,
)




# Root route for API health check
@app.get("/debug/tables")
async def list_tables():
    """Debug endpoint to list available tables and sample data"""
    try:
        tables = ['stock_prices', 'stock_predictions', 'stock_sentiments', 'news']
        result = {}
        
        for table in tables:
            try:
                # Get table info
                sample = supabase.table(table).select('*').limit(1).execute()
                count = supabase.table(table).select('count').execute()
                
                result[table] = {
                    'exists': True,
                    'sample': sample.data if sample.data else None,
                    'count': count.data[0]['count'] if count.data else 0,
                    'error': None
                }
            except Exception as table_error:
                result[table] = {
                    'exists': False,
                    'sample': None,
                    'count': 0,
                    'error': str(table_error)
                }
        
        return result
    except Exception as e:
        logger.error(f"Debug endpoint error: {str(e)}\nTraceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/debug/stock-price-mapping")
async def debug_stock_price_mapping():
    """Debug endpoint to understand stock symbol to stock_id mapping"""
    try:
        # Get a few samples from news table to see the structure
        news_sample = supabase.table('news').select('yfin_symbol, stock_name, sector').limit(5).execute()
        
        # Try to find if there's a way to map symbols to stock_ids
        # Check if there's a stocks table or any reference table
        try:
            stocks_sample = supabase.table('stocks').select('*').limit(3).execute()
            stocks_exists = True
            stocks_data = stocks_sample.data
        except:
            stocks_exists = False
            stocks_data = None
            
        # Get latest stock_prices sample
        prices_sample = supabase.table('stock_prices').select('*').order('date', desc=True).limit(3).execute()
        
        return {
            "news_sample": news_sample.data if news_sample.data else [],
            "stocks_table_exists": stocks_exists,
            "stocks_sample": stocks_data,
            "stock_prices_sample": prices_sample.data if prices_sample.data else [],
            "analysis": "Need to find mapping between yfin_symbol and stock_id"
        }
    except Exception as e:
        logger.error(f"Debug mapping error: {str(e)}")
        return {"error": str(e)}

# Define API routes
@api_router.get(
    "/market/overview",
    description="Get market overview including indices, top gainers, losers, and most active stocks",
    tags=["Market Data"]
)
async def get_market_overview(response: Response):
    # Add cache header for 5 minutes
    response.headers["Cache-Control"] = "public, max-age=300"
    logger.info("Attempting to fetch market overview")

    try:
        logger.info("Attempting to query stock_prices table")
        # Get latest stock data for market overview
        # Get latest date
        date_query = supabase.table('stock_prices').select('date').order('date', desc=True).limit(1).execute()
        logger.info(f"Date query response: {date_query}")
        
        if not date_query.data:
            logger.warning("No stock data found")
            # Return default values that match frontend expectations
            return {
                "indices": [{
                    "symbol": "NIFTY50",
                    "name": "Nifty 50",
                    "value": 19500.25,
                    "change": 0.0,
                    "change_percent": 0.0
                }, {
                    "symbol": "SENSEX",
                    "name": "BSE Sensex",
                    "value": 65420.75,
                    "change": 0.0,
                    "change_percent": 0.0
                }],
                "top_gainers": [],
                "top_losers": [],
                "most_active": [],
                "timestamp": datetime.now().isoformat()
            }

        latest_date = date_query.data[0]['date']
        
        # Get top stocks by volume
        stocks_data = supabase.table('stock_prices').select('*')\
            .eq('date', latest_date)\
            .order('volume', desc=True)\
            .limit(10)\
            .execute()
        
        stocks = stocks_data.data if stocks_data.data else []
        
        # Filter stocks with non-zero open prices
        valid_stocks = [stock for stock in stocks if float(stock["open"]) != 0]
        
        # Sort stocks by gain/loss percentage
        sorted_by_gain = sorted(
            valid_stocks,
            key=lambda stock: ((float(stock["close"]) - float(stock["open"])) / float(stock["open"])) * 100,
            reverse=True
        )
        
        # Format the response using actual stock data that matches frontend expectations
        overview = {
            "indices": [{
                "symbol": "NIFTY50",
                "name": "Nifty 50",
                "value": 19500.25,
                "change": 125.50,
                "change_percent": 0.65
            }, {
                "symbol": "SENSEX",
                "name": "BSE Sensex",
                "value": 65420.75,
                "change": 450.25,
                "change_percent": 0.69
            }],
            "top_gainers": [{
                "symbol": stock["symbol"].replace(".NS", ""),
                "name": stock["symbol"].replace(".NS", ""),
                "last_price": float(stock["close"]),
                "change": float(stock["close"]) - float(stock["open"]),
                "change_percent": ((float(stock["close"]) - float(stock["open"])) / float(stock["open"])) * 100,
                "volume": float(stock["volume"])
            } for stock in sorted_by_gain[:5]],
            "top_losers": [{
                "symbol": stock["symbol"].replace(".NS", ""),
                "name": stock["symbol"].replace(".NS", ""),
                "last_price": float(stock["close"]),
                "change": float(stock["close"]) - float(stock["open"]),
                "change_percent": ((float(stock["close"]) - float(stock["open"])) / float(stock["open"])) * 100
            } for stock in sorted_by_gain[-5:]],
            "most_active": [{
                "symbol": stock["symbol"].replace(".NS", ""),
                "name": stock["symbol"].replace(".NS", ""),
                "last_price": float(stock["close"]),
                "change": float(stock["close"]) - float(stock["open"]),
                "change_percent": ((float(stock["close"]) - float(stock["open"])) / float(stock["open"])) * 100,
                "volume": float(stock["volume"])
            } for stock in sorted(valid_stocks, key=lambda x: float(x["volume"]), reverse=True)[:5]],
            "timestamp": latest_date
        }
        
        logger.info(f"Successfully formatted market overview data with {len(stocks)} stocks")
        return overview
            
    except Exception as e:
        logger.error(f"Error in market overview: {str(e)}\nTraceback: {traceback.format_exc()}")
        return {
            "indices": [{
                "symbol": "NIFTY50",
                "name": "Nifty 50",
                "value": 19500.25,
                "change": 0.0,
                "change_percent": 0.0
            }, {
                "symbol": "SENSEX",
                "name": "BSE Sensex",
                "value": 65420.75,
                "change": 0.0,
                "change_percent": 0.0
            }],
            "top_gainers": [],
            "top_losers": [],
            "most_active": [],
            "timestamp": datetime.now().isoformat()
        }

@api_router.get("/stocks", response_model=List[StockSummary])
async def get_stocks(
    sentiment_days: int = Query(default=30, ge=1, le=365, description="Days back for sentiment calculation (default: 30 days)")
):
    try:
        logger.info(f"Fetching stocks using pre-calculated data (sentiment period: {sentiment_days} days)")
        
        # Determine which sentiment column to use based on requested days
        sentiment_column = 'sentiment_30d' if sentiment_days >= 15 else 'sentiment_7d'
        
        # Step 1: Get all stocks with their sentiment data
        stocks_query = supabase.table('stocks').select(f'''
            id, yfin_symbol, stock_name, sector, country, type,
            {sentiment_column}, sentiment_updated_at
        ''').eq('is_active', True).execute()
        
        if not stocks_query.data:
            logger.info("No active stocks found")
            return []
        
        # Step 2: Get latest date from stock_prices
        latest_date_query = supabase.table('stock_prices').select('date').order('date', desc=True).limit(1).execute()
        if not latest_date_query.data:
            logger.warning("No stock price data found")
            return []
        
        latest_date = latest_date_query.data[0]['date']
        logger.info(f"Using latest price data from: {latest_date}")
        
        # Step 3: Get latest price data for all stocks
        prices_query = supabase.table('stock_prices').select('''
            stock_id, close, open, volume, 
            change, change_percent,
            change_7d, change_percent_7d,
            change_15d, change_percent_15d,
            change_30d, change_percent_30d
        ''').eq('date', latest_date).execute()
        
        if not prices_query.data:
            logger.warning(f"No price data found for date: {latest_date}")
            return []
        
        # Create a mapping of stock_id to price data
        price_data_map = {item['stock_id']: item for item in prices_query.data}
        
        # Step 4: Combine stock info with price data
        stocks = []
        for stock in stocks_query.data:
            stock_id = stock['id']
            price_data = price_data_map.get(stock_id)
            
            if not price_data:
                continue  # Skip stocks without price data
            
            # Clean symbol (remove .NS suffix for display)
            yfin_symbol = stock.get('yfin_symbol', '')
            clean_symbol = yfin_symbol.replace('.NS', '') if yfin_symbol else ''
            
            if not clean_symbol:
                continue
            
            # Use pre-calculated values from database
            last_price = float(price_data.get('close', 0))
            volume = int(float(price_data.get('volume', 0)))
            
            # Select appropriate change values based on sentiment_days
            if sentiment_days <= 7:
                change = float(price_data.get('change_7d', 0))
                change_percent = float(price_data.get('change_percent_7d', 0))
            elif sentiment_days <= 15:
                change = float(price_data.get('change_15d', 0))
                change_percent = float(price_data.get('change_percent_15d', 0))
            elif sentiment_days <= 30:
                change = float(price_data.get('change_30d', 0))
                change_percent = float(price_data.get('change_percent_30d', 0))
            else:
                # Default to daily change for longer periods
                change = float(price_data.get('change', 0))
                change_percent = float(price_data.get('change_percent', 0))
            
            # Get pre-calculated sentiment
            sentiment_score = float(stock.get(sentiment_column, 0))
            
            stocks.append({
                "symbol": clean_symbol,
                "name": stock.get('stock_name') or clean_symbol,
                "last_price": last_price,
                "change": change,
                "change_percent": change_percent,
                "volume": volume,
                "sentiment_score": sentiment_score,
                "sector": stock.get('sector') or 'Unknown',
                "country": stock.get('country') or 'Unknown'
            })
        
        logger.info(f"Successfully fetched {len(stocks)} stocks using pre-calculated data")
        return stocks
        
    except Exception as e:
        logger.error(f"Error fetching stocks with pre-calculated data: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        # Fallback to simpler method if needed
        return await get_stocks_fallback(sentiment_days)

async def get_stocks_fallback(sentiment_days: int):
    """Fallback method with simpler queries (slower but more reliable)"""
    try:
        logger.info("Using fallback method for stocks endpoint")
        
        # Get stocks with basic info
        stocks_query = supabase.table('stocks').select('''
            id, yfin_symbol, stock_name, sector, country,
            sentiment_30d, sentiment_7d
        ''').eq('is_active', True).limit(50).execute()
        
        if not stocks_query.data:
            return []
        
        stocks = []
        for stock in stocks_query.data:
            try:
                stock_id = stock['id']
                yfin_symbol = stock.get('yfin_symbol', '')
                clean_symbol = yfin_symbol.replace('.NS', '') if yfin_symbol else ''
                
                if not clean_symbol:
                    continue
                
                # Get latest price data for this specific stock
                price_query = supabase.table('stock_prices').select('''
                    close, volume, change, change_percent
                ''').eq('stock_id', stock_id).order('date', desc=True).limit(1).execute()
                
                if price_query.data and len(price_query.data) > 0:
                    price_data = price_query.data[0]
                    last_price = float(price_data.get('close', 0))
                    volume = int(float(price_data.get('volume', 0)))
                    change = float(price_data.get('change', 0))
                    change_percent = float(price_data.get('change_percent', 0))
                else:
                    last_price = volume = change = change_percent = 0
                
                # Get appropriate sentiment
                sentiment_column = 'sentiment_30d' if sentiment_days >= 15 else 'sentiment_7d'
                sentiment_score = float(stock.get(sentiment_column, 0))
                
                stocks.append({
                    "symbol": clean_symbol,
                    "name": stock.get('stock_name') or clean_symbol,
                    "last_price": last_price,
                    "change": change,
                    "change_percent": change_percent,
                    "volume": volume,
                    "sentiment_score": sentiment_score,
                    "sector": stock.get('sector') or 'Unknown',
                    "country": stock.get('country') or 'Unknown'
                })
                
            except Exception as e:
                logger.warning(f"Error processing stock {stock.get('yfin_symbol', 'unknown')}: {str(e)}")
                continue
        
        logger.info(f"Fallback method returned {len(stocks)} stocks")
        return stocks
        
    except Exception as e:
        logger.error(f"Error in fallback method: {str(e)}")
        return []

# Route handlers continue

@api_router.get("/stocks/{stock_id}")
async def get_stock_detail(
    stock_id: str,
    history: Optional[int] = Query(None, ge=1, le=3650, description="Total number of days of historical data (e.g., 1, 5, 7, 30, 365)"),
    period: Optional[int] = Query(None, ge=1, le=365, description="Interval length in days for data aggregation (e.g., 1=daily, 7=weekly, 15=bi-weekly, 30=monthly)")
):
    """
    🎯 MAIN ENDPOINT for stock detail pages.
    
    Returns everything you need in ONE call:
    - Stock information (name, sector, sentiment)
    - Latest price with all metrics (7d, 15d, 30d changes)
    - Historical price data for charts (OHLCV) with optional aggregation
    
    Parameters:
    - history: Total number of days of historical data to fetch (default: 365)
      Examples: 1, 5, 7, 30, 90, 180, 365, 1825
    
    - period: Interval length in days for aggregating data points (default: 1 for daily)
      Examples: 
        * 1 = daily data points
        * 7 = weekly aggregation (one data point per week)
        * 15 = bi-weekly aggregation
        * 30 = monthly aggregation
    
    Examples:
    - GET /api/stocks/{stock_id}?history=365&period=1 (1 year daily data)
    - GET /api/stocks/{stock_id}?history=365&period=7 (1 year weekly aggregated)
    - GET /api/stocks/{stock_id}?history=30&period=1 (1 month daily data)
    - GET /api/stocks/{stock_id}?history=1825&period=30 (5 years monthly aggregated)
    """
    try:
        # Default values
        history_days = history if history is not None else 365  # Default to 1 year
        period_days = period if period is not None else 1  # Default to daily data
        
        logger.info(f"Fetching stock details for stock_id: {stock_id} with history: {history_days} days, period: {period_days} days")
        
        # 1. Get stock info from stocks table
        try:
            stock_query = supabase.table('stocks').select('*').eq('id', stock_id).single().execute()
            if not stock_query.data:
                logger.warning(f"Stock not found with id: {stock_id}")
                raise HTTPException(status_code=404, detail="Stock not found")
        except Exception as e:
            if "PGRST116" in str(e) or "0 rows" in str(e):
                logger.warning(f"Stock not found with id: {stock_id}")
                raise HTTPException(status_code=404, detail="Stock not found")
            raise
        
        stock_info = stock_query.data
        
        # 2. Get historical price data (last N days)
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=history_days)
        
        price_query = supabase.table('stock_prices').select('''
            date, open, high, low, close, volume,
            change, change_percent,
            change_7d, change_percent_7d,
            change_15d, change_percent_15d,
            change_30d, change_percent_30d
        ''').eq('stock_id', stock_id)\
          .gte('date', start_date.isoformat())\
          .lte('date', end_date.isoformat())\
          .order('date', desc=False)\
          .execute()
        
        price_history = price_query.data if price_query.data else []
        
        # 3. Apply period-based aggregation if period > 1
        if period_days > 1 and len(price_history) > 0:
            aggregated_history = []
            i = 0
            while i < len(price_history):
                # Take a chunk of 'period_days' worth of data
                chunk = price_history[i:min(i + period_days, len(price_history))]
                if len(chunk) > 0:
                    # Aggregate the chunk - handle None values
                    first_open = float(chunk[0].get('open') or 0)
                    last_close = float(chunk[-1].get('close') or 0)
                    
                    aggregated_point = {
                        "date": chunk[-1]['date'],  # Use the last date in the period
                        "open": first_open,  # First open
                        "high": max([float(p.get('high') or 0) for p in chunk]),  # Highest high
                        "low": min([float(p.get('low') or 0) for p in chunk if float(p.get('low') or 0) > 0]),  # Lowest low (exclude zeros)
                        "close": last_close,  # Last close
                        "volume": sum([int(float(p.get('volume') or 0)) for p in chunk]),  # Total volume
                        "change": last_close - first_open,  # Change over period
                        "change_percent": ((last_close - first_open) / first_open) * 100 if first_open != 0 else 0
                    }
                    aggregated_history.append(aggregated_point)
                i += period_days
            
            price_history = aggregated_history
        
        # 4. Get latest price for quick stats (always use the most recent data point)
        latest_price_raw = price_query.data[-1] if price_query.data else None
        
        # 5. Calculate overall period-specific metrics
        if len(price_history) > 0:
            first_price = price_history[0]
            last_price = price_history[-1]
            first_open = float(first_price.get('open') or 0)
            last_close = float(last_price.get('close') or 0)
            
            period_change = last_close - first_open
            period_change_percent = (period_change / first_open) * 100 if first_open != 0 else 0
            period_high = max([float(p.get('high') or 0) for p in price_history])
            period_low = min([float(p.get('low') or 0) for p in price_history if float(p.get('low') or 0) > 0])
            avg_volume = sum([int(p.get('volume') or 0) for p in price_history]) // len(price_history) if price_history else 0
        else:
            period_change = 0
            period_change_percent = 0
            period_high = 0
            period_low = 0
            avg_volume = 0
        
        # 6. Format historical data for charts
        formatted_history = []
        for price in price_history:
            formatted_history.append({
                "date": price.get('date'),
                "open": float(price.get('open') or 0),
                "high": float(price.get('high') or 0),
                "low": float(price.get('low') or 0),
                "close": float(price.get('close') or 0),
                "volume": int(price.get('volume') or 0),
                "change": float(price.get('change') or 0),
                "change_percent": float(price.get('change_percent') or 0)
            })
        
        # 7. Combine everything into comprehensive response
        result = {
            "stock_info": {
                "id": stock_info.get('id'),
                "symbol": stock_info.get('yfin_symbol', '').replace('.NS', ''),
                "yfin_symbol": stock_info.get('yfin_symbol'),
                "name": stock_info.get('stock_name'),
                "sector": stock_info.get('sector'),
                "country": stock_info.get('country'),
                "type": stock_info.get('type'),
                "is_active": stock_info.get('is_active'),
                "sentiment_7d": float(stock_info.get('sentiment_7d', 0)),
                "sentiment_30d": float(stock_info.get('sentiment_30d', 0)),
                "sentiment_updated_at": stock_info.get('sentiment_updated_at')
            },
            "latest_price": {
                "date": latest_price_raw.get('date') if latest_price_raw else None,
                "open": float(latest_price_raw.get('open') or 0) if latest_price_raw else 0,
                "high": float(latest_price_raw.get('high') or 0) if latest_price_raw else 0,
                "low": float(latest_price_raw.get('low') or 0) if latest_price_raw else 0,
                "close": float(latest_price_raw.get('close') or 0) if latest_price_raw else 0,
                "volume": int(float(latest_price_raw.get('volume') or 0)) if latest_price_raw else 0,
                "change": float(latest_price_raw.get('change') or 0) if latest_price_raw else 0,
                "change_percent": float(latest_price_raw.get('change_percent') or 0) if latest_price_raw else 0,
                "change_7d": float(latest_price_raw.get('change_7d') or 0) if latest_price_raw else 0,
                "change_percent_7d": float(latest_price_raw.get('change_percent_7d') or 0) if latest_price_raw else 0,
                "change_15d": float(latest_price_raw.get('change_15d') or 0) if latest_price_raw else 0,
                "change_percent_15d": float(latest_price_raw.get('change_percent_15d') or 0) if latest_price_raw else 0,
                "change_30d": float(latest_price_raw.get('change_30d') or 0) if latest_price_raw else 0,
                "change_percent_30d": float(latest_price_raw.get('change_percent_30d') or 0) if latest_price_raw else 0,
            } if latest_price_raw else None,
            "period_performance": {
                "history_days": history_days,
                "period_days": period_days,
                "change": period_change,
                "change_percent": period_change_percent,
                "high": period_high,
                "low": period_low,
                "avg_volume": avg_volume
            },
            "price_history": formatted_history,
            "meta": {
                "history_days": history_days,
                "period_days": period_days,
                "aggregation": "daily" if period_days == 1 else f"{period_days}-day",
                "data_points": len(formatted_history),
                "start_date": formatted_history[0]['date'] if formatted_history else None,
                "end_date": formatted_history[-1]['date'] if formatted_history else None
            }
        }
        
        logger.info(f"Successfully fetched stock details for {stock_id} with {len(formatted_history)} data points (history: {history_days}d, period: {period_days}d)")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching stock details for {stock_id}: {str(e)}\nTraceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error fetching stock details: {str(e)}")

# Optional: Lightweight endpoint if you only need basic info (without full price history)
@api_router.get("/stocks/{stock_id}/info")
async def get_stock_info_only(stock_id: str):
    """
    💡 LIGHTWEIGHT ENDPOINT - Only stock info + latest price (no history).
    Use this for quick lookups, stock cards, or when you don't need charts.
    
    Example: GET /api/stocks/{stock_id}/info
    """
    try:
        logger.info(f"Fetching stock info only for stock_id: {stock_id}")
        
        stock_query = supabase.table('stocks').select('*').eq('id', stock_id).single().execute()
        
        if not stock_query.data:
            logger.warning(f"Stock not found with id: {stock_id}")
            raise HTTPException(status_code=404, detail="Stock not found")
        
        stock_info = stock_query.data
        
        # Get just the latest price for current stats
        price_query = supabase.table('stock_prices').select('''
            date, close, change, change_percent, volume,
            change_7d, change_percent_7d,
            change_30d, change_percent_30d
        ''').eq('stock_id', stock_id).order('date', desc=True).limit(1).execute()
        
        latest_price = price_query.data[0] if price_query.data else None
        
        return {
            "id": stock_info.get('id'),
            "symbol": stock_info.get('yfin_symbol', '').replace('.NS', ''),
            "yfin_symbol": stock_info.get('yfin_symbol'),
            "name": stock_info.get('stock_name'),
            "sector": stock_info.get('sector'),
            "country": stock_info.get('country'),
            "type": stock_info.get('type'),
            "is_active": stock_info.get('is_active'),
            "sentiment_7d": float(stock_info.get('sentiment_7d', 0)),
            "sentiment_30d": float(stock_info.get('sentiment_30d', 0)),
            "current_price": float(latest_price.get('close', 0)) if latest_price else None,
            "change": float(latest_price.get('change', 0)) if latest_price else None,
            "change_percent": float(latest_price.get('change_percent', 0)) if latest_price else None,
            "volume": int(float(latest_price.get('volume', 0))) if latest_price else None,
            "last_updated": latest_price.get('date') if latest_price else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching stock info for {stock_id}: {str(e)}\nTraceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error fetching stock info: {str(e)}")

@api_router.get("/stocks/{symbol}/prices", response_model=List[StockPrice])
@api_router.get("/stocks/prices/{symbol}", response_model=List[StockPrice])  # Additional route for frontend compatibility
async def get_stock_prices_history(
    symbol: str,
    days: int = Query(30, description="Number of days of historical data")
):
    try:
        logger.info(f"Fetching price data for {symbol} for last {days} days")
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Add .NS suffix if not present
        clean_symbol = symbol if symbol.endswith('.NS') else f"{symbol}.NS"
        
        stock_data = await get_stock_prices(supabase, clean_symbol, start_date, end_date)
        if not stock_data:
            logger.info(f"No price data found for {symbol}")
            return []
            
        # Format the response to match frontend expectations
        formatted_data = []
        for price in stock_data:
            try:
                formatted_data.append({
                    "date": price.get("date", ""),
                    "open": float(price.get("open", 0)),
                    "high": float(price.get("high", 0)),
                    "low": float(price.get("low", 0)),
                    "close": float(price.get("close", 0)),
                    "volume": int(float(price.get("volume", 0))),
                    "change": float(price.get("close", 0)) - float(price.get("open", 0)),
                    "change_percent": ((float(price.get("close", 0)) - float(price.get("open", 0))) / float(price.get("open", 1))) * 100 if float(price.get("open", 0)) != 0 else 0
                })
            except (TypeError, ValueError, ZeroDivisionError) as e:
                logger.warning(f"Error processing price data for {symbol}: {str(e)}")
                continue
        
        logger.info(f"Found {len(formatted_data)} price records for {symbol}")
        return formatted_data
    except Exception as e:
        logger.error(f"Error fetching stock price for {symbol}: {str(e)}\nTraceback: {traceback.format_exc()}")
        return []  # Return empty list instead of error

from models import NewsListResponse

@api_router.get("/news", response_model=NewsListResponse)
async def get_news(
    stock_symbol: Optional[str] = Query(None, description="Filter by stock symbol"),
    sentiment: Optional[str] = Query(None, pattern="^(positive|negative|neutral)$"),
    page: int = Query(1, ge=1, description="Page number (starts from 1)"),
    limit: int = Query(10, ge=1, le=5000, description="Number of items per page (max 5000)"),
    start_date: Optional[str] = Query(None, description="Filter: published_at >= YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="Filter: published_at <= YYYY-MM-DD")
):
    try:
        logger.info(f"Fetching news for symbol: {stock_symbol}, sentiment: {sentiment}, page: {page}, limit: {limit}")
        query = supabase.table('news').select('*')
        if stock_symbol:
            # Remove .NS suffix if present and match against yfin_symbol
            clean_symbol = stock_symbol.replace(".NS", "")
            # Use IN filter for variants (.NS and bare) for supabase-py compatibility
            query = query.in_('yfin_symbol', [f"{clean_symbol}.NS", clean_symbol])
        if sentiment:
            query = query.eq('sentiment', sentiment)
        # Optional date filters
        if start_date:
            query = query.gte('published_at', f"{start_date}T00:00:00Z")
        if end_date:
            query = query.lte('published_at', f"{end_date}T23:59:59Z")
        
        # Validate pagination parameters
        if page < 1:
            page = 1
        if limit < 1:
            limit = 10
        elif limit > 5000:
            limit = 5000

        # Get total count for meta[found]
        count_query = supabase.table('news').select('id', count='exact')
        if stock_symbol:
            clean_symbol = stock_symbol.replace(".NS", "")
            count_query = count_query.in_('yfin_symbol', [f"{clean_symbol}.NS", clean_symbol])
        if sentiment:
            count_query = count_query.eq('sentiment', sentiment)
        if start_date:
            count_query = count_query.gte('published_at', f"{start_date}T00:00:00Z")
        if end_date:
            count_query = count_query.lte('published_at', f"{end_date}T23:59:59Z")
        count_response = count_query.execute()
        found = 0
        if hasattr(count_response, 'count') and count_response.count is not None:
            found = count_response.count
        elif isinstance(count_response, dict) and 'count' in count_response:
            found = count_response['count']

        # Fetch paginated news with consistent ordering
        response = query.order('published_at', desc=True).range((page-1)*limit, page*limit-1).execute()
        news_list = response.data if response and hasattr(response, 'data') and isinstance(response.data, list) else (response['data'] if response and isinstance(response, dict) and 'data' in response else [])
        logger.info(f"Found {len(news_list)} news items (page {page}, limit {limit}) out of {found}")

        def safe_news_item(item):
            return {
                "id": item.get("id", ""),
                "title": item.get("title", ""),
                "content": item.get("content") if item.get("content") is not None else "",
                "url": item.get("url") if item.get("url") is not None else "",
                "source": item.get("source", ""),
                "stock_symbol": item.get("stock_symbol") or item.get("yfin_symbol") or "",
                "published_at": item.get("published_at") or item.get("published_date") or datetime.now().isoformat(),
                "sentiment": item.get("sentiment") if item.get("sentiment") is not None else "neutral",
                "impact_score": float(item.get("sentiment_score", 0.0)) if item.get("sentiment_score") is not None else float(item.get("impact_score", 0.0)) if item.get("impact_score") is not None else 0.0,
                "country": item.get("country"),
                "sector": item.get("sector"),
                "type": item.get("type"),
                "stock_name": item.get("stock_name"),
            }
        safe_news = [safe_news_item(item) for item in news_list]
        
        # Calculate total pages for better frontend pagination
        total_pages = (found + limit - 1) // limit if found > 0 else 1
        
        meta = {
            "found": found,
            "returned": len(safe_news),
            "limit": limit,
            "page": page,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_previous": page > 1
        }
        return {"meta": meta, "data": safe_news}
    except Exception as e:
        logger.error(f"Error fetching news: {str(e)}\nTraceback: {traceback.format_exc()}")
        # Return error details for debugging
        return JSONResponse(status_code=500, content={"error": str(e), "trace": traceback.format_exc()})


@api_router.get("/developments")
async def get_stock_developments(
    stock_symbol: Optional[str] = Query(None, description="Filter by stock symbol"),
    days: int = Query(7, ge=1, le=30, description="Number of days to fetch (default 7)"),
    limit: int = Query(10, ge=1, le=100, description="Max developments to return")
):
    """
    Get recent developments for stocks
    Returns AI-identified key events and developments from news analysis
    """
    try:
        logger.info(f"Fetching developments for symbol: {stock_symbol}, days: {days}, limit: {limit}")
        
        # Calculate cutoff date
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        query = supabase.table('stock_developments').select('*')
        
        if stock_symbol:
            clean_symbol = stock_symbol.replace(".NS", "")
            query = query.eq('symbol', clean_symbol)
        
        query = query.gte('development_date', cutoff_date)
        query = query.order('development_date', desc=True)
        query = query.limit(limit)
        
        response = query.execute()
        developments = response.data if response and hasattr(response, 'data') else []
        
        logger.info(f"Found {len(developments)} developments")
        
        # Format response
        formatted_developments = []
        for dev in developments:
            formatted_developments.append({
                "id": dev.get("id"),
                "symbol": dev.get("symbol"),
                "title": dev.get("title"),
                "summary": dev.get("summary"),
                "category": dev.get("category"),
                "sentiment": dev.get("sentiment"),
                "impact_score": float(dev.get("impact_score", 0)),
                "development_date": dev.get("development_date"),
                "created_at": dev.get("created_at"),
                "source_article_count": len(dev.get("source_article_ids", []))
            })
        
        return {
            "meta": {
                "found": len(formatted_developments),
                "days": days,
                "symbol": stock_symbol
            },
            "data": formatted_developments
        }
        
    except Exception as e:
        logger.error(f"Error fetching developments: {str(e)}\nTraceback: {traceback.format_exc()}")
        return JSONResponse(status_code=500, content={"error": str(e), "trace": traceback.format_exc()})


# Mount all routes

app.include_router(api_router)

# --- Admin/Utility Endpoints ---

@api_router.get("/debug/stocks-data")
async def debug_stocks_data(
    sentiment_days: int = Query(default=30, ge=1, le=365, description="Days back for sentiment calculation")
):
    """Debug endpoint to see what data is being used for stocks"""
    try:
        # Get one stock as example
        stock_query = supabase.table('stocks').select('''
            id, yfin_symbol, stock_name, sentiment_30d, sentiment_7d, sentiment_updated_at
        ''').eq('is_active', True).limit(1).execute()
        
        if not stock_query.data:
            return {"error": "No stocks found"}
        
        stock = stock_query.data[0]
        stock_id = stock['id']
        
        # Get latest price data
        latest_date_query = supabase.table('stock_prices').select('date').order('date', desc=True).limit(1).execute()
        latest_date = latest_date_query.data[0]['date'] if latest_date_query.data else None
        
        price_query = supabase.table('stock_prices').select('''
            close, volume, change, change_percent,
            change_7d, change_percent_7d,
            change_15d, change_percent_15d,
            change_30d, change_percent_30d
        ''').eq('stock_id', stock_id).eq('date', latest_date).execute()
        
        price_data = price_query.data[0] if price_query.data else {}
        
        # Determine which values would be used
        sentiment_column = 'sentiment_30d' if sentiment_days >= 15 else 'sentiment_7d'
        
        if sentiment_days <= 7:
            change_used = "change_7d"
            change_value = price_data.get('change_7d')
            change_percent_value = price_data.get('change_percent_7d')
        elif sentiment_days <= 15:
            change_used = "change_15d"
            change_value = price_data.get('change_15d')
            change_percent_value = price_data.get('change_percent_15d')
        elif sentiment_days <= 30:
            change_used = "change_30d"
            change_value = price_data.get('change_30d')
            change_percent_value = price_data.get('change_percent_30d')
        else:
            change_used = "change (daily)"
            change_value = price_data.get('change')
            change_percent_value = price_data.get('change_percent')
        
        return {
            "stock_example": {
                "symbol": stock['yfin_symbol'],
                "name": stock['stock_name']
            },
            "latest_date": latest_date,
            "sentiment_period_requested": sentiment_days,
            "sentiment_column_used": sentiment_column,
            "sentiment_value": stock[sentiment_column],
            "change_period_used": change_used,
            "change_value": change_value,
            "change_percent_value": change_percent_value,
            "all_price_data": price_data,
            "all_sentiment_data": {
                "sentiment_7d": stock.get('sentiment_7d'),
                "sentiment_30d": stock.get('sentiment_30d'),
                "updated_at": stock.get('sentiment_updated_at')
            }
        }
        
    except Exception as e:
        return {"error": str(e)}


# --- Google OAuth Endpoints ---


# --- Google OAuth Login Endpoint ---
@app.get('/api/auth/google/login')
async def google_oauth_login(request: StarletteRequest):
    logger.info(f"OAuth login state before redirect (session): {request.session.get('google_oauth_state')}")
    redirect_uri = str(request.url_for('google_oauth_login_callback'))
    return await oauth.google.authorize_redirect(request, redirect_uri)

# --- Google OAuth Signup Endpoint ---
@app.get('/api/auth/google/signup')
async def google_oauth_signup(request: StarletteRequest):
    logger.info(f"OAuth signup state before redirect (session): {request.session.get('google_oauth_state')}")
    redirect_uri = str(request.url_for('google_oauth_signup_callback'))
    return await oauth.google.authorize_redirect(request, redirect_uri)





# --- Google OAuth Login Callback ---
@app.get('/api/auth/google/login/callback')
async def google_oauth_login_callback(request: StarletteRequest):
    try:
        logger.info(f"OAuth login callback state (session): {request.session.get('google_oauth_state')}")
        token = await oauth.google.authorize_access_token(request)
        logger.info(f"Google OAuth token response: {token}")
        user_info = None
        if token and 'userinfo' in token:
            user_info = token['userinfo']
        elif token and 'id_token' in token:
            user_info = await oauth.google.parse_id_token(request, token)
        if not user_info:
            resp = await oauth.google.get('userinfo', token=token)
            user_info = resp.json() if resp else None
        if not user_info:
            logger.error(f"Failed to fetch user info from Google. Token: {token}")
            return JSONResponse(status_code=400, content={"error": "Google authentication failed."})
        email = user_info.get('email')
        if not email:
            logger.error('No email found in Google user info')
            return JSONResponse(status_code=400, content={"error": "No email found in Google user info."})
        # Only allow login for existing users
        admin = supabase.auth.admin
        user_exists = False
        response = supabase.table('users')\
                .select('*')\
                .eq('email', email.strip().lower())\
                .execute()
        if len(response.data) > 0:
            user_exists = True
            logger.info(f"Found user in users table for email: {email}")
        
        if not user_exists:
            logger.info(f"OAuth login failed: user does not exist: {email}")
            return JSONResponse(status_code=400, content={"error": "No account found for this email. Please sign up first."})
        # Fetch authentication key from Supabase users table
        access_token = None
        try:
            user_row = supabase.table('users').select('authentication_key').eq('email', email).single().execute()
            if user_row and hasattr(user_row, 'data') and user_row.data and 'authentication_key' in user_row.data:
                access_token = user_row.data['authentication_key']
            elif user_row and isinstance(user_row, dict) and 'data' in user_row and user_row['data'] and 'authentication_key' in user_row['data']:
                access_token = user_row['data']['authentication_key']
        except Exception as e:
            logger.error(f"Error fetching authentication_key from users table: {str(e)}")
            access_token = None
        # Instead of redirect and cookie, return access_token in JSON
        if access_token:
            return {"access_token": access_token, "authenticated": True}
        else:
            return {"authenticated": False, "error": "No authentication key found."}
    except Exception as e:
        logger.error(f"Google OAuth login error: {str(e)}")
        return JSONResponse(status_code=400, content={"error": "Google authentication failed.", "details": str(e)})

# --- Google OAuth Signup Callback ---
@app.get('/api/auth/google/signup/callback')
async def google_oauth_signup_callback(request: StarletteRequest):
    try:
        logger.info(f"OAuth signup callback state (session): {request.session.get('google_oauth_state')}")
        token = await oauth.google.authorize_access_token(request)
        logger.info(f"Google OAuth token response: {token}")
        user_info = None
        if token and 'userinfo' in token:
            user_info = token['userinfo']
        elif token and 'id_token' in token:
            user_info = await oauth.google.parse_id_token(request, token)
        if not user_info:
            resp = await oauth.google.get('userinfo', token=token)
            user_info = resp.json() if resp else None
        if not user_info:
            logger.error(f"Failed to fetch user info from Google. Token: {token}")
            return JSONResponse(status_code=400, content={"error": "Google authentication failed."})
        email = user_info.get('email')
        if not email:
            logger.error('No email found in Google user info')
            return JSONResponse(status_code=400, content={"error": "No email found in Google user info."})
        # Only allow signup for new users
        admin = supabase.auth.admin
        user_exists = False
        response = supabase.table('users')\
                .select('*')\
                .eq('email', email.strip().lower())\
                .execute()
        if len(response.data) > 0:
            user_exists = True
            logger.info(f"Found user in users table for email: {email}")              
        if user_exists:
            logger.info(f"OAuth signup failed: user already exists: {email}")
            return JSONResponse(status_code=400, content={"error": "Account already exists with this email. Please log in instead."})
        # Create user in Supabase auth
        random_password = secrets.token_urlsafe(32)
        signup_result = supabase.auth.sign_up({"email": email, "password": random_password})
        if hasattr(signup_result, 'execute'):
            signup_result = signup_result.execute()
        error_msg = None
        if signup_result and isinstance(signup_result, dict):
            error = signup_result.get("error")
            user_obj = signup_result.get("user")
            if error:
                error_msg = error.get("message", str(error))
                logger.error(f"Supabase signup error: {error_msg}")
                return JSONResponse(status_code=400, content={"error": "Supabase signup failed.", "details": error_msg})
            elif user_obj:
                logger.info(f"Created new user in Supabase: {email}")
            else:
                logger.warning(f"Supabase signup returned no user and no error for: {email}")
        else:
            logger.warning(f"Unexpected signup_result format for: {email}")
        # Fetch authentication key from Supabase users table
        access_token = None
        try:
            user_row = supabase.table('users').select('authentication_key').eq('email', email).single().execute()
            if user_row and hasattr(user_row, 'data') and user_row.data and 'authentication_key' in user_row.data:
                access_token = user_row.data['authentication_key']
            elif user_row and isinstance(user_row, dict) and 'data' in user_row and user_row['data'] and 'authentication_key' in user_row['data']:
                access_token = user_row['data']['authentication_key']
        except Exception as e:
            logger.error(f"Error fetching authentication_key from users table: {str(e)}")
            access_token = None
        # Instead of redirect and cookie, return access_token in JSON
        if access_token:
            return {"access_token": access_token, "authenticated": True}
        else:
            return {"authenticated": False, "error": "No authentication key found."}
    except Exception as e:
        logger.error(f"Google OAuth signup error: {str(e)}")
        return JSONResponse(status_code=400, content={"error": "Google authentication failed.", "details": str(e)})

# Run the server when the file is executed directly
if __name__ == "__main__":
    import uvicorn
    import os
    # Get the current file's directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Change to the current directory
    os.chdir(current_dir)
    # Run uvicorn with the correct import string
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
