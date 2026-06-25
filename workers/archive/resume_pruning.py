#!/usr/bin/env python
"""
resume_pruning.py

Recovery script to resume a failed or interrupted news archival pruning process.
Uses the verified local Parquet archive file to safely resume deleting archived
rows from Supabase Postgres in optimal, network-safe batches.
"""

import os
import sys
import logging
import pandas as pd
from dotenv import load_dotenv
from supabase import create_client, Client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("pruning-recovery")

# Load environment variables
load_dotenv('d:/sentimatix/apps/api/.env')

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

def get_supabase_client() -> Client:
    if not SUPABASE_URL or not SUPABASE_KEY:
        logger.error("SUPABASE_URL and SUPABASE_KEY must be configured in environment variables.")
        sys.exit(1)
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def resume_pruning():
    local_path = "d:/sentimatix/data/archive/temp_archive_news_2026_05_26.parquet"
    
    if not os.path.exists(local_path):
        logger.error(f"Archived Parquet file not found at: {local_path}")
        logger.error("Cannot resume pruning without the source Parquet file.")
        sys.exit(1)
        
    logger.info(f"Loading archived news items from: {local_path}...")
    try:
        # Read Parquet file
        df = pd.read_parquet(local_path, columns=["id", "title"])
        archived_ids = df["id"].tolist()
        total_archived = len(archived_ids)
        logger.info(f"Successfully loaded {total_archived} archived IDs from local Parquet file.")
    except Exception as e:
        logger.error(f"Failed to read Parquet file: {e}")
        sys.exit(1)

    supabase = get_supabase_client()
    
    logger.info("Checking Supabase for remaining rows that need to be pruned...")
    
    # We will check existence of archived IDs in safe batches of 100
    check_batch_size = 100
    ids_to_prune = []
    
    for i in range(0, total_archived, check_batch_size):
        batch_ids = archived_ids[i : i + check_batch_size]
        logger.info(f"  Checking database status for offset {i} / {total_archived}...")
        try:
            res = supabase.table("news") \
                .select("id") \
                .in_("id", batch_ids) \
                .execute()
                
            if res.data:
                batch_existing_ids = [item["id"] for item in res.data]
                ids_to_prune.extend(batch_existing_ids)
                logger.info(f"    -> Found {len(batch_existing_ids)} / {len(batch_ids)} rows still present in Supabase.")
        except Exception as e:
            logger.error(f"Failed to query existence for batch starting at offset {i}: {e}")
            sys.exit(1)
            
    total_to_prune = len(ids_to_prune)
    logger.info(f"Verification complete. Out of {total_archived} archived items, {total_to_prune} are still in Supabase.")
    
    if total_to_prune == 0:
        logger.info("All archived items have already been pruned. No action needed!")
        return

    # Delete remaining rows in safe batches of 100 to avoid URL length limit / timeout issues
    delete_batch_size = 100
    deleted_count = 0
    
    logger.info(f"Pruning {total_to_prune} remaining rows from Supabase news table in batches of {delete_batch_size}...")
    
    for i in range(0, total_to_prune, delete_batch_size):
        batch_ids = ids_to_prune[i : i + delete_batch_size]
        try:
            supabase.table("news") \
                .delete() \
                .in_("id", batch_ids) \
                .execute()
            deleted_count += len(batch_ids)
            logger.info(f"  Deleted batch {i // delete_batch_size + 1} / {int(total_to_prune / delete_batch_size) + 1}: {len(batch_ids)} rows. (Progress: {deleted_count} / {total_to_prune})")
        except Exception as e:
            logger.error(f"Failed to delete batch starting at offset {i}: {e}")
            logger.error("Pruning halted. Please check network connectivity and rerun this recovery script.")
            sys.exit(1)
            
    logger.info(f"Successfully finished pruning recovery! Deleted all {deleted_count} remaining archived rows.")

if __name__ == "__main__":
    resume_pruning()
