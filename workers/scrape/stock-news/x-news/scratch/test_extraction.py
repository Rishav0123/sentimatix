
from bs4 import BeautifulSoup

with open("gnews_debug.html", "r", encoding="utf-8") as f:
    soup = BeautifulSoup(f.read(), "html.parser")

items = soup.select('div.IFHyqb')
print(f"Found {len(items)} items")

for i, item in enumerate(items[:3]):
    print(f"\nItem {i+1}:")
    link_tag = item.select_one('a.JtKRv')
    if link_tag:
        print(f"  Title: {link_tag.get_text(strip=True)}")
        print(f"  Link: {link_tag['href']}")
    
    # Let's find the source name and time
    # Looking for classes in the item
    source_tag = item.select_one('div.vr7PYb') # Common class for source
    if source_tag:
        print(f"  Source: {source_tag.get_text(strip=True)}")
    
    time_tag = item.select_one('time')
    if time_tag:
        print(f"  Time: {time_tag.get('datetime')} ({time_tag.get_text(strip=True)})")

    # If vr7PYb not found, look for any div with a short text
    if not source_tag:
        for div in item.find_all('div'):
            text = div.get_text(strip=True)
            if 2 < len(text) < 30 and 'More' not in text:
                print(f"  Potential Source (from div): {text}")
                break
