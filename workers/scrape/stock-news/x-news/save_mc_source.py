"""
Save MoneyControl Source
"""
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time

def save_source():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    
    url = "https://www.moneycontrol.com/company-article/divislaboratories/news/DL03"
    driver.get(url)
    time.sleep(5)
    
    with open("mc_source.html", "w", encoding="utf-8") as f:
        f.write(driver.page_source)
    
    driver.quit()

if __name__ == "__main__":
    save_source()
