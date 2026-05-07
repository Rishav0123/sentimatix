
import feedparser
import requests

url = "https://www.business-standard.com/rss/markets-106.rss"
headers = {"User-Agent": "Mozilla/5.0"}

print(f"Testing RSS: {url}")
response = requests.get(url, headers=headers)
print(f"Status: {response.status_code}")
print(f"Content Length: {len(response.text)}")

feed = feedparser.parse(response.text)
print(f"Entries found: {len(feed.entries)}")
if feed.entries:
    print(f"First entry: {feed.entries[0].title}")
