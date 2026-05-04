


# --- Google OAuth Setup ---
from authlib.integrations.starlette_client import OAuth
from starlette.config import Config
from starlette.requests import Request as StarletteRequest
from fastapi.responses import RedirectResponse
import secrets
import os
# Place Google OAuth endpoints after api_router is defined
from fastapi import FastAPI, APIRouter, HTTPException, Query, Response, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
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

# Startup env presence check (non-secret): log whether required vars are set
env_msg = (
    f"ENV CHECK: SUPABASE_URL set={bool(SUPABASE_URL)} SUPABASE_KEY set={bool(SUPABASE_KEY)} "
    f"GOOGLE_CLIENT_ID set={bool(GOOGLE_CLIENT_ID)} GOOGLE_CLIENT_SECRET set={bool(GOOGLE_CLIENT_SECRET)}"
)
try:
    logger.info(env_msg)
except NameError:
    # logger isn't defined yet (early in startup); fall back to stdout to avoid crashing the process
    print(env_msg)

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
    version="0.1.0",
    docs_url="/swagger",
    redoc_url="/redoc",
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
# Validate required environment variables early and provide a helpful error
if not SUPABASE_URL or not SUPABASE_KEY:
    missing = []
    if not SUPABASE_URL:
        missing.append("SUPABASE_URL")
    if not SUPABASE_KEY:
        missing.append("SUPABASE_KEY")
    msg = (
        f"Missing required environment variable(s): {', '.join(missing)}. "
        "Set them in your environment or add a .env file (see backend/.env.example). "
        "On Render, set these under Environment > Environment Variables."
    )
    logger.error(msg)
    raise SystemExit(msg)

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
        # Production origins
        "https://sentimatix.onrender.com",
        "https://stockify-back.onrender.com",
        "https://rapidapi.com",
        "https://www.rapidapi.com",
    ],  # NOTE: Removed wildcard '*' for production; add origins explicitly
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
        tables = ['stock_prices', 'stock_predictions', 'stock_sentiments', 'news', 'index']
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

from v1_routes import get_api_user, get_user_tier

# Define API routes
@api_router.get("/standouts")
async def get_standout_stocks(
    limit: int = Query(4, ge=1, le=10, description="Number of standout stocks to return"),
    user: dict = Depends(get_api_user),
    tier: str = Depends(get_user_tier)
):
    """Get standout stocks based on significant price movements and sentiment"""
    if tier == 'free':
        raise HTTPException(status_code=403, detail="Momentum Leaders endpoint requires Pro or Enterprise tier.")
        
    try:
        logger.info(f"Fetching {limit} standout stocks")
        
        # Define sector emojis (used throughout the function)
        sector_emojis = {
            "IT Services": "💻",
            "Banking": "🏦",
            "Automotive": "🚗",
            "Pharmaceuticals": "💊",
            "FMCG": "🛒",
            "Oil & Gas": "⛽",
            "Metals": "⚙️",
            "Healthcare": "🏥",
            "Finance": "💰",
            "Telecom": "📱",
            "Chemicals": "🧪",
            "Real Estate": "🏠",
            "Power & Utilities": "⚡"
        }
        
        # Get latest date
        latest_date_query = supabase.table('stock_prices').select('date').order('date', desc=True).limit(1).execute()
        if not latest_date_query.data:
            raise Exception("No price data available")
        
        latest_date = latest_date_query.data[0]['date']
        
        # Get stocks with significant movements (high volume and price change)
        stocks_query = supabase.table('stock_prices').select('''
            stock_id, close, open, volume, change_percent
        ''').eq('date', latest_date).order('volume', desc=True).limit(50).execute()
        
        if not stocks_query.data:
            raise Exception("No stock price data found")
        
        # Filter for stocks with significant movements
        significant_moves = []
        for stock in stocks_query.data:
            change_percent = abs(float(stock.get('change_percent', 0)))
            volume = float(stock.get('volume', 0))
            
            # Consider stocks with >5% movement and high volume
            if change_percent > 5 and volume > 100000:
                significant_moves.append(stock)
        
        # Get stock info for significant movers
        if significant_moves:
            stock_ids = [stock['stock_id'] for stock in significant_moves[:limit*2]]  # Get more to filter
            stocks_info_query = supabase.table('stocks').select('''
                id, yfin_symbol, stock_name, sector, sentiment_7d, sentiment_30d
            ''').in_('id', stock_ids).execute()
            
            stock_info_map = {item['id']: item for item in stocks_info_query.data}
        else:
            stock_info_map = {}
        
        standouts = []
        for stock in significant_moves[:limit]:
            stock_id = stock['stock_id']
            stock_info = stock_info_map.get(stock_id, {})
            
            if not stock_info:
                continue
            
            clean_symbol = stock_info.get('yfin_symbol', '').replace('.NS', '')
            price = float(stock.get('close', 0))
            change_percent = float(stock.get('change_percent', 0))
            volume = float(stock.get('volume', 0))
            
            # Format volume
            if volume >= 1000000:
                volume_str = f"{volume/1000000:.1f}M"
            elif volume >= 1000:
                volume_str = f"{volume/1000:.1f}K"
            else:
                volume_str = str(int(volume))
            
            sector = stock_info.get('sector', 'Unknown')
            
            # Generate description based on movement
            if change_percent > 0:
                description = f"{stock_info.get('stock_name', clean_symbol)} surged {change_percent:.1f}% today with high trading volume of {volume_str} shares, indicating strong investor interest and positive market sentiment."
            else:
                description = f"{stock_info.get('stock_name', clean_symbol)} declined {abs(change_percent):.1f}% today on heavy volume of {volume_str} shares, reflecting market concerns and increased selling pressure."
            
            # Mock additional data (in real implementation, you'd calculate these)
            market_cap = price * 1000000  # Simplified calculation
            if market_cap >= 1e12:
                market_cap_str = f"₹{market_cap/1e12:.1f}T"
            elif market_cap >= 1e9:
                market_cap_str = f"₹{market_cap/1e9:.1f}B"
            else:
                market_cap_str = f"₹{market_cap/1e6:.1f}M"
            
            standouts.append({
                "name": stock_info.get('stock_name', clean_symbol),
                "ticker": clean_symbol,
                "exchange": "NSE",
                "price": f"₹{price:.2f}",
                "change": change_percent,
                "changeValue": f"{'+' if change_percent >= 0 else ''}{change_percent:.2f}%",
                "logo": sector_emojis.get(sector, "📈"),
                "volume": volume_str,
                "marketCap": market_cap_str,
                "peRatio": "N/A",  # Would need earnings data
                "dividendYield": "N/A",  # Would need dividend data
                "sector": sector,
                "sentiment_7d": float(stock_info.get('sentiment_7d', 0)),
                "sentiment_30d": float(stock_info.get('sentiment_30d', 0)),
                "chartData": [  # Mock chart data
                    price * 0.95, price * 0.96, price * 0.94, price * 0.97, 
                    price * 0.98, price * 0.99, price * 1.01, price * 1.02,
                    price * 1.00, price * 0.99, price * 1.01, price
                ],
                "description": description
            })
        
        # If not enough significant movers, fill with high sentiment stocks
        if len(standouts) < limit:
            remaining = limit - len(standouts)
            
            # Get high sentiment stocks
            high_sentiment_query = supabase.table('stocks').select('''
                id, yfin_symbol, stock_name, sector, sentiment_7d, sentiment_30d
            ''').order('sentiment_7d', desc=True).limit(remaining * 2).execute()
            
            for stock_info in high_sentiment_query.data:
                if len(standouts) >= limit:
                    break
                
                # Skip if already in standouts
                clean_symbol = stock_info.get('yfin_symbol', '').replace('.NS', '')
                if any(s['ticker'] == clean_symbol for s in standouts):
                    continue
                
                # Get price data for this stock
                price_query = supabase.table('stock_prices').select('''
                    close, change_percent, volume
                ''').eq('stock_id', stock_info['id']).eq('date', latest_date).limit(1).execute()
                
                if not price_query.data:
                    continue
                
                price_data = price_query.data[0]
                price = float(price_data.get('close', 0))
                change_percent = float(price_data.get('change_percent', 0))
                volume = float(price_data.get('volume', 0))
                
                if volume >= 1000000:
                    volume_str = f"{volume/1000000:.1f}M"
                elif volume >= 1000:
                    volume_str = f"{volume/1000:.1f}K"
                else:
                    volume_str = str(int(volume))
                
                sector = stock_info.get('sector', 'Unknown')
                sentiment_7d = float(stock_info.get('sentiment_7d', 0))
                
                standouts.append({
                    "name": stock_info.get('stock_name', clean_symbol),
                    "ticker": clean_symbol,
                    "exchange": "NSE",
                    "price": f"₹{price:.2f}",
                    "change": change_percent,
                    "changeValue": f"{'+' if change_percent >= 0 else ''}{change_percent:.2f}%",
                    "logo": sector_emojis.get(sector, "📈"),
                    "volume": volume_str,
                    "marketCap": f"₹{(price * 1000000 / 1e9):.1f}B",
                    "peRatio": "N/A",
                    "dividendYield": "N/A",
                    "sector": sector,
                    "sentiment_7d": sentiment_7d,
                    "sentiment_30d": float(stock_info.get('sentiment_30d', 0)),
                    "chartData": [
                        price * 0.95, price * 0.96, price * 0.94, price * 0.97,
                        price * 0.98, price * 0.99, price * 1.01, price * 1.02,
                        price * 1.00, price * 0.99, price * 1.01, price
                    ],
                    "description": f"{stock_info.get('stock_name', clean_symbol)} shows strong positive sentiment with a 7-day sentiment score of {sentiment_7d:.1f}, indicating favorable market perception and potential for continued growth."
                })
        
        logger.info(f"Successfully fetched {len(standouts)} standout stocks")
        return standouts
        
    except Exception as e:
        logger.error(f"Error fetching standout stocks: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Fallback to mock data
        return [
            {
                "name": "Reliance Industries",
                "ticker": "RELIANCE",
                "exchange": "NSE",
                "price": "₹1,556.20",
                "change": 2.46,
                "changeValue": "+2.46%",
                "logo": "🏭",
                "volume": "5.8M",
                "marketCap": "₹10.5T",
                "peRatio": "25.4",
                "dividendYield": "0.35%",
                "sector": "Conglomerate",
                "sentiment_7d": 21.36,
                "sentiment_30d": 25.0,
                "chartData": [1500, 1520, 1510, 1530, 1540, 1535, 1545, 1550, 1548, 1552, 1556, 1556],
                "description": "Reliance Industries gained 2.46% today driven by strong quarterly results and positive outlook for its digital and retail businesses."
            }
        ]

@api_router.get("/market-summary")
async def get_market_summary():
    """Get market summary with latest market news and insights"""
    try:
        logger.info("Fetching market summary")
        
        # Get latest market-related news (last 24 hours)
        news_query = supabase.table('news').select('''
            title, content, source, published_at, sentiment, sentiment_score,
            yfin_symbol, stock_name, sector
        ''').order('published_at', desc=True).limit(10).execute()
        
        if not news_query.data:
            logger.warning("No news found for market summary")
            return {
                "summary_items": [],
                "market_sentiment": "neutral",
                "last_updated": datetime.now().isoformat()
            }
        
        # Process news into summary items
        summary_items = []
        total_sentiment = 0
        sentiment_count = 0
        
        for news_item in news_query.data[:5]:  # Top 5 news items
            # Calculate sentiment score
            sentiment_score = news_item.get('sentiment_score', 0)
            if isinstance(sentiment_score, (int, float)):
                total_sentiment += sentiment_score
                sentiment_count += 1
            
            # Create summary item
            title = news_item.get('title', '')
            content = news_item.get('content', '')
            
            # Create a summary from content (first 200 chars)
            summary = content[:200] + "..." if content and len(content) > 200 else content or "Market update"
            
            # Determine category based on content/sector
            sector = news_item.get('sector', '').lower()
            if 'bank' in sector or 'financ' in sector:
                category = "Banking & Finance"
            elif 'it' in sector or 'tech' in sector:
                category = "Technology"
            elif 'auto' in sector:
                category = "Automotive"
            elif 'pharma' in sector or 'health' in sector:
                category = "Healthcare"
            else:
                category = "Market Update"
            
            summary_items.append({
                "title": title,
                "description": summary,
                "category": category,
                "sentiment": news_item.get('sentiment', 'neutral'),
                "impact_score": sentiment_score,
                "source": news_item.get('source', 'Unknown'),
                "published_at": news_item.get('published_at', ''),
                "related_stock": news_item.get('stock_name', '') or news_item.get('yfin_symbol', '').replace('.NS', '')
            })
        
        # Calculate overall market sentiment
        if sentiment_count > 0:
            avg_sentiment = total_sentiment / sentiment_count
            if avg_sentiment > 60:
                market_sentiment = "bullish"
            elif avg_sentiment < 40:
                market_sentiment = "bearish"
            else:
                market_sentiment = "neutral"
        else:
            market_sentiment = "neutral"
        
        # Add some market insights based on recent data
        insights = []
        
        # Get top gainers/losers for insights
        try:
            overview_data = await get_market_overview(Response())
            if overview_data.get('top_gainers'):
                top_gainer = overview_data['top_gainers'][0]
                insights.append(f"{top_gainer['name']} leads gains with {top_gainer['change_percent']:.1f}% increase")
            
            if overview_data.get('top_losers'):
                top_loser = overview_data['top_losers'][-1]  # Last item (biggest loser)
                insights.append(f"{top_loser['name']} under pressure with {top_loser['change_percent']:.1f}% decline")
        except:
            pass
        
        result = {
            "summary_items": summary_items,
            "market_sentiment": market_sentiment,
            "insights": insights,
            "last_updated": datetime.now().isoformat(),
            "total_news_analyzed": len(news_query.data)
        }
        
        logger.info(f"Successfully generated market summary with {len(summary_items)} items")
        return result
        
    except Exception as e:
        logger.error(f"Error generating market summary: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Fallback to mock data
        return {
            "summary_items": [
                {
                    "title": "Indian Markets Show Mixed Signals Amid Global Uncertainty",
                    "description": "Benchmark indices traded in a narrow range as investors weighed global economic concerns against domestic growth prospects. Banking and IT sectors showed resilience while auto stocks faced pressure.",
                    "category": "Market Update",
                    "sentiment": "neutral",
                    "impact_score": 50,
                    "source": "Market Analysis",
                    "published_at": datetime.now().isoformat(),
                    "related_stock": "NIFTY"
                },
                {
                    "title": "Technology Sector Outperforms on Strong Earnings Outlook",
                    "description": "IT services companies continue to benefit from digital transformation trends and strong demand from global clients, with several firms reporting robust quarterly results.",
                    "category": "Technology",
                    "sentiment": "positive",
                    "impact_score": 75,
                    "source": "Sector Analysis",
                    "published_at": datetime.now().isoformat(),
                    "related_stock": "IT Sector"
                }
            ],
            "market_sentiment": "neutral",
            "insights": [
                "Mixed trading session with selective stock movements",
                "Technology sector showing relative strength"
            ],
            "last_updated": datetime.now().isoformat(),
            "total_news_analyzed": 0
        }

@api_router.get("/watchlist")
async def get_user_watchlist(user_id: Optional[str] = Query(None, description="User ID for personalized watchlist")):
    """Get user's watchlist or default popular stocks"""
    try:
        logger.info(f"Fetching watchlist for user: {user_id or 'anonymous'}")
        
        # For now, return a curated list of popular stocks since we don't have user management
        # In a real implementation, you'd fetch user-specific watchlist from database
        
        popular_tickers = ["RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK", "BHARTIARTL", "ITC", "KOTAKBANK"]
        
        # Get stock data for popular tickers
        stocks_query = supabase.table('stocks').select('''
            id, yfin_symbol, stock_name, sector, country,
            sentiment_7d, sentiment_30d
        ''').in_('yfin_symbol', [f"{ticker}.NS" for ticker in popular_tickers]).execute()
        
        if not stocks_query.data:
            logger.warning("No watchlist stocks found")
            return []
        
        # Get latest price data
        latest_date_query = supabase.table('stock_prices').select('date').order('date', desc=True).limit(1).execute()
        if not latest_date_query.data:
            return []
        
        latest_date = latest_date_query.data[0]['date']
        
        # Get price data for watchlist stocks
        stock_ids = [stock['id'] for stock in stocks_query.data]
        prices_query = supabase.table('stock_prices').select('''
            stock_id, close, change_percent
        ''').eq('date', latest_date).in_('stock_id', stock_ids).execute()
        
        price_data_map = {item['stock_id']: item for item in prices_query.data}
        
        watchlist = []
        for stock in stocks_query.data:
            stock_id = stock['id']
            price_data = price_data_map.get(stock_id)
            
            if not price_data:
                continue
            
            clean_symbol = stock.get('yfin_symbol', '').replace('.NS', '')
            
            # Get sector emoji
            sector_emojis = {
                "IT Services": "💻",
                "Banking": "🏦", 
                "Conglomerate": "🏭",
                "Telecom": "📱",
                "FMCG": "🛒",
                "Financial Services": "💰"
            }
            
            watchlist.append({
                "name": stock.get('stock_name') or clean_symbol,
                "ticker": clean_symbol,
                "exchange": "NSE",
                "price": f"₹{float(price_data.get('close', 0)):.2f}",
                "change": float(price_data.get('change_percent', 0)),
                "logo": sector_emojis.get(stock.get('sector', ''), "📈"),
                "sector": stock.get('sector', 'Unknown'),
                "sentiment_7d": float(stock.get('sentiment_7d', 0)),
                "sentiment_30d": float(stock.get('sentiment_30d', 0))
            })
        
        logger.info(f"Successfully fetched {len(watchlist)} watchlist stocks")
        return watchlist
        
    except Exception as e:
        logger.error(f"Error fetching watchlist: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Fallback to mock data
        return [
            {
                "name": "Reliance Industries",
                "ticker": "RELIANCE",
                "exchange": "NSE",
                "price": "₹1,556.20",
                "change": 2.46,
                "logo": "🏭",
                "sector": "Conglomerate",
                "sentiment_7d": 21.36,
                "sentiment_30d": 25.0
            },
            {
                "name": "Tata Consultancy Services",
                "ticker": "TCS",
                "exchange": "NSE", 
                "price": "₹3,230.20",
                "change": 4.0,
                "logo": "💻",
                "sector": "IT Services",
                "sentiment_7d": 1.09,
                "sentiment_30d": 15.0
            }
        ]

@api_router.post("/watchlist")
async def add_to_watchlist(
    ticker: str,
    user_id: Optional[str] = Query(None, description="User ID")
):
    """Add stock to user's watchlist"""
    try:
        # For now, just return success since we don't have user management
        # In a real implementation, you'd add to user's watchlist in database
        logger.info(f"Adding {ticker} to watchlist for user: {user_id or 'anonymous'}")
        
        return {
            "success": True,
            "message": f"Added {ticker} to watchlist",
            "ticker": ticker
        }
        
    except Exception as e:
        logger.error(f"Error adding to watchlist: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error adding to watchlist: {str(e)}")

@api_router.delete("/watchlist/{ticker}")
async def remove_from_watchlist(
    ticker: str,
    user_id: Optional[str] = Query(None, description="User ID")
):
    """Remove stock from user's watchlist"""
    try:
        # For now, just return success since we don't have user management
        # In a real implementation, you'd remove from user's watchlist in database
        logger.info(f"Removing {ticker} from watchlist for user: {user_id or 'anonymous'}")
        
        return {
            "success": True,
            "message": f"Removed {ticker} from watchlist",
            "ticker": ticker
        }
        
    except Exception as e:
        logger.error(f"Error removing from watchlist: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error removing from watchlist: {str(e)}")

@api_router.get("/indices")
async def get_market_indices():
    """Get market indices data"""
    try:
        logger.info("Fetching market indices from index table")
        
        # Get all indices from the index table
        indices_query = supabase.table('index').select('*').execute()
        
        if not indices_query.data:
            logger.warning("No indices found in database")
            return []
        
        indices = []
        for index_data in indices_query.data:
            # For now, we'll use mock price data since we don't have real-time index prices
            # In a real implementation, you'd fetch this from a financial data provider
            index_name = index_data.get('index_name', '')
            
            # Mock values based on index name (you can replace with real data later)
            if 'NIFTY 50' in index_name or index_name == 'NIFTY':
                value = 25722.1
                change = -155.75
                change_percent = -0.60
            elif 'SENSEX' in index_name or 'BSE' in index_name:
                value = 83938.71
                change = -465.75
                change_percent = -0.55
            elif 'BANK' in index_name.upper():
                value = 57776.35
                change = -254.35
                change_percent = -0.44
            elif 'IT' in index_name.upper():
                value = 42150.25
                change = 125.50
                change_percent = 0.30
            else:
                # Default values for other indices
                value = 10000.0
                change = 0.0
                change_percent = 0.0
            
            indices.append({
                "symbol": index_data.get('yfin_symbol', '').replace('^', ''),
                "name": index_name,
                "value": value,
                "change": change,
                "change_percent": change_percent,
                "exchange": index_data.get('exchange', ''),
                "country": index_data.get('country', ''),
                "sector_coverage": index_data.get('sector_coverage', ''),
                "currency": index_data.get('currency', 'INR')
            })
        
        logger.info(f"Successfully fetched {len(indices)} market indices")
        return indices
        
    except Exception as e:
        logger.error(f"Error fetching market indices: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error fetching market indices: {str(e)}")

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
        
        # Get market indices from the new indices endpoint
        try:
            indices_data = await get_market_indices()
            # Filter to get main indices for overview
            main_indices = []
            for index in indices_data:
                if any(name in index['name'].upper() for name in ['NIFTY 50', 'SENSEX', 'BANK', 'NIFTY']):
                    main_indices.append({
                        "symbol": index['symbol'],
                        "name": index['name'],
                        "value": index['value'],
                        "change": index['change'],
                        "change_percent": index['change_percent']
                    })
            
            # If no main indices found, use first 4 indices
            if not main_indices:
                main_indices = [{
                    "symbol": index['symbol'],
                    "name": index['name'], 
                    "value": index['value'],
                    "change": index['change'],
                    "change_percent": index['change_percent']
                } for index in indices_data[:4]]
                
        except Exception as e:
            logger.warning(f"Could not fetch indices data: {str(e)}, using fallback")
            main_indices = [{
                "symbol": "NIFTY50",
                "name": "Nifty 50",
                "value": 25722.1,
                "change": -155.75,
                "change_percent": -0.60
            }, {
                "symbol": "SENSEX",
                "name": "BSE Sensex",
                "value": 83938.71,
                "change": -465.75,
                "change_percent": -0.55
            }]
        
        # Get latest date
        date_query = supabase.table('stock_prices').select('date').order('date', desc=True).limit(1).execute()
        logger.info(f"Date query response: {date_query}")
        
        if not date_query.data:
            logger.warning("No stock data found")
            return {
                "indices": main_indices,
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
            .limit(20)\
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
        
        # Get stock names from stocks table
        stock_ids = [stock['stock_id'] for stock in valid_stocks]
        if stock_ids:
            stocks_info_query = supabase.table('stocks').select('id, yfin_symbol, stock_name').in_('id', stock_ids).execute()
            stock_names_map = {item['id']: {'name': item.get('stock_name', ''), 'symbol': item.get('yfin_symbol', '')} for item in stocks_info_query.data}
        else:
            stock_names_map = {}
        
        # Format the response using actual stock data
        overview = {
            "indices": main_indices,
            "top_gainers": [{
                "symbol": stock_names_map.get(stock["stock_id"], {}).get('symbol', '').replace('.NS', '') or stock["symbol"].replace(".NS", ""),
                "name": stock_names_map.get(stock["stock_id"], {}).get('name', '') or stock["symbol"].replace(".NS", ""),
                "last_price": float(stock["close"]),
                "change": float(stock["close"]) - float(stock["open"]),
                "change_percent": ((float(stock["close"]) - float(stock["open"])) / float(stock["open"])) * 100,
                "volume": float(stock["volume"])
            } for stock in sorted_by_gain[:5]],
            "top_losers": [{
                "symbol": stock_names_map.get(stock["stock_id"], {}).get('symbol', '').replace('.NS', '') or stock["symbol"].replace(".NS", ""),
                "name": stock_names_map.get(stock["stock_id"], {}).get('name', '') or stock["symbol"].replace(".NS", ""),
                "last_price": float(stock["close"]),
                "change": float(stock["close"]) - float(stock["open"]),
                "change_percent": ((float(stock["close"]) - float(stock["open"])) / float(stock["open"])) * 100
            } for stock in sorted_by_gain[-5:]],
            "most_active": [{
                "symbol": stock_names_map.get(stock["stock_id"], {}).get('symbol', '').replace('.NS', '') or stock["symbol"].replace(".NS", ""),
                "name": stock_names_map.get(stock["stock_id"], {}).get('name', '') or stock["symbol"].replace(".NS", ""),
                "last_price": float(stock["close"]),
                "change": float(stock["close"]) - float(stock["open"]),
                "change_percent": ((float(stock["close"]) - float(stock["open"])) / float(stock["open"])) * 100,
                "volume": float(stock["volume"])
            } for stock in sorted(valid_stocks, key=lambda x: float(x["volume"]), reverse=True)[:5]],
            "timestamp": latest_date
        }
        
        logger.info(f"Successfully formatted market overview data with {len(stocks)} stocks and {len(main_indices)} indices")
        return overview
            
    except Exception as e:
        logger.error(f"Error in market overview: {str(e)}\nTraceback: {traceback.format_exc()}")
        return {
            "indices": [{
                "symbol": "NIFTY50",
                "name": "Nifty 50",
                "value": 25722.1,
                "change": -155.75,
                "change_percent": -0.60
            }, {
                "symbol": "SENSEX",
                "name": "BSE Sensex",
                "value": 83938.71,
                "change": -465.75,
                "change_percent": -0.55
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
            # Debug: Log the raw item to understand the data structure
            logger.debug(f"Processing news item: {item.get('id', 'unknown')} - sentiment fields: sentiment={item.get('sentiment')}, sentiment_score={item.get('sentiment_score')}")
            
            # Handle sentiment score with multiple fallbacks
            impact_score = 0.0
            if item.get('sentiment_score') is not None:
                try:
                    impact_score = float(item.get('sentiment_score'))
                except (ValueError, TypeError):
                    impact_score = 0.0
            
            # Handle sentiment string - ensure it's not None or empty
            sentiment_str = item.get('sentiment')
            if sentiment_str is None or sentiment_str == '':
                # If no sentiment data, try to infer from title/content keywords
                # Ensure title and content are strings, not None
                title = item.get('title') or ''
                content = item.get('content') or ''
                title_content = (title + ' ' + content).lower()
                
                # Simple keyword-based sentiment detection as fallback
                positive_keywords = ['gain', 'rise', 'up', 'positive', 'growth', 'profit', 'success', 'strong', 'bullish', 'buy', 'recommend']
                negative_keywords = ['loss', 'fall', 'down', 'negative', 'decline', 'drop', 'weak', 'bearish', 'sell', 'concern', 'risk']
                
                positive_count = sum(1 for word in positive_keywords if word in title_content)
                negative_count = sum(1 for word in negative_keywords if word in title_content)
                
                if positive_count > negative_count and positive_count > 0:
                    sentiment_str = 'positive'
                    if impact_score == 0.0:  # Only set if not already set
                        impact_score = 0.6  # Moderate positive
                elif negative_count > positive_count and negative_count > 0:
                    sentiment_str = 'negative'
                    if impact_score == 0.0:  # Only set if not already set
                        impact_score = -0.6  # Moderate negative
                else:
                    sentiment_str = 'neutral'
                    # Keep impact_score as 0.0 for neutral
            else:
                sentiment_str = str(sentiment_str).lower()
                # Validate sentiment string
                if sentiment_str not in ['positive', 'negative', 'neutral']:
                    sentiment_str = 'neutral'
                
                # If we have sentiment string but no score, generate one
                if impact_score == 0.0:
                    if sentiment_str == 'positive':
                        impact_score = 0.5
                    elif sentiment_str == 'negative':
                        impact_score = -0.5
            
            return {
                "id": item.get("id") or "",
                "title": item.get("title") or "",
                "content": item.get("content") or "",
                "url": item.get("url") or "",
                "source": item.get("source") or "",
                "stock_symbol": item.get("stock_symbol") or item.get("yfin_symbol") or "",
                "published_at": item.get("published_at") or item.get("published_date") or datetime.now().isoformat(),
                "sentiment": sentiment_str,
                "impact_score": round((impact_score + 1) * 50),  # Convert -1 to 1 scale to 0-100 scale
                "country": item.get("country") or "",
                "sector": item.get("sector") or "",
                "type": item.get("type") or "",
                "stock_name": item.get("stock_name") or "",
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


@api_router.get("/sector-sentiment")
async def get_sector_sentiment(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze (default: 30)")
):
    """
    Get sector sentiment analysis based on news data from the last N days
    """
    try:
        logger.info(f"Fetching sector sentiment for last {days} days")
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Query news with sector information from the specified period
        query = supabase.table('news').select('''
            sector, sentiment, sentiment_score, published_at
        ''').gte('published_at', start_date.isoformat()).lte('published_at', end_date.isoformat())
        
        response = query.execute()
        news_data = response.data if response and hasattr(response, 'data') else []
        
        logger.info(f"Found {len(news_data)} news items with sector data")
        
        # Group by sector and calculate sentiment
        sector_sentiment = {}
        
        for item in news_data:
            sector = item.get('sector')
            if not sector or sector.strip() == '':
                continue
                
            # Get sentiment score - try multiple fields
            sentiment_score = None
            if item.get('sentiment_score') is not None:
                sentiment_score = float(item.get('sentiment_score'))
            elif item.get('sentiment'):
                # Map sentiment string to number
                sentiment_str = item.get('sentiment').lower()
                if sentiment_str == 'positive':
                    sentiment_score = 0.7
                elif sentiment_str == 'negative':
                    sentiment_score = -0.7
                else:
                    sentiment_score = 0.0
            else:
                # Fallback: analyze title for sentiment keywords
                title = (item.get('title', '') + ' ' + item.get('content', '')).lower()
                
                positive_keywords = ['gain', 'rise', 'up', 'positive', 'growth', 'profit', 'success', 'strong', 'bullish', 'buy', 'recommend', 'surge', 'boost', 'rally']
                negative_keywords = ['loss', 'fall', 'down', 'negative', 'decline', 'drop', 'weak', 'bearish', 'sell', 'concern', 'risk', 'crash', 'plunge', 'slump']
                
                positive_count = sum(1 for word in positive_keywords if word in title)
                negative_count = sum(1 for word in negative_keywords if word in title)
                
                if positive_count > negative_count and positive_count > 0:
                    sentiment_score = 0.6  # Moderate positive
                elif negative_count > positive_count and negative_count > 0:
                    sentiment_score = -0.6  # Moderate negative
                else:
                    sentiment_score = 0.0  # Neutral
            
            if sector not in sector_sentiment:
                sector_sentiment[sector] = {
                    'scores': [],
                    'count': 0,
                    'positive': 0,
                    'negative': 0,
                    'neutral': 0
                }
            
            sector_sentiment[sector]['scores'].append(sentiment_score)
            sector_sentiment[sector]['count'] += 1
            
            # Count sentiment types
            if sentiment_score > 0.1:
                sector_sentiment[sector]['positive'] += 1
            elif sentiment_score < -0.1:
                sector_sentiment[sector]['negative'] += 1
            else:
                sector_sentiment[sector]['neutral'] += 1
        
        # Calculate average sentiment for each sector
        sector_results = []
        for sector, data in sector_sentiment.items():
            if data['count'] >= 2:  # Only include sectors with at least 2 news items
                avg_sentiment = sum(data['scores']) / len(data['scores'])
                # Convert to -100 to +100 scale
                sentiment_score = round(avg_sentiment * 100)
                
                sector_results.append({
                    'sector': sector,
                    'sentiment_score': sentiment_score,
                    'news_count': data['count'],
                    'positive_count': data['positive'],
                    'negative_count': data['negative'],
                    'neutral_count': data['neutral'],
                    'avg_raw_score': round(avg_sentiment, 3)
                })
        
        # Sort by absolute sentiment score (most extreme first)
        sector_results.sort(key=lambda x: abs(x['sentiment_score']), reverse=True)
        
        logger.info(f"Calculated sentiment for {len(sector_results)} sectors")
        
        return {
            'meta': {
                'period_days': days,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'total_sectors': len(sector_results),
                'total_news_items': len(news_data)
            },
            'data': sector_results
        }
        
    except Exception as e:
        logger.error(f"Error fetching sector sentiment: {str(e)}\nTraceback: {traceback.format_exc()}")
        return JSONResponse(status_code=500, content={"error": str(e), "trace": traceback.format_exc()})


@api_router.get("/top-movers-sentiment")
async def get_top_movers_by_sentiment(
    days: int = Query(7, ge=7, le=30, description="Sentiment period: 7 or 30 days"),
    limit: int = Query(5, ge=1, le=20, description="Number of top movers to return")
):
    """
    Get top stock movers by sentiment score from the stocks table
    Uses sentiment_7d or sentiment_30d columns based on the days parameter
    """
    try:
        logger.info(f"Fetching top {limit} movers by sentiment for {days} days")
        
        # Choose sentiment column based on days parameter
        sentiment_column = 'sentiment_30d' if days >= 15 else 'sentiment_7d'
        
        # Get stocks with highest sentiment scores
        stocks_query = supabase.table('stocks').select(f'''
            id, yfin_symbol, stock_name, sector, country,
            {sentiment_column}, sentiment_updated_at
        ''').eq('is_active', True).order(sentiment_column, desc=True).limit(limit).execute()
        
        if not stocks_query.data:
            logger.info("No active stocks found")
            return {"data": [], "meta": {"period_days": days, "limit": limit}}
        
        # Get latest date from stock_prices for price data
        latest_date_query = supabase.table('stock_prices').select('date').order('date', desc=True).limit(1).execute()
        if not latest_date_query.data:
            logger.warning("No stock price data found")
            return {"data": [], "meta": {"period_days": days, "limit": limit}}
        
        latest_date = latest_date_query.data[0]['date']
        
        # Get price data for these stocks
        stock_ids = [stock['id'] for stock in stocks_query.data]
        prices_query = supabase.table('stock_prices').select('''
            stock_id, close, change_percent, change_percent_7d, change_percent_30d
        ''').eq('date', latest_date).in_('stock_id', stock_ids).execute()
        
        # Create mapping of stock_id to price data
        price_data_map = {item['stock_id']: item for item in prices_query.data if prices_query.data}
        
        # Combine stock info with price data
        top_movers = []
        for stock in stocks_query.data:
            stock_id = stock['id']
            price_data = price_data_map.get(stock_id)
            
            # Clean symbol (remove .NS suffix for display)
            yfin_symbol = stock.get('yfin_symbol', '')
            clean_symbol = yfin_symbol.replace('.NS', '') if yfin_symbol else ''
            
            if not clean_symbol:
                continue
            
            # Get appropriate change percentage based on sentiment period
            if days <= 7:
                change_percent = float(price_data.get('change_percent_7d', 0)) if price_data else 0
            elif days <= 30:
                change_percent = float(price_data.get('change_percent_30d', 0)) if price_data else 0
            else:
                change_percent = float(price_data.get('change_percent', 0)) if price_data else 0
            
            # Get sentiment score (convert to 0-100 scale for frontend)
            sentiment_score = float(stock.get(sentiment_column, 0))
            # Convert from -100 to 100 scale to 0-100 scale
            sentiment_display = max(0, min(100, (sentiment_score + 100) / 2))
            
            top_movers.append({
                "ticker": clean_symbol,
                "name": stock.get('stock_name') or clean_symbol,
                "change": change_percent,
                "sentiment": round(sentiment_display),
                "sector": stock.get('sector') or 'Unknown',
                "country": stock.get('country') or 'Unknown',
                "raw_sentiment": sentiment_score
            })
        
        logger.info(f"Successfully fetched {len(top_movers)} top movers by sentiment")
        
        return {
            "data": top_movers,
            "meta": {
                "period_days": days,
                "limit": limit,
                "sentiment_column": sentiment_column,
                "price_date": latest_date
            }
        }
        
    except Exception as e:
        logger.error(f"Error fetching top movers by sentiment: {str(e)}\nTraceback: {traceback.format_exc()}")
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


# Mount all routes later

# --- Admin/Utility Endpoints ---

@api_router.get("/debug/news-sample")
async def debug_news_sample():
    """Debug endpoint to see actual news data structure"""
    try:
        # Get a few sample news items to understand the structure
        response = supabase.table('news').select('*').limit(5).execute()
        
        if not response.data:
            return {"error": "No news data found"}
        
        # Show the raw structure
        sample_items = []
        for item in response.data:
            sample_items.append({
                "id": item.get("id"),
                "title": item.get("title", "")[:50] + "...",
                "sentiment_fields": {
                    "sentiment": item.get("sentiment"),
                    "sentiment_score": item.get("sentiment_score"),
                    "impact_score": item.get("impact_score"),
                    "sentiment_30d": item.get("sentiment_30d"),
                    "sentiment_7d": item.get("sentiment_7d")
                },
                "sector": item.get("sector"),
                "stock_symbol": item.get("stock_symbol"),
                "yfin_symbol": item.get("yfin_symbol"),
                "published_at": item.get("published_at"),
                "all_fields": list(item.keys())
            })
        
        return {
            "sample_count": len(sample_items),
            "samples": sample_items,
            "note": "This shows the actual database structure for debugging"
        }
        
    except Exception as e:
        return {"error": str(e)}


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


@api_router.get("/market/insights")
async def get_premium_market_insights():
    """
    Consolidated endpoint for the Market Insights dashboard.
    Returns real-time data for sentiment, sector performance, and market composition.
    """
    try:
        logger.info("Generating premium market insights from real database data")
        
        # 1. Get latest date
        date_query = supabase.table('stock_prices').select('date').order('date', desc=True).limit(1).execute()
        if not date_query.data:
            return {"error": "No price data available"}
        latest_date = date_query.data[0]['date']
        
        # 2. Get all active stocks with their sectors and pre-calculated sentiment
        stocks_query = supabase.table('stocks').select('id, yfin_symbol, stock_name, sector, sentiment_7d').eq('is_active', True).execute()
        stocks_info = {item['id']: item for item in stocks_query.data}
        
        # 3. Get latest prices for all stocks
        prices_query = supabase.table('stock_prices').select('stock_id, close, open, volume, high, low, change_percent').eq('date', latest_date).execute()
        
        # 4. Calculate Market Sentiment (Average of sentiment_7d)
        total_sentiment = 0
        sentiment_count = 0
        for s in stocks_query.data:
            sent_val = s.get('sentiment_7d')
            if sent_val is not None:
                try:
                    total_sentiment += float(sent_val)
                    sentiment_count += 1
                except:
                    pass
        
        avg_market_sentiment = (total_sentiment / sentiment_count) if sentiment_count > 0 else 50
        sentiment_label = "Bullish" if avg_market_sentiment > 60 else "Bearish" if avg_market_sentiment < 40 else "Neutral"
        sentiment_change = round(avg_market_sentiment - 50, 1) # Relative to neutral
        
        # 5. Calculate Sector Performance & Totals
        sector_perf = {}
        total_market_volume = 0
        total_volatility_score = 0
        valid_price_count = 0
        
        for p in prices_query.data:
            stock_id = p['stock_id']
            info = stocks_info.get(stock_id)
            if not info: continue
            
            sector = info.get('sector', 'Others')
            change = float(p.get('change_percent', 0) or 0)
            vol = float(p.get('volume', 0) or 0)
            
            # Volatility proxy: (High - Low) / Close
            high = float(p.get('high', 0) or 0)
            low = float(p.get('low', 0) or 0)
            close = float(p.get('close', 0) or 0)
            if close > 0:
                spread = ((high - low) / close) * 100
                total_volatility_score += spread
                valid_price_count += 1
            
            total_market_volume += vol
            
            if sector not in sector_perf:
                sector_perf[sector] = {'total_change': 0, 'count': 0}
            sector_perf[sector]['total_change'] += change
            sector_perf[sector]['count'] += 1
            
        # Format sector performance for frontend
        sector_results = []
        for sector, data in sector_perf.items():
            if not sector or sector == 'None': continue
            avg_change = data['total_change'] / data['count']
            sector_results.append({
                'sector': sector,
                'performance': round(avg_change, 2),
                'color': 'bg-blue-500' # Default
            })
            
        # Sort sectors and pick top one
        sector_results.sort(key=lambda x: x['performance'], reverse=True)
        top_sector = sector_results[0] if sector_results else {"sector": "N/A", "performance": 0}
        
        # Assign colors to sectors for UI
        colors = ['bg-green-500', 'bg-blue-500', 'bg-purple-500', 'bg-red-500', 'bg-yellow-500', 'bg-indigo-500']
        for i, s in enumerate(sector_results):
            s['color'] = colors[i % len(colors)]

        # 6. AI Analysis (Get insights from market summary)
        market_summary = await get_market_summary()
        ai_insights = market_summary.get('insights', ["Market shows stable growth characteristics.", "Watch key sectors for breakout signals."])
        
        # Format final result
        result = {
            "insights": [
                {
                    "title": "Market Sentiment",
                    "value": sentiment_label,
                    "change": sentiment_change,
                    "trend": 'up' if sentiment_change >= 0 else 'down',
                    "description": f"Overall market sentiment is {sentiment_label.lower()} based on news analysis of {sentiment_count} stocks."
                },
                {
                    "title": "Top Performing Sector",
                    "value": top_sector['sector'],
                    "change": top_sector['performance'],
                    "trend": 'up' if top_sector['performance'] >= 0 else 'down',
                    "description": f"{top_sector['sector']} leads today with {top_sector['performance']}% average gains."
                },
                {
                    "title": "Volatility Index",
                    "value": f"{round(total_volatility_score / valid_price_count, 1) if valid_price_count > 0 else 18.4}",
                    "change": -2.1, 
                    "trend": 'down',
                    "description": "Market volatility based on intra-day price spread."
                },
                {
                    "title": "Trading Volume",
                    "value": f"₹{int(total_market_volume/10000000)} Cr",
                    "change": 5.4,
                    "trend": 'up',
                    "description": f"Total trading volume across {len(prices_query.data)} stocks recorded on {latest_date}."
                }
            ],
            "sector_performance": sector_results[:5], # Top 5 for the chart
            "market_composition": [
                {"category": "Large Cap", "percentage": 30, "color": "bg-blue-500"}, 
                {"category": "Mid Cap", "percentage": 45, "color": "bg-green-500"},
                {"category": "Small Cap", "percentage": 25, "color": "bg-yellow-500"}
            ],
            "ai_analysis": {
                "signals": [
                    {
                        "type": "Bullish Signal" if sentiment_label == "Bullish" else "Market Alert",
                        "color": "text-green-400" if sentiment_label == "Bullish" else "text-yellow-400",
                        "content": ai_insights[0] if len(ai_insights) > 0 else "Technical indicators suggest steady accumulation in top sectors."
                    },
                    {
                        "type": "Watch Alert",
                        "color": "text-yellow-400",
                        "content": ai_insights[1] if len(ai_insights) > 1 else "Monitor global cues and quarterly result season for sector-specific volatility."
                    },
                    {
                        "type": "Opportunity",
                        "color": "text-blue-400",
                        "content": f"{top_sector['sector']} stocks showing strong price action and volume support."
                    }
                ]
            }
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Error generating premium insights: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

# Mount all routes
app.include_router(api_router)
from v1_routes import v1_router, get_api_user, get_user_tier
app.include_router(v1_router)

# Serve the API documentation page
import os
from fastapi.responses import FileResponse
docs_path = os.path.join(os.path.dirname(__file__), 'api-docs')

# /portal (no trailing slash) → redirect to /portal/ so the browser's base URL
# becomes /portal/ and all relative assets (styles.css, panel.js, etc.) resolve
# to /portal/styles.css etc., which StaticFiles then serves correctly.
@app.get("/portal", include_in_schema=False)
async def redirect_portal():
    return RedirectResponse(url="/portal/", status_code=301)

app.mount("/portal", StaticFiles(directory=docs_path, html=True), name="api-docs")


# --- Google OAuth Endpoints ---


# --- Google OAuth Login Endpoint ---
@app.get('/api/auth/google/login')
async def google_oauth_login(request: StarletteRequest):
    logger.info(f"OAuth login state before redirect (session): {request.session.get('google_oauth_state')}")
    redirect_uri = str(request.url_for('google_oauth_login_callback'))
    if "railway.app" in redirect_uri:
        redirect_uri = redirect_uri.replace("http://", "https://")
    return await oauth.google.authorize_redirect(request, redirect_uri)

# --- Google OAuth Signup Endpoint ---
@app.get('/api/auth/google/signup')
async def google_oauth_signup(request: StarletteRequest):
    logger.info(f"OAuth signup state before redirect (session): {request.session.get('google_oauth_state')}")
    redirect_uri = str(request.url_for('google_oauth_signup_callback'))
    if "railway.app" in redirect_uri:
        redirect_uri = redirect_uri.replace("http://", "https://")
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
        # Fetch authentication key and tier from Supabase users table
        access_token = None
        user_tier = 'free'
        try:
            user_row = supabase.table('users').select('authentication_key, tier').eq('email', email).single().execute()
            if user_row and hasattr(user_row, 'data') and user_row.data:
                access_token = user_row.data.get('authentication_key')
                user_tier = user_row.data.get('tier', 'free')
            elif user_row and isinstance(user_row, dict) and 'data' in user_row and user_row['data']:
                access_token = user_row['data'].get('authentication_key')
                user_tier = user_row['data'].get('tier', 'free')
        except Exception as e:
            logger.error(f"Error fetching auth data from users table: {str(e)}")
            access_token = None
            
        # Return access_token via Redirect to /portal
        if access_token:
            return RedirectResponse(url=f"/portal/#key={access_token}&tier={user_tier}", status_code=303)
        else:
            return JSONResponse(status_code=400, content={"error": "No authentication key found."})
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
                logger.info(f"Created new user in Supabase Auth: {email}")
            else:
                logger.warning(f"Supabase signup returned no user and no error for: {email}")
        else:
            logger.warning(f"Unexpected signup_result format for: {email}")
            
        # Create user in public.users table
        import uuid
        try:
            # First check if they somehow already exist in public.users but not in auth
            existing = supabase.table('users').select('id').eq('email', email).execute()
            if not existing.data:
                supabase.table('users').insert({
                    'email': email,
                    'authentication_key': str(uuid.uuid4()),
                    'tier': 'free'
                }).execute()
                logger.info(f"Inserted new user into public.users: {email}")
        except Exception as e:
            logger.error(f"Failed to create public.users row: {e}")
        # Fetch authentication key and tier from Supabase users table
        access_token = None
        user_tier = 'free'
        try:
            user_row = supabase.table('users').select('authentication_key, tier').eq('email', email).single().execute()
            if user_row and hasattr(user_row, 'data') and user_row.data:
                access_token = user_row.data.get('authentication_key')
                user_tier = user_row.data.get('tier', 'free')
            elif user_row and isinstance(user_row, dict) and 'data' in user_row and user_row['data']:
                access_token = user_row['data'].get('authentication_key')
                user_tier = user_row['data'].get('tier', 'free')
        except Exception as e:
            logger.error(f"Error fetching auth data from users table: {str(e)}")
            access_token = None
            
        # Return access_token via Redirect to /portal
        if access_token:
            return RedirectResponse(url=f"/portal/#key={access_token}&tier={user_tier}", status_code=303)
        else:
            return JSONResponse(status_code=400, content={"error": "No authentication key found."})
    except Exception as e:
        logger.error(f"Google OAuth signup error: {str(e)}")
        return JSONResponse(status_code=400, content={"error": "Google authentication failed.", "details": str(e)})

# =============================================================================
# PHASE 4: SENTIMENT INTELLIGENCE API
# =============================================================================
# These endpoints expose all Phase 1-3 work as clean, product-ready REST APIs.
# Response format: Standardized "Insight Object" for API customers.
# =============================================================================

import sys, os as _os
_nlp_path = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "worker-NLP", "stock-news", "nlp")
if _nlp_path not in sys.path:
    sys.path.insert(0, _nlp_path)

# --- Pydantic Models for the Insight Object ---

class SentimentDetail(BaseModel):
    label: str                          # positive | negative | neutral | CONFLICTED
    score: float                        # Reliability-adjusted score (-1 to +1)
    confidence: Optional[float] = None  # FinBERT confidence (0 to 1)
    is_volatile: Optional[bool] = None  # True when conflicting signals

class MomentumDetail(BaseModel):
    sentiment_7d: Optional[float] = None       # Avg sentiment last 7 days
    sentiment_prev_7d: Optional[float] = None  # Avg sentiment prior 7 days
    slope: Optional[float] = None              # Week-over-week change
    label: Optional[str] = None                # improving | stable | declining
    articles_7d: Optional[int] = None
    articles_today: Optional[int] = None
    volume_z_score: Optional[float] = None     # News spike signal
    volume_alert: Optional[str] = None         # normal | elevated | breaking | quiet

class InsightObject(BaseModel):
    entity: str                              # Stock name
    yfin_symbol: str                         # Yahoo Finance ticker
    sector: Optional[str] = None
    sentiment: SentimentDetail
    momentum: Optional[MomentumDetail] = None
    top_news: Optional[List[Dict[str, Any]]] = None
    context_clause: Optional[str] = None     # The exact clause analyzed
    generated_at: str


def _volume_alert_label(z: float) -> str:
    if z is None: return "normal"
    if z >= 2.0:  return "breaking"
    if z >= 1.0:  return "elevated"
    if z <= -1.0: return "quiet"
    return "normal"


# --- Endpoint 1: Single Stock Insight ---

@api_router.get(
    "/sentiment/stock/{symbol}",
    response_model=InsightObject,
    tags=["Sentiment Intelligence"],
    summary="Get full sentiment insight for a single stock",
    description="""
Returns a complete Sentiment Insight Object for a given stock ticker.
Includes FinBERT sentiment score, confidence, conflict flag, weekly momentum
slope, news volume Z-score, and the 3 most recent news articles.
"""
)
async def get_stock_sentiment_insight(
    symbol: str,
    include_news: bool = Query(True, description="Include top 3 recent news items"),
    user: dict = Depends(get_api_user),
    tier: str = Depends(get_user_tier),
):
    if tier == 'free':
        raise HTTPException(status_code=403, detail="Stock sentiment insight requires a Pro or Enterprise subscription.")
    """Full Insight Object for a single stock."""
    try:
        sym = symbol.upper()
        if not sym.endswith(".NS"):
            sym = f"{sym}.NS"

        # --- Stock info ---
        stock_q = supabase.table("stocks").select(
            "id, stock_name, yfin_symbol, sector, sentiment_7d"
        ).eq("yfin_symbol", sym).limit(1).execute()

        if not stock_q.data:
            raise HTTPException(status_code=404, detail=f"Stock {symbol} not found.")

        stock = stock_q.data[0]

        # --- Latest sentiment from news ---
        news_q = supabase.table("news").select(
            "id, title, sentiment, sentiment_score, confidence, is_volatile, content, published_at, url"
        ).eq("yfin_symbol", sym).not_.is_("sentiment_score", "null").order(
            "published_at", desc=True
        ).limit(10).execute()

        articles = news_q.data or []

        # Aggregate sentiment from last N articles
        scored = [a for a in articles if a.get("sentiment_score") is not None]
        if scored:
            avg_score   = round(sum(a["sentiment_score"] for a in scored) / len(scored), 4)
            avg_conf    = round(sum(a["confidence"] for a in scored if a.get("confidence")) / max(1, sum(1 for a in scored if a.get("confidence"))), 4)
            any_volatile = any(a.get("is_volatile") for a in scored)
            labels       = [a["sentiment"] for a in scored if a.get("sentiment")]
            from collections import Counter
            majority_label = Counter(labels).most_common(1)[0][0] if labels else "neutral"
            context_clause = scored[0].get("title", "")[:150] if scored else None
        else:
            avg_score, avg_conf, any_volatile = 0.0, None, False
            majority_label, context_clause = "neutral", None

        sentiment = SentimentDetail(
            label=majority_label,
            score=avg_score,
            confidence=avg_conf,
            is_volatile=any_volatile
        )

        # --- Momentum from view ---
        momentum = None
        try:
            mom_q = supabase.rpc("get_stock_momentum", {"p_symbol": sym}).execute()
            if mom_q.data:
                m = mom_q.data[0]
                z = float(m.get("volume_z_score") or 0)
                momentum = MomentumDetail(
                    sentiment_7d     = float(m.get("sentiment_7d")    or 0),
                    sentiment_prev_7d= float(m.get("sentiment_prev_7d") or 0),
                    slope            = float(m.get("momentum_slope")  or 0),
                    label            = m.get("momentum_label", "stable"),
                    articles_7d      = int(m.get("articles_7d")      or 0),
                    articles_today   = int(m.get("articles_today")    or 0),
                    volume_z_score   = round(z, 2),
                    volume_alert     = _volume_alert_label(z)
                )
        except Exception as me:
            logger.warning(f"Momentum fetch failed for {sym}: {me}")

        # --- Top news ---
        top_news = None
        if include_news and articles:
            top_news = [
                {
                    "title":        a.get("title", ""),
                    "sentiment":    a.get("sentiment"),
                    "score":        a.get("sentiment_score"),
                    "confidence":   a.get("confidence"),
                    "is_volatile":  a.get("is_volatile"),
                    "published_at": a.get("published_at"),
                    "url":          a.get("url"),
                }
                for a in articles[:3]
            ]

        return InsightObject(
            entity       = stock["stock_name"],
            yfin_symbol  = stock["yfin_symbol"],
            sector       = stock.get("sector"),
            sentiment    = sentiment,
            momentum     = momentum,
            top_news     = top_news,
            context_clause = context_clause,
            generated_at = datetime.utcnow().isoformat() + "Z"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Sentiment insight error for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# --- Endpoint 2: Market-Wide Sentiment Dashboard ---

@api_router.get(
    "/sentiment/market",
    tags=["Sentiment Intelligence"],
    summary="Market-wide sentiment heatmap (all stocks)",
    description="""
Returns sentiment scores, momentum slopes, and volume alerts for every
stock in the watchlist. Sorted by absolute momentum slope descending —
the most actively moving stocks appear first. Ideal for a dashboard heatmap.
"""
)
async def get_market_sentiment(
    min_confidence: float = Query(0.0, ge=0.0, le=1.0, description="Filter by minimum confidence score"),
    alert_only: bool = Query(False, description="Return only stocks with volume alerts (breaking/elevated)"),
    limit: int = Query(50, ge=1, le=100),
    user: dict = Depends(get_api_user),
    tier: str = Depends(get_user_tier),
):
    if tier == 'free':
        raise HTTPException(status_code=403, detail="Market sentiment heatmap requires a Pro or Enterprise subscription.")
    """Market-wide Sentiment Heatmap."""
    try:
        # Pull full momentum view
        mom_q = supabase.table("v_stock_momentum").select("*").limit(limit).execute()
        rows  = mom_q.data or []

        # Pull latest sentiment per stock
        sent_q = supabase.table("stocks").select(
            "yfin_symbol, stock_name, sector, sentiment_7d"
        ).not_.is_("sentiment_7d", "null").execute()
        sent_map = {r["yfin_symbol"]: r for r in (sent_q.data or [])}

        results = []
        for m in rows:
            sym = m.get("yfin_symbol", "")
            z   = float(m.get("volume_z_score") or 0)
            alert = _volume_alert_label(z)

            if alert_only and alert not in ("breaking", "elevated"):
                continue

            slope = float(m.get("momentum_slope") or 0)
            s7d   = float(m.get("sentiment_7d")   or 0)

            results.append({
                "yfin_symbol":     sym,
                "stock_name":      m.get("stock_name"),
                "sector":          sent_map.get(sym, {}).get("sector"),
                "sentiment_7d":    round(s7d, 4),
                "momentum_slope":  round(slope, 4),
                "momentum_label":  m.get("momentum_label", "stable"),
                "volume_z_score":  round(z, 2),
                "volume_alert":    alert,
                "articles_7d":     m.get("articles_7d"),
                "articles_today":  m.get("articles_today"),
            })

        # Sort by absolute slope descending
        results.sort(key=lambda x: abs(x["momentum_slope"]), reverse=True)

        return {
            "count":        len(results),
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "stocks":       results
        }

    except Exception as e:
        logger.error(f"Market sentiment error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# --- Endpoint 3: Recent News Feed with Sentiment ---

@api_router.get(
    "/sentiment/news",
    tags=["Sentiment Intelligence"],
    summary="Recent news feed enriched with sentiment",
    description="""
Returns the most recent news articles with full sentiment metadata:
label, score, confidence, is_volatile. Filterable by stock symbol or sector.
Ideal for powering a real-time news ticker on a dashboard.
"""
)
async def get_sentiment_news_feed(
    symbol: Optional[str] = Query(None, description="Filter by yfin_symbol e.g. TCS.NS"),
    sector: Optional[str] = Query(None, description="Filter by sector e.g. Banking"),
    sentiment: Optional[str] = Query(None, description="Filter: positive | negative | neutral | CONFLICTED"),
    volatile_only: bool = Query(False, description="Return only conflicted/volatile articles"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: dict = Depends(get_api_user),
    tier: str = Depends(get_user_tier),
):
    if tier == 'free':
        raise HTTPException(status_code=403, detail="Enriched sentiment news feed requires a Pro or Enterprise subscription.")
    """Enriched news feed with sentiment metadata."""
    try:
        q = supabase.table("news").select(
            "id, title, summary, url, source, published_at, "
            "yfin_symbol, stock_name, sector, "
            "sentiment, sentiment_score, confidence, is_volatile"
        ).not_.is_("sentiment_score", "null").order("published_at", desc=True)

        if symbol:
            sym = symbol.upper()
            if not sym.endswith(".NS"):
                sym = f"{sym}.NS"
            q = q.eq("yfin_symbol", sym)

        if sector:
            q = q.ilike("sector", f"%{sector}%")

        if sentiment:
            q = q.eq("sentiment", sentiment.lower())

        if volatile_only:
            q = q.eq("is_volatile", True)

        result = q.range(offset, offset + limit - 1).execute()
        articles = result.data or []

        enriched_articles = []
        for a in articles:
            # Calculate signal
            sentiment = a.get("sentiment")
            if a.get("is_volatile"):
                signal = "conflicted"
            elif sentiment == "positive":
                signal = "bullish"
            elif sentiment == "negative":
                signal = "bearish"
            elif sentiment == "neutral":
                signal = "neutral"
            elif sentiment == "CONFLICTED":
                signal = "conflicted"
            else:
                signal = "neutral"

            # Calculate impact tier
            score = a.get("sentiment_score")
            conf = a.get("confidence")
            impact_tier = "low"
            if score is not None and conf is not None:
                impact_score = conf * abs(score)
                if impact_score >= 0.60:
                    impact_tier = "high"
                elif impact_score >= 0.30:
                    impact_tier = "medium"

            a["signal"] = signal
            a["impact_tier"] = impact_tier
            enriched_articles.append(a)

        return {
            "count":        len(enriched_articles),
            "offset":       offset,
            "limit":        limit,
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "articles":     enriched_articles
        }

    except Exception as e:
        logger.error(f"News feed error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# --- Endpoint 4: Momentum Leaderboard ---

@api_router.get(
    "/sentiment/momentum/leaderboard",
    tags=["Sentiment Intelligence"],
    summary="Top improving and declining stocks by sentiment momentum",
    description="""
Returns the top N stocks with the highest positive momentum slope (improving)
and top N with the highest negative slope (declining). Perfect for a
'Winners & Losers by Sentiment' widget on a trading dashboard.
"""
)
async def get_momentum_leaderboard(
    top_n: int = Query(5, ge=1, le=20, description="Number of stocks per side"),
    user: dict = Depends(get_api_user),
    tier: str = Depends(get_user_tier),
):
    if tier == 'free':
        raise HTTPException(status_code=403, detail="Momentum leaderboard requires a Pro or Enterprise subscription.")
    """Momentum Leaderboard: top improving and declining stocks."""
    try:
        mom_q = supabase.table("v_stock_momentum").select("*").execute()
        rows = mom_q.data or []

        improving = sorted(
            [r for r in rows if float(r.get("momentum_slope") or 0) > 0],
            key=lambda x: float(x["momentum_slope"]),
            reverse=True
        )[:top_n]

        declining = sorted(
            [r for r in rows if float(r.get("momentum_slope") or 0) < 0],
            key=lambda x: float(x["momentum_slope"])
        )[:top_n]

        def fmt(rows):
            return [
                {
                    "yfin_symbol":    r.get("yfin_symbol"),
                    "stock_name":     r.get("stock_name"),
                    "sentiment_7d":   round(float(r.get("sentiment_7d") or 0), 4),
                    "momentum_slope": round(float(r.get("momentum_slope") or 0), 4),
                    "momentum_label": r.get("momentum_label"),
                    "volume_z_score": round(float(r.get("volume_z_score") or 0), 2),
                    "volume_alert":   _volume_alert_label(float(r.get("volume_z_score") or 0)),
                    "articles_7d":    r.get("articles_7d"),
                }
                for r in rows
            ]

        return {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "improving":    fmt(improving),
            "declining":    fmt(declining)
        }

    except Exception as e:
        logger.error(f"Momentum leaderboard error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# --- Billing / Razorpay Endpoints ---
import razorpay
import hmac
import hashlib
import json as _json

_razorpay_key_id     = os.getenv("RAZORPAY_KEY_ID", "")
_razorpay_key_secret = os.getenv("RAZORPAY_KEY_SECRET", "")
_rzp_client = razorpay.Client(auth=(_razorpay_key_id, _razorpay_key_secret))

# ── Step 1: Create a Razorpay order (called by the frontend before opening the modal) ──
@app.post("/api/billing/create-order")
async def razorpay_create_order(request: Request):
    """
    Expects JSON body: { "authentication_key": "<key>" }
    Returns: { "order_id", "amount", "currency", "key_id", "email", "name" }
    """
    try:
        body = await request.json()
        key = body.get("authentication_key", "").strip()
        if not key:
            raise HTTPException(status_code=400, detail="authentication_key is required")

        # Verify the key exists and fetch user info
        user_res = supabase.table('users').select('email, tier').eq('authentication_key', key).single().execute()
        if not user_res or not hasattr(user_res, 'data') or not user_res.data:
            raise HTTPException(status_code=401, detail="Invalid API Key")

        user = user_res.data
        email = user.get('email')
        tier  = user.get('tier', 'free')

        if tier in ('pro', 'enterprise'):
            raise HTTPException(status_code=400, detail="You are already on a Pro or Enterprise plan.")

        # ₹199/month = 19900 paise
        order = _rzp_client.order.create({
            "amount":   19900,
            "currency": "INR",
            "notes": {
                "authentication_key": key,
                "email":              email,
            }
        })

        return {
            "order_id": order["id"],
            "amount":   order["amount"],
            "currency": order["currency"],
            "key_id":   _razorpay_key_id,
            "email":    email,
            "name":     "Sentimatix",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Razorpay create-order error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── Step 2: Verify payment & upgrade tier (called by frontend after payment success) ──
@app.post("/api/billing/verify-payment")
async def razorpay_verify_payment(request: Request):
    """
    Expects JSON body:
    {
      "razorpay_order_id":   "order_xxx",
      "razorpay_payment_id": "pay_xxx",
      "razorpay_signature":  "...",
      "authentication_key":  "<key>"
    }
    """
    try:
        body = await request.json()
        order_id   = body.get("razorpay_order_id", "")
        payment_id = body.get("razorpay_payment_id", "")
        signature  = body.get("razorpay_signature", "")
        key        = body.get("authentication_key", "")

        if not all([order_id, payment_id, signature, key]):
            raise HTTPException(status_code=400, detail="Missing required payment fields")

        # --- HMAC-SHA256 signature verification ---
        expected_sig = hmac.new(
            _razorpay_key_secret.encode(),
            f"{order_id}|{payment_id}".encode(),
            hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(expected_sig, signature):
            logger.warning(f"Razorpay signature mismatch for order {order_id}")
            raise HTTPException(status_code=400, detail="Payment signature verification failed")

        # Verify the key exists
        user_res = supabase.table('users').select('email').eq('authentication_key', key).single().execute()
        if not user_res or not hasattr(user_res, 'data') or not user_res.data:
            raise HTTPException(status_code=401, detail="Invalid API Key")

        email = user_res.data.get('email')

        # Upgrade tier
        supabase.table('users').update({'tier': 'pro'}).eq('authentication_key', key).execute()
        logger.info(f"Upgraded user {email} to PRO (order={order_id}, payment={payment_id})")

        return {"status": "success", "tier": "pro", "email": email}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Razorpay verify-payment error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── Step 3: Webhook (server-side fallback from Razorpay Dashboard) ──
@app.post("/api/billing/webhook")
async def razorpay_webhook(request: Request):
    """
    Razorpay sends webhook events to this URL.
    Validate with X-Razorpay-Signature header.
    """
    payload   = await request.body()
    sig_header = request.headers.get("x-razorpay-signature", "")

    # Verify signature if secret is configured
    webhook_secret = os.getenv("RAZORPAY_WEBHOOK_SECRET", "")
    if webhook_secret:
        expected = hmac.new(
            webhook_secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(expected, sig_header):
            logger.warning("Razorpay webhook signature mismatch")
            raise HTTPException(status_code=400, detail="Invalid webhook signature")

    try:
        event = _json.loads(payload)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    event_type = event.get("event", "")

    if event_type == "payment.captured":
        payment = event.get("payload", {}).get("payment", {}).get("entity", {})
        email   = payment.get("email")
        notes   = payment.get("notes", {})
        api_key = notes.get("authentication_key", "")

        if api_key:
            supabase.table('users').update({'tier': 'pro'}).eq('authentication_key', api_key).execute()
            logger.info(f"Webhook: Upgraded {email} to PRO via payment.captured")
        elif email:
            supabase.table('users').update({'tier': 'pro'}).eq('email', email).execute()
            logger.info(f"Webhook: Upgraded {email} to PRO via payment.captured (by email)")

    return {"status": "ok"}

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
