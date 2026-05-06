
from bs4 import BeautifulSoup

with open("gnews_debug.html", "r", encoding="utf-8") as f:
    soup = BeautifulSoup(f.read(), "html.parser")

links = soup.find_all("a", href=True)
for i, link in enumerate(links[:20]):
    print(f"{i+1}. {link.get_text(strip=True)} -> {link['href']}")

body_text = soup.get_text(separator=' ', strip=True)
print(f"\nBody Text snippet (first 500 chars):")
print(body_text[:500])
