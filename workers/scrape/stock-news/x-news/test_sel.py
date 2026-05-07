from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time

chrome_options = Options()
chrome_options.add_argument('--headless=new')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--window-size=1920,1080')
chrome_options.add_argument('--user-agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"')

driver = webdriver.Chrome(options=chrome_options)
driver.get('https://www.moneycontrol.com/company-article/karurvysyabank/news/KVB')
time.sleep(5) # wait for page to load fully

articles = driver.find_elements(By.CSS_SELECTOR, '.MT15.PT10.PB10')
print(f'Found {len(articles)} articles with Selenium using .MT15.PT10.PB10')

for i, a in enumerate(articles):
    try:
        title = a.find_element(By.CSS_SELECTOR, 'a.g_14bl strong').text.strip()
        print(f'Article {i+1}: {title[:80]}...')
    except Exception as e:
        print(f'Article {i+1}: Exception getting title')

print("\n--- Let's try scoping it to the main content area ---")
main_area = driver.find_elements(By.CSS_SELECTOR, '#mc_mainWrapper .FL.rightCont.pcContainer .MT15.PT10.PB10')
print(f'Found {len(main_area)} articles inside #mc_mainWrapper')

for i, a in enumerate(main_area):
    try:
        title = a.find_element(By.CSS_SELECTOR, 'a.g_14bl strong').text.strip()
        print(f'Main Article {i+1}: {title[:80]}...')
    except Exception as e:
        print(f'Main Article {i+1}: Exception getting title')

driver.quit()
