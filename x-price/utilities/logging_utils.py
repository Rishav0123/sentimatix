"""
Logging utilities for the price fetching system
"""
import os
from pathlib import Path
from datetime import datetime, UTC

def setup_logging():
    """Create logs directory if it doesn't exist"""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    return log_dir

def log_message(message: str, log_type: str = "INFO"):
    """
    Log a message to the daily log file and console
    
    Args:
        message (str): Message to log
        log_type (str): Type of log message (INFO, ERROR, WARNING)
    """
    # Create logs directory if it doesn't exist
    log_dir = setup_logging()
    
    # Create log file with today's date
    log_file = log_dir / f"price_fetcher_log_{datetime.now(UTC).strftime('%Y%m%d')}.txt"
    
    # Format the log message
    timestamp = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")
    formatted_message = f"[{timestamp}] [{log_type}] {message}\n"
    
    # Write to log file
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(formatted_message)
    
    # Also print to console
    print(message)

def log_error(message: str):
    """Log an error message"""
    log_message(message, "ERROR")

def log_warning(message: str):
    """Log a warning message"""
    log_message(message, "WARNING")

def log_info(message: str):
    """Log an info message"""
    log_message(message, "INFO")

def log_success(message: str):
    """Log a success message"""
    log_message(message, "SUCCESS")