# This script uses Selenium to scrape news headlines from Moneycontrol for a given company.

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent / 'utilities'))
from store_news_article import store_news_article
from get_active_stocks import get_active_stocks
from datetime import datetime, UTC
import time
import logging
from pathlib import Path


# MoneyControl base URL
BASE_URL = "https://www.moneycontrol.com/company-article"

# Updated function to scrape specific news headlines, timestamps, and descriptions
# Function to store news in Supabase

def scrape_moneycontrol_news_selenium(company_name: str, symbol: str):
    url = f"{BASE_URL}/{company_name}/news/{symbol}"

    # Set up Selenium WebDriver
    chrome_options = Options()
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    try:
        driver.get(url)
        WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".MT15.PT10.PB10")))

        headlines = []
        articles = driver.find_elements(By.CSS_SELECTOR, ".MT15.PT10.PB10")
        for article in articles:
            article_url = None
            for elem in article.find_elements(By.XPATH, './/*'):
                if elem.tag_name == "a":
                    href = elem.get_attribute("href")
                    if href:
                        article_url = href
            try:
                title = article.find_element(By.CSS_SELECTOR, "a.g_14bl strong").text.strip()
                # Get all <p> tags in the article
                p_tags = article.find_elements(By.TAG_NAME, "p")
                timestamp = p_tags[0].text.strip() if len(p_tags) > 0 else ""
                # Use the second <p> tag as the content/summary if available
                content = p_tags[1].text.strip() if len(p_tags) > 1 else ""
                headlines.append({
                    "title": title,
                    "timestamp": timestamp,
                    "description": content,
                    "url": article_url
                })
            except Exception:
                continue

        return headlines

    except Exception as e:
        print(f"Failed to fetch news for {symbol}: {e}")
        return []

    finally:
        driver.quit()


# Example usage
if __name__ == "__main__":
    # Setup logging to logs/moneycontrol_{date}.log
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / f"moneycontrol_{datetime.now().strftime('%Y%m%d')}.log"
    # Use UTF-8 encoding for StreamHandler to avoid UnicodeEncodeError
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    stream_handler = logging.StreamHandler()
    try:
        stream_handler.stream.reconfigure(encoding='utf-8')
    except Exception:
        pass  # For Python <3.7 or if reconfigure not available
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            file_handler,
            stream_handler
        ]
    )
    logger = logging.getLogger(__name__)
    # Fetch active stocks from database
    stocks = get_active_stocks()
    if not stocks:
        logger.info("No active stocks found in database")
        exit(1)
    logger.info(f"Found {len(stocks)} active stocks to process")
    for stock in stocks:
        id = stock['id']
        mc_link_1 = stock['mc_link_1']
        yfin_symbol = stock['yfin_symbol']
        mc_link_2 = stock['mc_link_2'].lower().replace(' ', '').replace('.', '')
        logger.info(f"\nProcessing {mc_link_1} ({mc_link_2})...")
        headlines = scrape_moneycontrol_news_selenium(mc_link_2, mc_link_1)
        # Print all found headlines for debugging
        logger.info(f"All headlines for {mc_link_1}:")
        for h in headlines:
            logger.info(f"  Title: {h['title']} | Timestamp: {h['timestamp']}")
        if headlines:
            logger.info(f"Found {len(headlines)} news articles")
            stored_count = 0
            skipped_count = 0
            for news in headlines:
                timestamp_str = news['timestamp']
                full_datetime = None
                try:
                    time_part, date_part = timestamp_str.split(' | ')
                    time_12h = time_part.lower()
                    if 'pm' in time_12h and not time_12h.startswith('12'):
                        hour = int(time_12h.split('.')[0]) + 12
                        minute = int(time_12h.split('.')[1].split()[0])
                        time_24h = f"{hour:02d}:{minute:02d}"
                    elif 'am' in time_12h and time_12h.startswith('12'):
                        minute = int(time_12h.split('.')[1].split()[0])
                        time_24h = f"00:{minute:02d}"
                    else:
                        hour = int(time_12h.split('.')[0])
                        minute = int(time_12h.split('.')[1].split()[0])
                        time_24h = f"{hour:02d}:{minute:02d}"
                    date_obj = datetime.strptime(date_part, "%d %b %Y")
                    full_datetime = f"{date_obj.strftime('%Y-%m-%d')}T{time_24h}:00+00:00"
                except Exception as e:
                    logger.error(f"Error parsing timestamp for article '{news['title']}' with raw timestamp '{timestamp_str}': {e}")
                    # Fallback: use current time as published_at
                    full_datetime = datetime.now(UTC).isoformat()
                try:
                    news_data = {
                        "id": id,
                        "title": news['title'],
                        "content": news['description'],
                        "url": news['url'],
                        "source": "moneycontrol",
                        "yfin_symbol": yfin_symbol,
                        "published_at": full_datetime,
                        "scraped_at": datetime.now(UTC).isoformat(),
                        "tags": [stock['mc_link_2'], "news"],
                        "sentiment": None,
                        "published_date": (datetime.fromisoformat(full_datetime).date().isoformat() if 'T' in full_datetime else datetime.now(UTC).date().isoformat())
                    }
                    logger.debug(news_data)
                    if store_news_article(news_data):
                        stored_count += 1
                    else:
                        skipped_count += 1
                except Exception as e:
                    logger.error(f"Error inserting article '{news['title']}': {e}")
            logger.info(f"Stored {stored_count} new articles, skipped {skipped_count} existing articles")
        else:
            logger.info(f"No news found for {mc_link_1}.")
        time.sleep(5)