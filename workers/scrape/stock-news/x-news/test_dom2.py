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
    path = []
    while p and p.name != 'body':
        path.append(f'{p.name}#{p.get("id", "")}@{p.get("class", "")}')
        p = p.parent
    print(path)
