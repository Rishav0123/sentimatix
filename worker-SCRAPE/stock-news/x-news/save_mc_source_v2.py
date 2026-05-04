"""
Save MoneyControl Source v2
"""
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time

def save_source():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    
    url = "https://www.moneycontrol.com/company-article/divislaboratories/news/DL03"
    driver.get(url)
    time.sleep(5)
    
    with open("mc_source_v2.html", "w", encoding="utf-8") as f:
        f.write(driver.page_source)
    
    driver.quit()

if __name__ == "__main__":
    save_source()
