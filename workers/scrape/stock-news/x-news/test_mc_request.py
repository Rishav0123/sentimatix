import requests

url = "https://www.moneycontrol.com/company-article/divislaboratories/news/DL03"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}
response = requests.get(url, headers=headers, allow_redirects=True)
print(f"Status: {response.status_code}")
print(f"Final URL: {response.url}")
print(f"Redirects: {response.history}")
