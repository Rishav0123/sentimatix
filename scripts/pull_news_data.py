import os
import json
import requests
from datetime import datetime, timedelta

def pull_data():
    base_url = "https://sentimatix-production.up.railway.app/api/v1"
    
    # We found this API key in the Supabase database for rishavdutta.kgp@gmail.com
    api_key = "686b700d-9c97-4c41-ae2a-52755f2abaf1"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    results = {}
    
    # 1. Fetch supported entities (to see which stocks are available)
    print("Fetching supported entities...")
    entities_url = f"{base_url}/entities"
    try:
        res = requests.get(entities_url, headers=headers, params={"limit": 5})
        res.raise_for_status()
        entities_data = res.json()
        results["entities"] = entities_data.get("data", [])[:10]  # Store top 10 for display
        print(f"Successfully fetched {len(entities_data.get('data', []))} entities.")
    except Exception as e:
        print(f"Failed to fetch entities: {e}")
        results["entities_error"] = str(e)

    # 2. Fetch latest news for a few top stocks (e.g., RELIANCE, TCS)
    print("\nFetching news for RELIANCE and TCS...")
    news_url = f"{base_url}/news"
    params = {
        "symbols": "RELIANCE,TCS",
        "limit": 10
    }
    try:
        res = requests.get(news_url, headers=headers, params=params)
        res.raise_for_status()
        news_data = res.json()
        results["news"] = news_data.get("data", [])
        print(f"Successfully fetched {len(news_data.get('data', []))} news articles.")
    except Exception as e:
        print(f"Failed to fetch news: {e}")
        results["news_error"] = str(e)

    # 3. Fetch sentiment for RELIANCE and TCS
    print("\nFetching sentiment for RELIANCE and TCS...")
    sentiment_url = f"{base_url}/sentiment"
    try:
        res = requests.get(sentiment_url, headers=headers, params={"symbols": "RELIANCE,TCS"})
        res.raise_for_status()
        sentiment_data = res.json()
        results["sentiment"] = sentiment_data.get("data", [])
        print(f"Successfully fetched sentiment for {len(sentiment_data.get('data', []))} stocks.")
    except Exception as e:
        print(f"Failed to fetch sentiment: {e}")
        results["sentiment_error"] = str(e)

    # 4. Fetch trending stocks
    print("\nFetching trending stocks (last 24 hours)...")
    trending_url = f"{base_url}/analytics/trending"
    try:
        res = requests.get(trending_url, headers=headers, params={"hours": 24})
        res.raise_for_status()
        trending_data = res.json()
        results["trending"] = trending_data.get("data", [])[:10]
        print(f"Successfully fetched {len(trending_data.get('data', []))} trending stocks.")
    except Exception as e:
        print(f"Failed to fetch trending stocks: {e}")
        results["trending_error"] = str(e)

    # 5. Fetch sector sentiment
    print("\nFetching sector sentiment...")
    sector_url = f"{base_url}/sentiment/sectors"
    try:
        res = requests.get(sector_url, headers=headers, params={"period": "7d"})
        res.raise_for_status()
        sector_data = res.json()
        results["sectors"] = sector_data.get("data", [])
        print(f"Successfully fetched {len(sector_data.get('data', []))} sectors.")
    except Exception as e:
        print(f"Failed to fetch sector sentiment: {e}")
        results["sectors_error"] = str(e)

    # Save all output to a local JSON file
    output_file = "pulled_api_data.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\nAll data successfully saved to: {os.path.abspath(output_file)}")

if __name__ == "__main__":
    pull_data()
