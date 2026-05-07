
import requests

url = "https://news.google.com/search?q=Reliance+finance+india&hl=en-IN&gl=IN&ceid=IN:en"
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"}

response = requests.get(url, headers=headers)
with open("gnews_debug.html", "w", encoding="utf-8") as f:
    f.write(response.text)
print(f"Status: {response.status_code}")
print(f"HTML Length: {len(response.text)}")
