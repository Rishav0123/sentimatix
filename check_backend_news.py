import requests
import json
from datetime import datetime, timedelta

def check_backend_news():
    symbol = "TCS"
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    
    url = "http://localhost:8000/api/news"
    params = {
        "stock_symbol": symbol,
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d"),
        "limit": 100
    }
    
    print(f"Fetching news from {url} with params {params}")
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        news_items = data.get("data", [])
        print(f"Found {len(news_items)} news items.")
        
        for i, item in enumerate(news_items[:10], 1):
            print(f"{i}. [{item.get('published_at')}] {item.get('title')} (Source: {item.get('source')}, Symbol: {item.get('stock_symbol')})")
            
        with open("backend_news_check.json", "w") as f:
            json.dump(data, f, indent=2)
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_backend_news()
