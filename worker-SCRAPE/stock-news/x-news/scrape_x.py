import requests
import os

BEARER_TOKEN = "AAAAAAAAAAAAAAAAAAAAAOOn4gEAAAAADdzDfij5hXGfM9RfDp7Q3Trm8iE%3DSj4xJv8N9X2sJQ61UlMxa6GXEnK7Byp1tbVZN9oNfQTWt5xuKY"

def fetch_tweets(query: str, max_results: int = 10):
    url = "https://api.twitter.com/2/tweets/search/recent"
    headers = {"Authorization": f"Bearer {BEARER_TOKEN}"}
    params = {
        "query": query,
        "max_results": max_results,
        "tweet.fields": "created_at,author_id,text"
    }
    response = requests.get(url, headers=headers, params=params)
    if response.status_code != 200:
        raise Exception(f"Request failed: {response.status_code}, {response.text}")
    return response.json()

if __name__ == "__main__":
    tweets = fetch_tweets("TCS OR Tata Consultancy Services", max_results=10)
    for t in tweets.get("data", []):
        print(f"{t['created_at']} - {t['text']}\n")
