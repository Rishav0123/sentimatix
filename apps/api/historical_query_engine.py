"""
historical_query_engine.py

Historical Query Engine for Cold Tier news retrieval using DuckDB.
Queries snappy-compressed Parquet files directly from S3/R2 or falls back to a local archive directory.
"""

import os
import logging
import duckdb
from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime

logger = logging.getLogger("historical_query_engine")

# S3/R2 Configuration
S3_ACCESS_KEY_ID = os.getenv("S3_ACCESS_KEY_ID")
S3_SECRET_ACCESS_KEY = os.getenv("S3_SECRET_ACCESS_KEY")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "sentimatix-news-archive")
S3_ENDPOINT_URL = os.getenv("S3_ENDPOINT_URL")
S3_REGION = os.getenv("S3_REGION", "us-east-1")

class HistoricalQueryEngine:
    def __init__(self):
        self.local_dir = "d:/sentimatix/data/archive"
        self._initialized = False
        self.con = None

    def _setup_connection(self):
        """Initializes DuckDB and configures S3/R2 if credentials are provided."""
        if self._initialized and self.con:
            return

        try:
            self.con = duckdb.connect(database=":memory:")
            self.con.execute("INSTALL httpfs;")
            self.con.execute("LOAD httpfs;")

            # Configure S3 compatible storage (e.g. Cloudflare R2 / AWS S3)
            if S3_ACCESS_KEY_ID and S3_SECRET_ACCESS_KEY:
                logger.info("Configuring DuckDB S3/R2 credentials...")
                self.con.execute(f"SET s3_access_key_id='{S3_ACCESS_KEY_ID}';")
                self.con.execute(f"SET s3_secret_access_key='{S3_SECRET_ACCESS_KEY}';")
                
                if S3_ENDPOINT_URL:
                    # DuckDB expects endpoint without protocol
                    endpoint_clean = S3_ENDPOINT_URL.replace("https://", "").replace("http://", "")
                    self.con.execute(f"SET s3_endpoint='{endpoint_clean}';")
                    self.con.execute("SET s3_use_ssl=true;")
                
                if S3_REGION:
                    self.con.execute(f"SET s3_region='{S3_REGION}';")
            else:
                logger.info("S3 credentials not found. DuckDB will run in local-only fallback mode.")

            self._initialized = True
        except Exception as e:
            logger.error(f"Failed to initialize DuckDB connection: {e}")
            raise e

    def _get_archive_path(self) -> Tuple[str, bool]:
        """
        Returns the Parquet path and a boolean indicating whether it is an S3 path.
        Checks for local parquet files if S3 is not configured.
        """
        if S3_ACCESS_KEY_ID and S3_SECRET_ACCESS_KEY:
            return f"s3://{S3_BUCKET_NAME}/archive/*.parquet", True

        # Local fallback check
        if os.path.exists(self.local_dir):
            parquet_files = [f for f in os.listdir(self.local_dir) if f.endswith(".parquet")]
            if parquet_files:
                return os.path.join(self.local_dir, "*.parquet").replace("\\", "/"), False

        return "", False

    def query_historical_news(
        self,
        symbols: Optional[List[str]] = None,
        sentiment: Optional[str] = None,
        published_after: Optional[str] = None,
        published_before: Optional[str] = None,
        only_market_sensitive: bool = False,
        limit: int = 10,
        offset: int = 0
    ) -> Tuple[int, List[Dict[str, Any]]]:
        """
        Queries historical Parquet cold tier data using DuckDB.
        Returns a tuple of (total_matching_count, list_of_records).
        """
        try:
            self._setup_connection()
        except Exception:
            return 0, []

        archive_path, is_s3 = self._get_archive_path()
        if not archive_path:
            logger.info("No historical archives found locally or S3 not configured. Returning empty.")
            return 0, []

        # Build SQL dynamic filters
        filters = ["is_ready = 'Y'"]
        params = []

        if symbols:
            # SQL IN clause
            placeholders = ", ".join([f"'{sym}'" for sym in symbols])
            filters.append(f"yfin_symbol IN ({placeholders})")

        if sentiment:
            filters.append("sentiment = ?")
            params.append(sentiment.lower())

        if published_after:
            filters.append("published_at >= ?")
            params.append(f"{published_after}T00:00:00Z")

        if published_before:
            filters.append("published_at <= ?")
            params.append(f"{published_before}T23:59:59Z")

        if only_market_sensitive:
            filters.append("is_volatile = true")

        filter_clause = " AND ".join(filters)
        
        # Build counting query and data query
        count_sql = f"SELECT COUNT(*) FROM read_parquet('{archive_path}') WHERE {filter_clause};"
        query_sql = f"""
            SELECT 
                id, title, content, url, source, published_at, 
                sentiment, sentiment_score, confidence, is_volatile, yfin_symbol, stock_name
            FROM read_parquet('{archive_path}') 
            WHERE {filter_clause}
            ORDER BY published_at DESC
            LIMIT ? OFFSET ?;
        """

        try:
            # 1. Get Count
            count_res = self.con.execute(count_sql, params).fetchone()
            total_count = count_res[0] if count_res else 0
            
            if total_count == 0:
                return 0, []

            # 2. Get Records
            query_params = params + [limit, offset]
            df = self.con.execute(query_sql, query_params).fetchdf()
            
            # Convert NaN to None for JSON serialization
            df = df.where(df.notnull(), None)
            
            # Map fields to match database format
            records = []
            for _, row in df.iterrows():
                records.append({
                    "id": row["id"],
                    "title": row["title"],
                    "content": row["content"],
                    "url": row["url"],
                    "source": row["source"],
                    "published_at": row["published_at"],
                    "sentiment": row["sentiment"],
                    "sentiment_score": float(row["sentiment_score"]) if row["sentiment_score"] is not None else None,
                    "confidence": float(row["confidence"]) if row["confidence"] is not None else None,
                    "is_volatile": bool(row["is_volatile"]) if row["is_volatile"] is not None else None,
                    "yfin_symbol": row["yfin_symbol"],
                    "stock_name": row["stock_name"],
                    "is_ready": "Y"
                })
            
            return total_count, records

        except Exception as e:
            logger.error(f"Error querying cold tier via DuckDB: {e}")
            return 0, []

# Singleton instance
historical_engine = HistoricalQueryEngine()
