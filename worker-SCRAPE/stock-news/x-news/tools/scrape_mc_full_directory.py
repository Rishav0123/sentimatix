import requests
from bs4 import BeautifulSoup
import json
import time
import string
import os

def scrape_all_letters():
    letters = list(string.ascii_uppercase) + ['others']
    master_directory = {}
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.moneycontrol.com/"
    }
    
    session = requests.Session()
    session.headers.update(headers)
    
    for letter in letters:
        url = f"https://www.moneycontrol.com/india/stockpricequote/{letter}"
        print(f"Scraping letter: {letter}...")
        
        try:
            response = session.get(url, timeout=30)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                links = soup.select("table.pcq_tbl a.bl_12")
                
                count = 0
                for link in links:
                    name = link.get_text().strip()
                    href = link.get('href')
                    if name and href:
                        master_directory[name] = href
                        count += 1
                
                print(f"  Successfully found {count} stocks.")
            else:
                print(f"  Failed with status {response.status_code}")
                
            time.sleep(1.5) # Be polite
        except Exception as e:
            print(f"  Error: {e}")
            
    # Save the master directory
    output_file = 'mc_master_mapping.json'
    with open(output_file, 'w') as f:
        json.dump(master_directory, f, indent=2)
    
    print(f"\nScraping complete! Total stocks found: {len(master_directory)}")
    print(f"Mapping saved to {output_file}")

if __name__ == "__main__":
    scrape_all_letters()
