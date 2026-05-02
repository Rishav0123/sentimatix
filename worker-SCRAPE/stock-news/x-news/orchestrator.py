import subprocess
import json
import os
import logging
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from datetime import datetime
from utilities.get_active_stocks import get_active_stocks

# Configure logging
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / "orchestrator.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def run_scraper_batch(script_name, stocks_batch):
    """
    Runs a specific scraper script for a batch of stocks.
    We pass the stocks as a JSON string to the script.
    """
    try:
        # Scrapers are now in the scrapers/ directory
        script_path = os.path.join('scrapers', script_name)
        stocks_json = json.dumps(stocks_batch)
        process = subprocess.Popen(
            ['python', script_path, '--stocks-json', stocks_json],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = process.communicate()
        
        if process.returncode == 0:
            return f"Successfully ran {script_name} for batch of {len(stocks_batch)} stocks."
        else:
            return f"Error running {script_name}: {stderr}"
    except Exception as e:
        return f"Exception in batch: {str(e)}"

def chunk_list(data, chunk_size):
    for i in range(0, len(data), chunk_size):
        yield data[i:i + chunk_size]

def main():
    logger.info("Starting Parallel Orchestrator...")
    
    # 1. Fetch all active stocks
    all_stocks = get_active_stocks()
    if not all_stocks:
        logger.error("No active stocks found. Exiting.")
        return
    
    logger.info(f"Total stocks to process: {len(all_stocks)}")

    # 2. Parallelize Google News (Lightweight)
    # GNews is fast, we can use larger batches and more workers
    gnews_batches = list(chunk_list(all_stocks, 50))
    logger.info(f"Running Google News in {len(gnews_batches)} batches...")
    
    with ProcessPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(run_scraper_batch, 'scrape_gnews.py', batch) for batch in gnews_batches]
        for future in as_completed(futures):
            logger.info(future.result())

    # 3. Parallelize MoneyControl (Heavyweight)
    # Selenium is heavy, we use smaller batches and fewer workers
    mc_batches = list(chunk_list(all_stocks, 20))
    logger.info(f"Running MoneyControl in {len(mc_batches)} batches...")
    
    # Adjust max_workers based on RAM (e.g., 4-6 for t3.medium)
    with ProcessPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(run_scraper_batch, 'scrape_moneycontrol.py', batch) for batch in mc_batches]
        for future in as_completed(futures):
            logger.info(future.result())

    logger.info("Orchestration complete.")

if __name__ == "__main__":
    main()
