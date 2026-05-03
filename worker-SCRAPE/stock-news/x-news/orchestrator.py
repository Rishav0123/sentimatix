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
    try:
        script_path = os.path.join('scrapers', script_name)
        json.dump(stocks_batch, temp_file)
        temp_file.close()
        
        process = subprocess.Popen(
            [sys.executable, script_path, '--stocks-json', temp_file.name, '--run-id', run_id],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = process.communicate()
    finally:
        if os.path.exists(temp_file.name):
            os.remove(temp_file.name)
        
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

def log_scraper_report(scraper_name, run_id, metrics):
    """Logs the aggregated metrics to the database."""
    try:
        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_KEY')
        supabase = create_client(url, key)
        
        total_inserted = sum(metrics.values())
        
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

def main():
    logger.info("Starting Parallel Orchestrator...")
    
    # 1. Fetch all active stocks
    all_stocks = get_active_stocks()
    if not all_stocks:
        logger.error("No active stocks found. Exiting.")
        return
    
    logger.info(f"Total stocks to process: {len(all_stocks)}")
    
    run_id = str(uuid.uuid4())
    logger.info(f"Current Run ID: {run_id}")

    # 2. Parallelize Google News
    gnews_batches = list(chunk_list(all_stocks, 50))
    logger.info(f"Running Google News in {len(gnews_batches)} batches...")
    
    gnews_metrics = {}
    with ProcessPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(run_scraper_batch, 'scrape_gnews.py', batch, run_id) for batch in gnews_batches]
        for future in as_completed(futures):
            res = future.result()
            logger.info(res['message'])
            if res['metrics']:
                for sym, count in res['metrics'].items():
                    gnews_metrics[sym] = gnews_metrics.get(sym, 0) + count
    
    log_scraper_report('gnews', run_id, gnews_metrics)

    # 3. Parallelize MoneyControl
    mc_batches = list(chunk_list(all_stocks, 20))
    logger.info(f"Running MoneyControl in {len(mc_batches)} batches...")
    
    mc_metrics = {}
    with ProcessPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(run_scraper_batch, 'scrape_moneycontrol.py', batch, run_id) for batch in mc_batches]
        for future in as_completed(futures):
            res = future.result()
            logger.info(res['message'])
            if res['metrics']:
                for sym, count in res['metrics'].items():
                    mc_metrics[sym] = mc_metrics.get(sym, 0) + count
                    
    log_scraper_report('moneycontrol', run_id, mc_metrics)

    logger.info("Orchestration complete.")

if __name__ == "__main__":
    main()
