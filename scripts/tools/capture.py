from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto('http://localhost:8501/?theme=dark')
    time.sleep(5)
    
    # Wait for the sidebar password input to be available
    page.wait_for_selector('input[type="password"]')
    page.fill('input[type="password"]', '686b700d-9c97-4c41-ae2a-52755f2abaf1')
    page.keyboard.press('Enter')
    time.sleep(10) # wait for data to load
    
    page.screenshot(path='d:\\sentimatix\\docs\\sentimatix_demo.png', full_page=True)
    browser.close()
