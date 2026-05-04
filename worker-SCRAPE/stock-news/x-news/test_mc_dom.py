"""
Debug: Check what Selenium actually gets back from MoneyControl.
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

url = "https://www.moneycontrol.com/company-article/jindalsteel/news/jsp"
print(f"Testing URL: {url}")

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
    print(f"Page title: {driver.title}")
    print(f"Current URL: {driver.current_url}")

    # Check for access denied
    if "access denied" in driver.title.lower() or "access denied" in driver.page_source.lower()[:500]:
        print("STATUS: ACCESS DENIED - blocked by MoneyControl WAF")
    else:
        print("STATUS: Page loaded OK")

    # Try the original selector
    articles_old = driver.find_elements(By.CSS_SELECTOR, "#mc_mainWrapper .FL.rightCont .MT15.PT10.PB10")
    print(f"Old selector matches: {len(articles_old)}")

    # Check first article URL if any
    if articles_old:
        for elem in articles_old[0].find_elements(By.XPATH, './/*'):
            if elem.tag_name == "a":
                href = elem.get_attribute("href")
                if href:
                    print(f"First article URL: {href}")
                    break

    # Try broader selectors to see what IS on the page
    li_items = driver.find_elements(By.CSS_SELECTOR, "li.clearfix")
    print(f"Broader 'li.clearfix' matches: {len(li_items)}")

    # Print a snippet of the page source for diagnosis
    source_snippet = driver.page_source[:3000].encode('ascii', 'replace').decode()
    print(f"\nPage source snippet (first 3000 chars):\n{source_snippet}")

finally:
    driver.quit()
