# This script uses Selenium to scrape news headlines from Moneycontrol for a given company.

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import sys
import os
from pathlib import Path
# Add the root directory to sys.path
sys.path.append(str(Path(__file__).parent.parent))
from utilities.store_news_article import store_news_article
from utilities.get_active_stocks import get_active_stocks
from datetime import datetime, timezone
import time
import logging
from pathlib import Path
import argparse
import json

from scrapers.agent_scrapers import enhanced_keyword_matching

# MoneyControl base URL
BASE_URL = "https://www.moneycontrol.com/company-article"

# Updated function to scrape specific news headlines, timestamps, and descriptions
# Function to store news in Supabase

def scrape_moneycontrol_news_selenium(company_name: str, symbol: str, stock_name: str = "", keywords: list = None):
    url = f"{BASE_URL}/{company_name}/news/{symbol}"

    # Set up Selenium WebDriver with optimized flags for headless Linux
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--blink-settings=imagesEnabled=false")
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    try:
        driver.get(url)
        
        # Check if we were redirected to the homepage or a generic news page
        # A valid stock news URL must contain "company-article"
        current_url = driver.current_url
        if "company-article" not in current_url:
            print(f"Redirected away from company-article to {current_url}. Skipping to avoid generic news.")
            return [], True

        # Validation: Detect generic template fallback pages
        # MoneyControl often serves a "Latest News" page with an empty placeholder in the title if the company is not found.
        page_title = driver.title
        if "on ," in page_title and ", Results News" in page_title:
            print(f"Detected generic news fallback (empty title placeholder) for {company_name}. Skipping.")
            return [], True
            
        # Verify if the slug or stock name is present in the title
        title_norm = page_title.lower().replace(' ', '')
        slug_match = company_name.lower() in title_norm or symbol.lower() in title_norm
        
        # If we have a stock name, check for it as well
        name_match = True
        if stock_name:
            name_parts = [p.lower() for p in stock_name.split() if len(p) > 2]
            name_match = any(part in page_title.lower() for part in name_parts)
            
        if not slug_match and not name_match:
            print(f"Page title '{page_title}' does not seem to match company '{stock_name or company_name}'. Skipping to avoid junk news.")
            return [], True

        # Wait for the main news links to appear
        WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a.g_14bl")))
 
        headlines = []
        # Find all headline links
        headline_links = driver.find_elements(By.CSS_SELECTOR, "a.g_14bl")
        
        for link in headline_links:
            try:
                # The container is usually a parent of the link
                # We need to find the specific MT15.PT10.PB10 wrapper
                article = link.find_element(By.XPATH, "./ancestor::div[contains(@class, 'MT15')]")
                
                article_url = link.get_attribute("href")
                if not article_url or "moneycontrol.com" not in article_url:
                    continue
                    
                # Skip generic non-financial paths (double safety)
                GENERIC_PATHS = [
                    '/entertainment/', '/sports/', '/world/', '/education/', 
                    '/news/trends/', '/news/india/', '/news/politics/', '/opinion/'
                ]
                if any(path in article_url.lower() for path in GENERIC_PATHS):
                    continue

                title = link.text.strip()
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

        # Filter headlines based on keywords if provided
        filtered_headlines = []
        if keywords:
            # Always ensure the stock name is in the keywords for fallback
            if stock_name and stock_name not in keywords:
                keywords.append(stock_name)
                
            for h in headlines:
                combined_text = f"{h['title']} {h['description']}"
                is_match, _ = enhanced_keyword_matching(combined_text, keywords)
                if is_match:
                    filtered_headlines.append(h)
                else:
                    # Also try basic financial relevance just in case, but require the stock name match
                    # Since these are aggregator pages, we MUST ensure the title or description mentions the stock
                    name_parts = [p.lower() for p in (stock_name or company_name).split() if len(p) > 2]
                    if any(part in combined_text.lower() for part in name_parts):
                        filtered_headlines.append(h)
        else:
            filtered_headlines = headlines

        return filtered_headlines, False

    except Exception as e:
        print(f"Failed to fetch news for {symbol}: {e}")
        return [], False

    finally:
        driver.quit()


# Example usage
if __name__ == "__main__":
    # Setup logging with a unique name if run-id is provided to avoid permission issues in parallel batches
    parser = argparse.ArgumentParser(description="Scrape MoneyControl news")
    parser.add_argument("--stocks-json", type=str, help="JSON string of stocks to process")
    parser.add_argument("--run-id", type=str, help="Run ID for tracking")
    args = parser.parse_args()

    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Unique log file for this batch (using PID to avoid conflicts in parallel)
    batch_suffix = f"_{args.run_id[:8]}" if args.run_id else ""
    pid_suffix = f"_pid{os.getpid()}"
    log_file = log_dir / f"moneycontrol_{datetime.now().strftime('%Y%m%d')}{batch_suffix}{pid_suffix}.log"
    
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    stream_handler = logging.StreamHandler()
    try:
        stream_handler.stream.reconfigure(encoding='utf-8')
    except Exception:
        pass
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            file_handler,
            stream_handler
        ]
    )
    logger = logging.getLogger(__name__)

    if args.stocks_json:
        if os.path.exists(args.stocks_json):
            with open(args.stocks_json, 'r') as f:
                stocks = json.load(f)
        else:
            stocks = json.loads(args.stocks_json)
        logger.info(f"Processing {len(stocks)} stocks from command line")
    else:
        stocks = get_active_stocks()
        if not stocks:
            logger.info("No active stocks found in database")
            exit(1)
        logger.info(f"Found {len(stocks)} active stocks to process")

    overall_report = {}
    for stock in stocks:
        id = stock['id']
        yfin_symbol = stock['yfin_symbol']

        # Guard against stocks with missing MC links (would crash silently before any log output)
        if not stock.get('mc_link_1') or not stock.get('mc_link_2'):
            logger.warning(f"⚠️ Skipping {yfin_symbol}: mc_link_1 or mc_link_2 is NULL in DB")
            overall_report[yfin_symbol] = "generic"
            continue

        # Clean both links to ensure they are URL-safe (lowercase, no spaces)
        link_a = stock['mc_link_1'].lower().replace(' ', '').replace('.', '')
        link_b = stock['mc_link_2'].lower().replace(' ', '').replace('.', '')
        
        # Moneycontrol URL format is: /company-article/<long_company_name>/news/<short_symbol_id>
        # Because the database has inconsistent parameter ordering (sometimes link_1 is the name, sometimes the symbol),
        # we can reliably determine which is which by length. The company name is always the longer string.
        if len(link_a) > len(link_b):
            company_name = link_a
            symbol = link_b
        else:
            company_name = link_b
            symbol = link_a
            
        # Extract keywords
        keywords = []
        if stock.get('keyword_lst'):
            try:
                kw_obj = json.loads(stock['keyword_lst']) if isinstance(stock['keyword_lst'], str) else stock['keyword_lst']
                if isinstance(kw_obj, dict) and 'keyword' in kw_obj:
                    keywords = kw_obj['keyword']
                elif isinstance(kw_obj, list):
                    keywords = kw_obj
            except Exception as e:
                logger.error(f"Error parsing keywords for {id}: {e}")
                
                
        logger.info(f"\nProcessing {company_name} ({symbol}) for {yfin_symbol}...")
        headlines, is_generic = scrape_moneycontrol_news_selenium(company_name, symbol, stock.get('stock_name', ''), keywords)
        
        if is_generic:
            logger.info(f"Marking {yfin_symbol} as generic news.")
            overall_report[yfin_symbol] = "generic"
            continue

        # Print all found headlines for debugging
        logger.info(f"All headlines for {company_name}:")
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
                    # Handle extra parts like " | Source: Moneycontrol.com"
                    parts = timestamp_str.split(' | ')
                    time_part = parts[0]
                    date_part = parts[1]
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
                    full_datetime = datetime.now(timezone.utc).isoformat()
                    
                # Date Filtering: Discard anything older than 15 days
                try:
                    from datetime import timedelta
                    article_date = datetime.fromisoformat(full_datetime).date()
                    if article_date < (datetime.now(timezone.utc).date() - timedelta(days=15)):
                        logger.info(f"⏭️ Skipping old news ({article_date}): {news['title'][:50]}...")
                        skipped_count += 1
                        continue
                except Exception as de:
                    logger.error(f"Error filtering Moneycontrol news by date: {de}")
                    
                try:
                    news_data = {
                        "stock_id": id,
                        "title": news['title'],
                        "content": news['description'],
                        "url": news['url'],
                        "source": "moneycontrol",
                        "yfin_symbol": yfin_symbol,
                        "stock_name": stock.get('stock_name', ''),
                        "published_at": full_datetime,
                        "scraped_at": datetime.now(timezone.utc).isoformat(),
                        "tags": [stock['mc_link_2'], "news"],
                        "sentiment": None,
                        "published_date": (datetime.fromisoformat(full_datetime).date().isoformat() if 'T' in full_datetime else datetime.now(timezone.utc).date().isoformat())
                    }
                    logger.debug(news_data)
                    if store_news_article(news_data):
                        stored_count += 1
                    else:
                        skipped_count += 1
                except Exception as e:
                    logger.error(f"Error inserting article '{news['title']}': {e}")
            logger.info(f"Stored {stored_count} new articles, skipped {skipped_count} existing articles")
            overall_report[yfin_symbol] = f"inserted:{stored_count} skipped:{skipped_count}"
        else:
            logger.info(f"No news found for {company_name}.")
            overall_report[yfin_symbol] = "inserted:0 skipped:0"
        time.sleep(5)
    
    # Output metrics for the orchestrator to capture
    print(f"\nMETRICS: {json.dumps(overall_report)}")