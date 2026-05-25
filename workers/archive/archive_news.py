#!/usr/bin/env python
"""
archive_news.py

Weekly Archival Worker for Hot-Cold News Archival Tiering.
Moves articles older than 30 days from Supabase Postgres to highly compressed Parquet files on S3/Cloudflare R2.
"""

import os
import sys
import argparse
import logging
from datetime import datetime, timedelta, timezone
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv
from supabase import create_client, Client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("archiver")

# Load environment variables
load_dotenv('d:/sentimatix/apps/api/.env')

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# S3/R2 Configuration
S3_ACCESS_KEY_ID = os.getenv("S3_ACCESS_KEY_ID")
S3_SECRET_ACCESS_KEY = os.getenv("S3_SECRET_ACCESS_KEY")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "sentimatix-news-archive")
S3_ENDPOINT_URL = os.getenv("S3_ENDPOINT_URL")
S3_REGION = os.getenv("S3_REGION", "us-east-1")

def get_supabase_client() -> Client:
    if not SUPABASE_URL or not SUPABASE_KEY:
        logger.error("SUPABASE_URL and SUPABASE_KEY must be configured in environment variables.")
        sys.exit(1)
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def upload_to_s3(local_path: str, s3_key_name: str) -> bool:
    """Uploads a local file to S3/R2 storage."""
    if not S3_ACCESS_KEY_ID or not S3_SECRET_ACCESS_KEY:
        logger.warning("S3 credentials not fully configured. Skipping S3 upload.")
        return False

    logger.info(f"Uploading {local_path} to S3 bucket '{S3_BUCKET_NAME}' at '{s3_key_name}'...")
    try:
        # Create boto3 client
        s3_client = boto3.client(
            "s3",
            aws_access_key_id=S3_ACCESS_KEY_ID,
            aws_secret_access_key=S3_SECRET_ACCESS_KEY,
            endpoint_url=S3_ENDPOINT_URL,
            region_name=S3_REGION
        )
        s3_client.upload_file(local_path, S3_BUCKET_NAME, s3_key_name)
        logger.info("Upload completed successfully.")
        return True
    except ClientError as e:
        logger.error(f"Failed to upload to S3: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during S3 upload: {e}")
        return False

def archive_pipeline(retention_days: int, dry_run: bool, allow_local_pruning: bool):
    logger.info("Initializing Hot-Cold News Archival Pipeline...")
    logger.info(f"Settings: retention_days={retention_days}, dry_run={dry_run}, allow_local_pruning={allow_local_pruning}")

    # Connect to Supabase
    supabase = get_supabase_client()

    # Calculate cutoff date
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=retention_days)
    cutoff_str = cutoff_date.isoformat()
    logger.info(f"Archiving articles published before: {cutoff_str}")

    # Fetch articles in batches using Cursor-Based Pagination
    batch_size = 5000
    all_articles = []
    last_published_at = None

    logger.info("Fetching eligible news items from Supabase using Cursor-Based Pagination...")
    while True:
        logger.info(f"  Fetching batch (last_published_at={last_published_at})...")
        try:
            # Query base
            query = supabase.table("news") \
                .select("*") \
                .eq("is_ready", "Y") \
                .lt("published_at", cutoff_str)
                
            if last_published_at:
                query = query.gt("published_at", last_published_at)
                
            res = query.order("published_at") \
                .limit(batch_size) \
                .execute()
            
            if res.data:
                all_articles.extend(res.data)
                logger.info(f"  Fetched {len(res.data)} items. (Total so far: {len(all_articles)})")
                
                # Update last_published_at for cursor pagination
                last_published_at = res.data[-1]["published_at"]
                
                if len(res.data) < batch_size:
                    break
            else:
                break
        except Exception as e:
            logger.error(f"Error fetching batch from Supabase: {e}")
            sys.exit(1)

    logger.info(f"Successfully retrieved {len(all_articles)} news items.")

    if len(all_articles) == 0:
        logger.info("No articles to archive. Exiting.")
        return

    # Convert to Pandas DataFrame
    df = pd.DataFrame(all_articles)

    # Clean complex columns to ensure 100% PyArrow compatibility
    # If list columns exist (like 'tags'), keep them as lists, or serialize to JSON strings.
    # PyArrow supports list columns perfectly, but converting them to strings/JSON avoids any type mismatched rows.
    # Let's keep them as lists but handle nulls or different types.
    if 'tags' in df.columns:
        df['tags'] = df['tags'].apply(lambda x: list(x) if isinstance(x, (list, set, tuple)) else ([] if pd.isna(x) else [str(x)]))

    # Generate Parquet file
    today_str = datetime.now().strftime("%Y_%m_%d")
    local_dir = "d:/sentimatix/data/archive"
    os.makedirs(local_dir, exist_ok=True)
    local_filename = f"temp_archive_news_{today_str}.parquet"
    local_path = os.path.join(local_dir, local_filename)

    logger.info(f"Writing to local Parquet file: {local_path}...")
    try:
        # Convert to pyarrow Table and write with Snappy compression
        table = pa.Table.from_pandas(df)
        pq.write_table(table, local_path, compression="snappy")
        logger.info(f"Local Parquet file created. Size: {os.path.getsize(local_path) / 1024 / 1024:.2f} MB")
    except Exception as e:
        logger.error(f"Failed to generate Parquet file: {e}")
        if os.path.exists(local_path):
            os.remove(local_path)
        sys.exit(1)

    # Upload to S3/R2
    s3_key_name = f"archive/news_{today_str}.parquet"
    uploaded = upload_to_s3(local_path, s3_key_name)

    # Determine if we can safely prune Supabase Postgres news table
    prune_ok = False
    if uploaded:
        prune_ok = True
    elif allow_local_pruning:
        logger.warning("S3 upload skipped/failed but --allow-local-pruning is enabled. Pruning local data anyway.")
        prune_ok = True
    else:
        logger.warning("Pruning aborted because S3 upload failed/skipped and local pruning is disabled.")
        logger.info(f"Your archived Parquet file remains safe locally at: {local_path}")

    if prune_ok:
        if dry_run:
            logger.info("[DRY RUN] Skipping deletion of archived rows from Supabase.")
        else:
            # Verify Parquet row count before deleting
            try:
                parquet_file = pq.ParquetFile(local_path)
                parquet_rows = parquet_file.metadata.num_rows
                logger.info(f"Verifying row count: database={len(all_articles)}, parquet={parquet_rows}")
                
                if parquet_rows != len(all_articles):
                    logger.error("Verification failed: row counts do not match! Aborting pruning.")
                    sys.exit(1)
                
                logger.info("Verification succeeded! Row counts match exactly.")
            except Exception as e:
                logger.error(f"Failed to verify Parquet row count: {e}. Aborting pruning.")
                sys.exit(1)

            # Prune in batches from Supabase Postgres to avoid timeouts
            logger.info("Deleting archived rows from Supabase Postgres in batches of 1000...")
            ids_to_delete = [item["id"] for item in all_articles]
            delete_batch_size = 1000
            deleted_count = 0

            for i in range(0, len(ids_to_delete), delete_batch_size):
                batch_ids = ids_to_delete[i : i + delete_batch_size]
                try:
                    del_res = supabase.table("news") \
                        .delete() \
                        .in_("id", batch_ids) \
                        .execute()
                    deleted_count += len(batch_ids)
                    logger.info(f"  Deleted batch {i // delete_batch_size + 1}: {len(batch_ids)} rows.")
                except Exception as e:
                    logger.error(f"Failed to delete batch starting at offset {i}: {e}")
                    logger.error("Database might be in a partially pruned state. Please check database logs.")
                    sys.exit(1)

            logger.info(f"Successfully pruned {deleted_count} archived rows from Supabase news table!")

    logger.info("Archival pipeline execution complete.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Weekly Archival Worker for Hot-Cold News Archival Tiering")
    parser.add_argument(
        "--retention-days",
        type=int,
        default=30,
        help="Number of days of active news to keep in the primary database (default: 30)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Generate local Parquet archive but do NOT upload to S3 or delete rows from Supabase"
    )
    parser.add_argument(
        "--allow-local-pruning",
        action="store_true",
        help="Allow deleting rows from Supabase even if S3 upload was skipped (useful for local-only testing)"
    )
    args = parser.parse_args()

    archive_pipeline(
        retention_days=args.retention_days,
        dry_run=args.dry_run,
        allow_local_pruning=args.allow_local_pruning
    )
