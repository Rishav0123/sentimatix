import os
import json
import csv
import requests

def generate_sample():
    base_url = "https://sentimatix-production.up.railway.app/api/v1"
    api_key = "686b700d-9c97-4c41-ae2a-52755f2abaf1"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # We will pull 100 records per page for 10 pages to get 1000 records
    all_news = []
    
    print("Generating Sample Dataset for Enterprise Prospects...")
    
    for page in range(1, 11):
        print(f"Fetching page {page}/10...")
        news_url = f"{base_url}/news"
        params = {
            "limit": 100,
            "page": page
        }
        try:
            res = requests.get(news_url, headers=headers, params=params)
            if res.status_code != 200:
                print(f"Failed to fetch page {page}: {res.status_code} - {res.text}")
                break
            news_data = res.json().get("data", [])
            all_news.extend(news_data)
            if len(news_data) < 100:
                break # Reached the end early
        except Exception as e:
            print(f"Failed to fetch news on page {page}: {e}")
            break

    if not all_news:
        print("No data fetched.")
        return

    # Process to clean structure
    cleaned_data = []
    for item in all_news:
        # Extract stock ticker from entities if available
        symbols = [e.get("symbol") for e in item.get("entities", []) if e.get("symbol")]
        primary_symbol = symbols[0] if symbols else ""
        
        cleaned_item = {
            "news_id": item.get("uuid"),
            "published_at": item.get("published_at"),
            "source": item.get("source"),
            "title": item.get("title"),
            "snippet": item.get("snippet", ""),
            "primary_ticker": primary_symbol,
            "sentiment_label": item.get("sentiment"),
            "sentiment_score": item.get("sentiment_score"),
            "confidence": item.get("confidence"),
            "is_market_sensitive": item.get("is_market_sensitive", False),
            "url": item.get("url")
        }
        cleaned_data.append(cleaned_item)

    # Save to JSON
    json_path = os.path.join(os.path.dirname(__file__), "..", "docs", "enterprise", "sample_dataset.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(cleaned_data, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(cleaned_data)} records to JSON: {os.path.abspath(json_path)}")
    
    # Save to CSV
    csv_path = os.path.join(os.path.dirname(__file__), "..", "docs", "enterprise", "sample_dataset.csv")
    if cleaned_data:
        keys = cleaned_data[0].keys()
        with open(csv_path, "w", newline='', encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(cleaned_data)
        print(f"Saved {len(cleaned_data)} records to CSV: {os.path.abspath(csv_path)}")

if __name__ == "__main__":
    generate_sample()
