import subprocess
import json
import os
import logging
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from datetime import datetime
from utilities.get_active_stocks import get_active_stocks
import sys
import tempfile
from dotenv import load_dotenv

load_dotenv()

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

import uuid
from supabase import create_client

def run_scraper_batch(script_name, stocks_batch, run_id):
    """
    Runs a specific scraper script for a batch of stocks.
    We pass the stocks as a JSON string to the script.
    """
    # Create a temporary file to pass the stocks JSON
    temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
    stdout = ""
    stderr = ""
    try:
        script_path = os.path.join('scrapers', script_name)
        with open(temp_file.name, 'w') as f:
            json.dump(stocks_batch, f)
        
        process = subprocess.Popen(
            [sys.executable, script_path, '--stocks-json', temp_file.name, '--run-id', run_id],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = process.communicate()
        
        metrics = {}
        if "METRICS: " in stdout:
            try:
                metrics_str = stdout.split("METRICS: ")[1].split("\n")[0]
                metrics = json.loads(metrics_str)
            except Exception as e:
                logger.error(f"Error parsing metrics from {script_name}: {e}")

        if process.returncode == 0:
            return {
                "status": "success",
                "message": f"Successfully ran {script_name} for batch of {len(stocks_batch)} stocks.",
                "metrics": metrics
            }
        else:
            return {
                "status": "error",
                "message": f"Error running {script_name}: {stderr}",
                "metrics": {}
            }
    except Exception as e:
        return {
            "status": "exception",
            "message": f"Exception in batch: {str(e)}",
            "metrics": {}
        }
    finally:
        if os.path.exists(temp_file.name):
            try:
                os.remove(temp_file.name)
            except:
                pass

def log_scraper_report(scraper_name, run_id, metrics):
    """Logs the aggregated metrics to the database."""
    try:
        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_KEY')
        supabase = create_client(url, key)
        
        total_inserted = 0
        for val in metrics.values():
            if isinstance(val, str) and "inserted:" in val:
                try:
                    # Extract X from "inserted:X skipped:Y"
                    count = int(val.split("inserted:")[1].split()[0])
                    total_inserted += count
                except:
                    pass
            elif isinstance(val, int):
                total_inserted += val
        
        supabase.table('scraper_reports').insert({
            'scraper_name': scraper_name,
            'run_id': run_id,
            'total_inserted': total_inserted,
            'stock_counts': metrics
        }).execute()
        
        logger.info(f"Logged report for {scraper_name}: {total_inserted} total articles.")
    except Exception as e:
        logger.error(f"Failed to log scraper report: {e}")

def chunk_list(data, chunk_size):
    for i in range(0, len(data), chunk_size):
        yield data[i:i + chunk_size]

def warmup_chrome_driver():
    """Ensures the Chrome driver is installed once before parallel workers start."""
    try:
        # Import inside function to avoid dependency issues if not using Selenium scrapers
        from webdriver_manager.chrome import ChromeDriverManager
        logger.info("Warming up Chrome driver...")
        ChromeDriverManager().install()
        logger.info("Chrome driver warmup complete.")
    except Exception as e:
        logger.error(f"Failed to warmup Chrome driver: {e}")

def main():
    print(f"\n[DEBUG] Starting Parallel Orchestrator...")
    print(f"[DEBUG] Script path: {__file__}")
    print(f"[DEBUG] Current working directory: {os.getcwd()}")
    logger.info("Starting Parallel Orchestrator...")
    
    # 1. Warm up resources
    warmup_chrome_driver()
    
    # 2. Fetch all active stocks
    all_stocks = get_active_stocks()
    if not all_stocks:
        logger.error("No active stocks found. Exiting.")
        return
    
    logger.info(f"Total stocks to process: {len(all_stocks)}")
    
    run_id = str(uuid.uuid4())
    logger.info(f"Current Run ID: {run_id}")

    # 2. Parallelize Google News
    print(f"\n[DEBUG] Entering Google News block. all_stocks length: {len(all_stocks)}")
    try:
        gnews_batches = list(chunk_list(all_stocks, 5))
        print(f"[DEBUG] Google News batches: {len(gnews_batches)}")
        logger.info(f"Running Google News in {len(gnews_batches)} batches...")
        
        gnews_metrics = {}
        if gnews_batches:
            with ProcessPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(run_scraper_batch, 'scrape_gnews.py', batch, run_id) for batch in gnews_batches]
                for future in as_completed(futures):
                    try:
                        res = future.result()
                        logger.info(res['message'])
                        if res['metrics']:
                            for sym, val in res['metrics'].items():
                                # Store the metric string/value for each symbol
                                gnews_metrics[sym] = val
                    except Exception as fe:
                        print(f"[DEBUG] Future result error in GNews: {fe}")
        
        log_scraper_report('gnews', run_id, gnews_metrics)
    except Exception as ge:
        print(f"[DEBUG] CRITICAL ERROR in Google News block: {ge}")
        import traceback
        traceback.print_exc()

    # 3. Parallelize MoneyControl
    print(f"\n[DEBUG] Entering MoneyControl block.")
    try:
        mc_batches = list(chunk_list(all_stocks, 5))
        print(f"[DEBUG] MoneyControl batches: {len(mc_batches)}")
        logger.info(f"Running MoneyControl in {len(mc_batches)} batches (5 stocks each)...")
    
        mc_metrics = {}
        with ProcessPoolExecutor(max_workers=8) as executor:
            futures = [executor.submit(run_scraper_batch, 'scrape_moneycontrol.py', batch, run_id) for batch in mc_batches]
            for future in as_completed(futures):
                res = future.result()
                logger.info(res['message'])
                if res['metrics']:
                    for sym, val in res['metrics'].items():
                        # If it's the new string format, we overwrite (since we shouldn't have duplicate symbols across batches anyway)
                        mc_metrics[sym] = val
                        
        log_scraper_report('moneycontrol', run_id, mc_metrics)
    except Exception as me:
        print(f"[DEBUG] CRITICAL ERROR in MoneyControl block: {me}")
        import traceback
        traceback.print_exc()

    # 4. Telegram (Single Fetch Optimization)
    print(f"\n[DEBUG] Entering Telegram block.")
    try:
        logger.info(f"Running Telegram for all {len(all_stocks)} stocks in a single pass...")
        
        tg_metrics = {}
        res = run_scraper_batch('scrape_tg_bot.py', all_stocks, run_id)
        logger.info(res['message'])
        if res['metrics']:
            tg_metrics = res['metrics']
                        
        log_scraper_report('tg', run_id, tg_metrics)
    except Exception as te:
        print(f"[DEBUG] CRITICAL ERROR in Telegram block: {te}")
        import traceback
        traceback.print_exc()

    logger.info("Orchestration complete.")

if __name__ == "__main__":
    main()
