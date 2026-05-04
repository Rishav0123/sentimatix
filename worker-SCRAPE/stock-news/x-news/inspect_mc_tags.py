"""
Inspect MoneyControl Tags: Print all 'a' tags with class 'g_14bl'
"""
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import time

def inspect_tags():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    
    url = "https://www.moneycontrol.com/company-article/divislaboratories/news/DL03"
    driver.get(url)
    time.sleep(3) # Wait for load
    
    print("Tags with class g_14bl:")
    tags = driver.find_elements(By.CSS_SELECTOR, "a.g_14bl")
    for i, tag in enumerate(tags):
        text = tag.text.strip()
        href = tag.get_attribute("href")
        # Get parent info
        parent = tag.find_element(By.XPATH, "..")
        p_class = parent.get_attribute("class")
        gp = parent.find_element(By.XPATH, "..")
        gp_class = gp.get_attribute("class")
        
        print(f"{i}. Text: {text[:50]}...")
        print(f"   Parent Class: {p_class}")
        print(f"   Grandparent Class: {gp_class}")
        if i > 10: break
        
    driver.quit()

if __name__ == "__main__":
    inspect_tags()
