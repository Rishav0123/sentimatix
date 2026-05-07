
from bs4 import BeautifulSoup

with open("gnews_debug.html", "r", encoding="utf-8") as f:
    soup = BeautifulSoup(f.read(), "html.parser")

title_text = "Q4 results: Reliance Industries"
# Find element containing the title
element = soup.find(string=lambda t: title_text in t)

if element:
    print(f"Found element: {element.name}")
    parent = element.parent
    for i in range(5):
        if not parent: break
        print(f"Parent {i+1}: {parent.name}, class: {parent.get('class')}")
        parent = parent.parent
else:
    print("Title not found in soup")
