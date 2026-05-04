import requests
from bs4 import BeautifulSoup

url = 'https://www.moneycontrol.com/company-article/karurvysyabank/news/KVB'
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.text, 'html.parser')

articles = soup.select('.MT15.PT10.PB10')
if articles:
    a = articles[0]
    p = a.parent
    print(f'Immediate parent: {p.name}, id={p.get("id")}, class={p.get("class")}')
    p2 = p.parent
    print(f'Grandparent: {p2.name}, id={p2.get("id")}, class={p2.get("class")}')
