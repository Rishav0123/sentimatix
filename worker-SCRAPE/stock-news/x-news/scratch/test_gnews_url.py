
import requests
from bs4 import BeautifulSoup
from datetime import datetime

def test_gnews(stock, include_date=True):
    date_str = datetime.now().strftime('%Y-%m-%d')
    if include_date:
        query = f"{stock}+finance+india+{date_str}"
    else:
        query = f"{stock}+finance+india"
        
    url = f"https://news.google.com/search?q={query}&hl=en-IN&gl=IN&ceid=IN:en"
    print(f"Testing URL: {url}")
    
    response = requests.get(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"})
    print(f"Status Code: {response.status_code}")
    
    soup = BeautifulSoup(response.text, "html.parser")
    articles = soup.select("article")
    print(f"Articles found: {len(articles)}")
    
    if articles:
        for i, art in enumerate(articles[:3]):
            title = art.select_one("h3") or art.select_one("h4")
            title_text = title.get_text() if title else "No Title"
            print(f"  {i+1}. {title_text}")

print("--- Testing WITH date ---")
test_gnews("Reliance")
print("\n--- Testing WITHOUT date ---")
test_gnews("Reliance", include_date=False)
