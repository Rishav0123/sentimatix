"""
Master Pipeline Runner for Sentimatix
=====================================
Executes the entire data pipeline sequentially:
1. Web Scrapers (GNews, MoneyControl, Telegram, X, etc.)
2. Sentiment Analyzer (FinBERT inference)
3. Momentum Updater (calculates rolling averages & alerts)

Designed to be run via a single cron job on the EC2 instance.
"""

import sys
import os
import subprocess
import time
from datetime import datetime

# Set up paths relative to this script's location
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCRAPER_SCRIPT = os.path.join(BASE_DIR, "worker-SCRAPE", "stock-news", "x-news", "agent_scrapers.py")
NLP_SCRIPT = os.path.join(BASE_DIR, "worker-NLP", "stock-news", "nlp", "analyze_sentiment_production.py")
MOMENTUM_SCRIPT = os.path.join(BASE_DIR, "worker-NLP", "update_momentum.py")

# Ensure UTF-8 output for logs
env = os.environ.copy()
env["PYTHONIOENCODING"] = "utf-8"

def log(msg):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}", flush=True)

def run_step(name, script_path, args=None):
    log(f"--- STARTING: {name} ---")
    start_time = time.time()
    
    cmd = [sys.executable, script_path]
    if args:
        cmd.extend(args)
        
    try:
        # Run process and stream output
        process = subprocess.Popen(
            cmd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            cwd=os.path.dirname(script_path)
        )
        
        for line in process.stdout:
            print(line, end="", flush=True)
            
        process.wait()
        
        elapsed = int(time.time() - start_time)
        if process.returncode == 0:
            log(f"--- SUCCESS: {name} (Took {elapsed}s) ---\n")
            return True
        else:
            log(f"--- FAILED: {name} (Exit code {process.returncode}) ---\n")
            return False
            
    except Exception as e:
        log(f"--- ERROR executing {name}: {e} ---\n")
        return False

def main():
    log("=========================================")
    log("SENTIMATIX DATA PIPELINE STARTED")
    log("=========================================")
    
    # Step 1: Run Scrapers
    # If agent_scrapers.py has a block that runs automatically, this works.
    # Otherwise you might need to call a specific runner script.
    # Assuming agent_scrapers.py has an if __name__ == "__main__": block
    run_step("Web Scrapers", SCRAPER_SCRIPT)
    
    # Step 2: Run Sentiment Analysis
    # The --production flag tells it to fetch NULL sentiment rows from Supabase
    run_step("Sentiment Analyzer", NLP_SCRIPT, args=["--production"])
    
    # Step 3: Run Momentum Updates
    run_step("Momentum Updater", MOMENTUM_SCRIPT)
    
    log("=========================================")
    log("SENTIMATIX DATA PIPELINE COMPLETED")
    log("=========================================")

if __name__ == "__main__":
    main()
