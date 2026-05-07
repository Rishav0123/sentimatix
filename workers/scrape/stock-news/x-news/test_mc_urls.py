"""
Debug: Print ALL article URLs to understand what patterns to filter.
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

url = "https://www.moneycontrol.com/company-article/jindalsteel/news/jsp"
print(f"URL: {url}\n")

chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

try:
    driver.get(url)
    articles = driver.find_elements(By.CSS_SELECTOR, "#mc_mainWrapper .FL.rightCont .MT15.PT10.PB10")
    print(f"Total articles found by selector: {len(articles)}\n")
    
    for i, article in enumerate(articles, 1):
        article_url = None
        for elem in article.find_elements(By.XPATH, './/*'):
            if elem.tag_name == "a":
                href = elem.get_attribute("href")
                if href:
                    article_url = href
                    break
        try:
            title = article.find_element(By.CSS_SELECTOR, "a.g_14bl strong").text.strip()
            title_safe = title.encode('ascii', 'replace').decode()
        except:
            title_safe = "(no title)"
        
        print(f"Article {i}:")
        print(f"  Title: {title_safe[:70]}")
        print(f"  URL:   {article_url}")
        print()

finally:
    driver.quit()
