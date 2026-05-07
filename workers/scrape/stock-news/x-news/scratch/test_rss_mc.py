
import feedparser
import requests

url = "https://www.moneycontrol.com/rss/MCtopnews.xml"
headers = {"User-Agent": "Mozilla/5.0"}

print(f"Testing RSS: {url}")
try:
    response = requests.get(url, headers=headers, timeout=10)
    print(f"Status: {response.status_code}")
    print(f"Content Length: {len(response.text)}")

    feed = feedparser.parse(response.text)
    print(f"Entries found: {len(feed.entries)}")
except Exception as e:
    print(f"Error: {e}")
