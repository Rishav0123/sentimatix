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

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.handlers.clear()

# File handler: logs everything to file (INFO and above)
file_handler = logging.FileHandler(log_dir / "orchestrator.log", encoding="utf-8")
file_handler.setLevel(logging.INFO)
file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)

# Console handler: logs only WARNING and above to console (prevents info logs from disrupting progress bar)
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.WARNING)
console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

def console_info(msg):
    """Prints message to stdout and records it to the logger info stream."""
    print(msg)
    logger.info(msg)

def draw_progress_bar(current, total, bar_length=30, prefix="", status=""):
    """Draws a beautiful progress bar in the console with percentage and stats."""
    percent = float(current) / total
    filled_length = int(round(bar_length * percent))
    bar = '█' * filled_length + '░' * (bar_length - filled_length)
    
    # Progress text formatting
    progress_str = f"\r{prefix} [{bar}] {percent * 100:.1f}% ({current}/{total}) | {status}"
    
    # Pad to clean old line content completely
    sys.stdout.write(progress_str.ljust(120))
    sys.stdout.flush()

def extract_batch_stats(metrics):
    """Extracts running counts of inserted and skipped articles from batch metrics."""
    inserted = 0
    skipped = 0
    if not metrics:
        return inserted, skipped
    for val in metrics.values():
        if isinstance(val, str):
            try:
                if "inserted:" in val:
                    inserted += int(val.split("inserted:")[1].split()[0])
                if "skipped:" in val:
                    skipped += int(val.split("skipped:")[1].split()[0])
            except:
                pass
        elif isinstance(val, int):
            inserted += val
    return inserted, skipped


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
        
        # Force UTF-8 environment settings for the spawned scraper process
        env = os.environ.copy()
        env["PYTHONUTF8"] = "1"
        env["PYTHONIOENCODING"] = "utf-8"

        process = subprocess.Popen(
            [sys.executable, script_path, '--stocks-json', temp_file.name, '--run-id', run_id],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            errors='replace',
            env=env
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
        console_info("Warming up Chrome driver...")
        ChromeDriverManager().install()
        console_info("Chrome driver warmup complete.")
    except Exception as e:
        logger.error(f"Failed to warmup Chrome driver: {e}")

def main():
    print(f"\n[DEBUG] Starting Parallel Orchestrator...")
    print(f"[DEBUG] Script path: {__file__}")
    print(f"[DEBUG] Current working directory: {os.getcwd()}")
    console_info("Starting Parallel Orchestrator...")
    
    # 1. Warm up resources
    warmup_chrome_driver()
    
    # 2. Fetch all active stocks
    all_stocks = get_active_stocks()
    if not all_stocks:
        logger.error("No active stocks found. Exiting.")
        return
    
    console_info(f"Total stocks to process: {len(all_stocks)}")
    
    run_id = str(uuid.uuid4())
    console_info(f"Current Run ID: {run_id}")

    # 2. Parallelize Google News
    print(f"\n[DEBUG] Entering Google News block. all_stocks length: {len(all_stocks)}")
    try:
        gnews_batches = list(chunk_list(all_stocks, 5))
        total_gnews_batches = len(gnews_batches)
        print(f"[DEBUG] Google News batches: {total_gnews_batches}")
        console_info(f"Running Google News in {total_gnews_batches} batches...")
        
        gnews_metrics = {}
        gnews_inserted = 0
        gnews_skipped = 0
        completed_gnews_batches = 0
        
        if gnews_batches:
            # Render starting state of GNews progress bar
            draw_progress_bar(0, total_gnews_batches, prefix="GNews Progress:", status="Starting...")
            
            with ProcessPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(run_scraper_batch, 'scrape_gnews.py', batch, run_id) for batch in gnews_batches]
                for future in as_completed(futures):
                    try:
                        res = future.result()
                        logger.info(res['message'])
                        
                        if res['metrics']:
                            for sym, val in res['metrics'].items():
                                gnews_metrics[sym] = val
                            
                            # Extract and add stats
                            ins, skp = extract_batch_stats(res['metrics'])
                            gnews_inserted += ins
                            gnews_skipped += skp
                        
                        completed_gnews_batches += 1
                        draw_progress_bar(
                            completed_gnews_batches,
                            total_gnews_batches,
                            prefix="GNews Progress:",
                            status=f"Inserted: {gnews_inserted} | Skipped: {gnews_skipped}"
                        )
                    except Exception as fe:
                        sys.stdout.write("\n")
                        print(f"[DEBUG] Future result error in GNews: {fe}")
            print() # End the progress bar line
        
        log_scraper_report('gnews', run_id, gnews_metrics)
    except Exception as ge:
        print(f"[DEBUG] CRITICAL ERROR in Google News block: {ge}")
        import traceback
        traceback.print_exc()

    # 3. Parallelize MoneyControl
    console_info("MoneyControl scraping is skipped.")

    # 4. Telegram (Single Fetch Optimization)
    print(f"\n[DEBUG] Entering Telegram block.")
    try:
        console_info(f"Running Telegram for all {len(all_stocks)} stocks in a single pass...")
        
        tg_metrics = {}
        res = run_scraper_batch('scrape_tg_bot.py', all_stocks, run_id)
        logger.info(res['message'])
        if res['metrics']:
            tg_metrics = res['metrics']
            tg_inserted, tg_skipped = extract_batch_stats(tg_metrics)
            console_info(f"Telegram Done | Inserted: {tg_inserted} | Skipped: {tg_skipped}")
                        
        log_scraper_report('tg', run_id, tg_metrics)
    except Exception as te:
        print(f"[DEBUG] CRITICAL ERROR in Telegram block: {te}")
        import traceback
        traceback.print_exc()

    console_info("Orchestration complete.")

if __name__ == "__main__":
    main()
