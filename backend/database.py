from datetime import datetime, timedelta
from typing import List, Optional
from supabase import Client

async def get_stock_prices(
    supabase: Client,
    stock_id: str,
    start_date: datetime,
    end_date: datetime
) -> List[dict]:
    """
    Fetch price rows either by stock_id (UUID) or by yfin_symbol (e.g., HDFCBANK or HDFCBANK.NS).

    The API layer may pass a bare symbol for routes like /stocks/prices/{symbol}.
    This function now supports both forms.
    """
    try:
        print(stock_id)
        print(f"Querying stock prices for {stock_id} from {start_date} to {end_date}")

        # Build base query
        query = supabase.table('stock_prices').select('*')

        key = (stock_id or "").strip()
        # Heuristic: UUIDs contain dashes and are 36 chars; otherwise treat as symbol
        is_uuid_like = ('-' in key and len(key) >= 32)
        if is_uuid_like:
            query = query.eq('stock_id', key)
        else:
            clean = key.upper().replace('.NS', '')
            # Match either with .NS suffix or without using in_ filter
            query = query.in_('yfin_symbol', [f"{clean}.NS", clean])

        response = query \
            .gte('date', start_date.strftime('%Y-%m-%d')) \
            .lte('date', end_date.strftime('%Y-%m-%d')) \
            .order('date') \
            .execute()

        print(f"Query response: {response}")
        return response.data if response and hasattr(response, 'data') else []
    except Exception as e:
        print(f"Error in get_stock_prices: {str(e)}")
        return []

async def get_stock_sentiments(
    supabase: Client,
    stock_id: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> List[dict]:
    query = supabase.table('stock_sentiments') \
        .select('*') \
        .eq('stock_id', stock_id)
    
    if start_date:
        query = query.gte('date', start_date.strftime('%Y-%m-%d'))
    if end_date:
        query = query.lte('date', end_date.strftime('%Y-%m-%d'))
    
    response = query.order('date').execute()
    return response.data

def get_stock_predictions(
    supabase: Client,
    stock_symbol: str
) -> List[dict]:
    try:
        response = supabase.table('stock_predictions') \
            .select('*,metrics,indicators') \
            .eq('stock_symbol', stock_symbol) \
            .order('prediction_date', desc=True) \
            .limit(5) \
            .execute()
        
        # Validate and clean the response data
        if not response.data:
            return []
            
        clean_predictions = []
        for pred in response.data:
            if not isinstance(pred, dict):
                continue
                
            # Ensure metrics and indicators are dictionaries
            metrics = pred.get('metrics', {})
            if not isinstance(metrics, dict):
                metrics = {}
                
            indicators = pred.get('indicators', {})
            if not isinstance(indicators, dict):
                indicators = {}
                
            clean_pred = {
                'id': str(pred.get('id', '')),
                'stock_symbol': str(pred.get('stock_symbol', stock_symbol)),
                'predicted_price': float(pred.get('predicted_price', 0)),
                'predicted_change': float(pred.get('predicted_change', 0)),
                'confidence': float(pred.get('confidence', 0)),
                'current_price': float(pred.get('current_price', 0)),
                'direction': str(pred.get('direction', 'neutral')),
                'prediction_date': pred.get('prediction_date', ''),
                'metrics': {
                    'accuracy': float(metrics.get('accuracy', 0)),
                    'precision': float(metrics.get('precision', 0)),
                    'recall': float(metrics.get('recall', 0)),
                    'f1_score': float(metrics.get('f1_score', 0))
                },
                'indicators': {
                    'rsi': float(indicators.get('rsi', 0)),
                    'macd': float(indicators.get('macd', 0)),
                    'sma': float(indicators.get('sma', 0)),
                    'ema': float(indicators.get('ema', 0))
                }
            }
            clean_predictions.append(clean_pred)
            
        return clean_predictions
    except Exception as e:
        print(f"Error fetching predictions from database: {str(e)}")
        return []

async def get_latest_stock_prices(
    supabase: Client,
    limit: int = 10
) -> List[dict]:
    try:
        # Get latest date
        latest_date_response = supabase.table('stock_prices') \
            .select('date') \
            .order('date', desc=True) \
            .limit(1) \
            .execute()
        
        if not latest_date_response.data:
            return []
        
        latest_date = latest_date_response.data[0]['date']
        
        # Get stock prices for latest date
        response = supabase.table('stock_prices') \
            .select('*') \
            .eq('date', latest_date) \
            .order('volume', desc=True) \
            .limit(limit) \
            .execute()
        
        # Filter out any entries with empty or invalid stock IDs
        valid_stocks = []
        for stock in response.data:
            if stock.get('symbol') or stock.get('stock_id'):
                valid_stocks.append({
                    'symbol': stock.get('symbol') or stock.get('stock_id', '').replace('.NS', ''),
                    'stock_id': stock.get('stock_id', ''),
                    'open': float(stock.get('open', 0)),
                    'high': float(stock.get('high', 0)),
                    'low': float(stock.get('low', 0)),
                    'close': float(stock.get('close', 0)),
                    'volume': int(float(stock.get('volume', 0))),
                    'date': stock.get('date', latest_date)
                })
        
        return valid_stocks
    except Exception as e:
        print(f"Error in get_latest_stock_prices: {str(e)}")
        return []

async def get_market_overview(supabase: Client) -> dict:
    # Get latest prices for all stocks
    latest_prices = await get_latest_stock_prices(supabase, limit=100)
    
    # Calculate price changes
    stocks_with_changes = []
    for price in latest_prices:
        # Get previous day's price
        prev_date = (datetime.strptime(price['date'], '%Y-%m-%d') - timedelta(days=1)).strftime('%Y-%m-%d')
        prev_price_response = supabase.table('stock_prices') \
            .select('close') \
            .eq('stock_id', price['stock_id']) \
            .eq('date', prev_date) \
            .execute()
        
        prev_close = prev_price_response.data[0]['close'] if prev_price_response.data else price['open']
        change = price['close'] - prev_close
        change_percent = (change / prev_close) * 100 if prev_close else 0
        
        stocks_with_changes.append({
            'symbol': price['stock_id'],
            'last_price': price['close'],
            'change': change,
            'change_percent': change_percent,
            'volume': price['volume']
        })
    
    # Sort for top gainers, losers, and most active
    gainers = sorted(stocks_with_changes, key=lambda x: x['change_percent'], reverse=True)[:5]
    losers = sorted(stocks_with_changes, key=lambda x: x['change_percent'])[:5]
    most_active = sorted(stocks_with_changes, key=lambda x: x['volume'], reverse=True)[:5]
    
    return {
        'top_gainers': gainers,
        'top_losers': losers,
        'most_active': most_active
    }