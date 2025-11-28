#!/usr/bin/env python3
"""
Sentiment Batch Updater - Updates sentiment scores for all stocks
Run this periodically (e.g., every hour) via cron job or scheduler
"""

import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv
from supabase import create_client, Client
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def calculate_weighted_sentiment(sentiment_data, sentiment_days):
    """Calculate weighted average sentiment with time decay"""
    if not sentiment_data:
        return 0.0
    
    total_weight = 0
    weighted_sum = 0
    
    for data in sentiment_data:
        # Weight calculation: newer articles get higher weight
        # Weight decreases linearly from 1.0 (today) to 0.1 (sentiment_days ago)
        weight = max(0.1, 1.0 - (data['days_old'] / sentiment_days * 0.9))
        
        weighted_sum += data['score'] * weight
        total_weight += weight
    
    return weighted_sum / total_weight if total_weight > 0 else 0.0

def update_stock_sentiment(stock_symbol, yfin_symbol, sentiment_days=30):
    """Update sentiment for a single stock"""
    try:
        # Calculate date cutoff
        cutoff_date = datetime.now() - timedelta(days=sentiment_days)
        
        # Get sentiment data for this stock
        news_query = supabase.table('news').select(
            'sentiment_score, published_at'
        ).eq('yfin_symbol', yfin_symbol).gte('published_at', cutoff_date.isoformat()).execute()
        
        if not news_query.data:
            return 0.0
        
        # Process sentiment data
        sentiment_data = []
        for item in news_query.data:
            if item.get('sentiment_score') is not None:
                try:
                    published_at = datetime.fromisoformat(item.get('published_at', '').replace('Z', '+00:00'))
                    days_old = (datetime.now(published_at.tzinfo) - published_at).days
                    
                    sentiment_data.append({
                        'score': float(item.get('sentiment_score', 0)),
                        'days_old': days_old
                    })
                except (ValueError, TypeError):
                    # Skip invalid dates
                    continue
        
        # Calculate weighted sentiment
        avg_sentiment = calculate_weighted_sentiment(sentiment_data, sentiment_days)
        
        return avg_sentiment
        
    except Exception as e:
        logger.error(f"Error updating sentiment for {stock_symbol}: {str(e)}")
        return 0.0

def update_all_stocks_sentiment():
    """Update sentiment for all stocks"""
    try:
        logger.info("Starting sentiment update for all stocks...")
        
        # Get all stocks - use correct column names from stocks table
        stocks_query = supabase.table('stocks').select('id, stock_name, yfin_symbol').execute()
        
        if not stocks_query.data:
            logger.warning("No stocks found")
            return
        
        updated_count = 0
        for stock in stocks_query.data:
            stock_id = stock['id']
            stock_name = stock.get('stock_name', 'Unknown')
            yfin_symbol = stock['yfin_symbol']
            
            # Extract clean symbol from yfin_symbol for display
            clean_symbol = yfin_symbol.replace('.NS', '') if yfin_symbol else stock_name
            
            # Calculate 30-day and 7-day sentiment
            sentiment_30d = update_stock_sentiment(clean_symbol, yfin_symbol, 30)
            sentiment_7d = update_stock_sentiment(clean_symbol, yfin_symbol, 7)
            
            # Update the stocks table
            try:
                supabase.table('stocks').update({
                    'sentiment_30d': round(sentiment_30d * 100, 2),  # Convert to percentage
                    'sentiment_7d': round(sentiment_7d * 100, 2),   # Convert to percentage
                    'sentiment_updated_at': datetime.now().isoformat()
                }).eq('id', stock_id).execute()
                
                updated_count += 1
                logger.info(f"Updated {clean_symbol} ({stock_name}): 30d={sentiment_30d*100:.2f}%, 7d={sentiment_7d*100:.2f}%")
                
            except Exception as e:
                logger.error(f"Error updating database for {clean_symbol}: {str(e)}")
                continue
        
        logger.info(f"Sentiment update completed. Updated {updated_count} stocks.")
        
    except Exception as e:
        logger.error(f"Error in batch sentiment update: {str(e)}")

def update_single_stock_sentiment(yfin_symbol):
    """Update sentiment for a single stock (for real-time updates)"""
    try:
        # Get stock info - use correct column names
        stock_query = supabase.table('stocks').select('id, stock_name').eq('yfin_symbol', yfin_symbol).execute()
        
        if not stock_query.data:
            logger.warning(f"Stock not found: {yfin_symbol}")
            return
        
        stock = stock_query.data[0]
        stock_id = stock['id']
        stock_name = stock.get('stock_name', 'Unknown')
        
        # Extract clean symbol for display
        clean_symbol = yfin_symbol.replace('.NS', '') if yfin_symbol else stock_name
        
        # Calculate sentiment
        sentiment_30d = update_stock_sentiment(clean_symbol, yfin_symbol, 30)
        sentiment_7d = update_stock_sentiment(clean_symbol, yfin_symbol, 7)
        
        # Update database
        supabase.table('stocks').update({
            'sentiment_30d': round(sentiment_30d * 100, 2),
            'sentiment_7d': round(sentiment_7d * 100, 2),
            'sentiment_updated_at': datetime.now().isoformat()
        }).eq('id', stock_id).execute()
        
        logger.info(f"Updated sentiment for {clean_symbol} ({stock_name}): 30d={sentiment_30d*100:.2f}%, 7d={sentiment_7d*100:.2f}%")
        
    except Exception as e:
        logger.error(f"Error updating sentiment for {yfin_symbol}: {str(e)}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Update single stock
        yfin_symbol = sys.argv[1]
        update_single_stock_sentiment(yfin_symbol)
    else:
        # Update all stocks
        update_all_stocks_sentiment()