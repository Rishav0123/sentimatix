
from bs4 import BeautifulSoup

with open("gnews_debug.html", "r", encoding="utf-8") as f:
    soup = BeautifulSoup(f.read(), "html.parser")

links = soup.find_all("a", href=True)
print(f"Total links: {len(links)}")

found_count = 0
for link in links:
    href = link['href']
    if "./articles/" in href or "articles/" in href:
        found_count += 1
        print(f"\nLink {found_count}: {href}")
        print(f"Text: {link.get_text(strip=True)}")
        # Print the classes of the link and its immediate parents
        print(f"Link classes: {link.get('class')}")
        parent = link.parent
        if parent:
            print(f"Parent tag: {parent.name}, classes: {parent.get('class')}")
            grandparent = parent.parent
            if grandparent:
                print(f"Grandparent tag: {grandparent.name}, classes: {grandparent.get('class')}")
        
        if found_count >= 5:
            break

if found_count == 0:
    print("No article links found with './articles/'")
