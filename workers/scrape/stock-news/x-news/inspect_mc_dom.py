"""
Inspect MoneyControl DOM: Print classes of elements inside .leftCont
"""
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

def inspect_dom():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    
    url = "https://www.moneycontrol.com/company-article/divislaboratories/news/DL03"
    driver.get(url)
    
    print("Elements inside .leftCont:")
    left_cont = driver.find_element(By.CSS_SELECTOR, ".leftCont")
    children = left_cont.find_elements(By.XPATH, "./*")
    for i, child in enumerate(children):
        tag = child.tag_name
        classes = child.get_attribute("class")
        print(f"{i}. <{tag} class='{classes}'>")
        if i > 20: break
        
    driver.quit()

if __name__ == "__main__":
    inspect_dom()
