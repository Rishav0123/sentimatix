# Implementation Plan - Hot-Cold News Archival Tiering (Supabase + DuckDB + S3)

This plan details the design and deployment of an archival pipeline to prevent performance degradation on your primary Supabase Postgres database. By limiting the live table to the most recent 30 days and offloading older articles into highly compressed **Parquet files on S3/Cloudflare R2**, we keep Supabase costs near zero and queries lightning-fast.

---

## 1. High-Level Architecture & Data Flow

```
[News Scrapers]
      │
      ▼
┌──────────────┐      Weekly Cron Job      ┌─────────────────────────────────┐
│   SUPABASE   │ ────────────────────────> │      S3 / Cloudflare R2         │
│  (Postgres)  │                           │   (Compressed Parquet Files)   │
│  [Hot Tier:  │ <──────────────────────── │       [Cold Tier: >30 Days]     │
│  0-30 Days]  │    Deletes Archived Rows  │  Format: news_YYYY_MM_DD.parquet│
└──────────────┘                           └─────────────────────────────────┘
      ▲                                                     ▲
      │                                                     │
      │ 1. Real-time Queries (<30 days)                     │ 2. Historical Queries (>30 days)
      │                                                     │    (HTTP Range Requests - Direct S3)
      └─────────────────────┐         ┌─────────────────────┘
                            │         │
                     ┌───────────────────┐
                     │    FastAPI API    │
                     │ (Railway Backend) │
                     │  [Imports DuckDB] │
                     └───────────────────┘
```

---

## 2. Technical Stack Requirements

*   **Primary Database**: Supabase Postgres (existing)
*   **Archival Storage**: S3-compatible bucket (e.g. AWS S3 or Cloudflare R2)
*   **Query Engine**: `duckdb` (embedded inside Python backend)
*   **Data Conversion**: `pandas`, `pyarrow` (optimized columnar processing library)
*   **Additional Python Packages**:
    ```text
    duckdb>=0.10.0
    pyarrow>=14.0.0
    pandas>=2.0.0
    boto3>=1.30.0  # For S3 uploads
    ```

---

## 3. Proposed Changes

### Component 1: Weekly Archival Worker

We will create a standalone script running as a scheduled worker (or local task/cron) to handle data offloading.

#### [NEW] [archive_news.py](file:///d:/sentimatix/workers/archive/archive_news.py)
*   **Purpose**: Run weekly to compress and move >30 days old articles.
*   **Logic**:
    1.  Calculates the boundary date: `cutoff_date = datetime.now() - timedelta(days=30)`.
    2.  Fetches articles older than the cutoff date in batches of 5,000 from Supabase Postgres.
    3.  If records exist, converts the batch to a PyArrow Table and writes it locally to a temporary compressed Parquet file:
        `temp_archive_news_YYYY_MM_DD.parquet` (columnar compression reduces file size by up to 80-90%).
    4.  Uploads the Parquet file to the S3 bucket path: `archive/news_YYYY_MM_DD.parquet`.
    5.  Once the upload is 100% verified, deletes those archived rows from the Supabase Postgres `news` table to reclaim space and shrink active database index sizes.
    6.  Sends a success report to the database logs.

---

### Component 2: Unified API Query Interface

We will update the backend routes to transparently routing standard vs historical news queries.

#### [NEW] [historical_query_engine.py](file:///d:/sentimatix/apps/api/historical_query_engine.py)
*   **Purpose**: Abstract DuckDB queries to S3.
*   **Logic**:
    1.  Exposes an analytical query interface using local in-process DuckDB.
    2.  Configures `duckdb` with the `httpfs` extension and S3 access keys.
    3.  Queries files directly from S3 using global wildcard paths:
        `read_parquet('s3://sentimatix-news-archive/archive/*.parquet')`
    4.  Processes aggregations, averages, and trend data over 1-year or multi-year windows instantly in memory.

#### [MODIFY] [v1_routes.py](file:///d:/sentimatix/apps/api/v1_routes.py)
*   **Purpose**: Combine primary database and historical storage data seamlessly.
*   **Logic**:
    *   For live feeds/news tickers (last 30 days): Direct database query to Supabase.
    *   For custom dashboard charts/historical analytics (e.g. 90-day, 1-year, or 5-year trends): Route queries to `historical_query_engine.py` (DuckDB + S3), merge results with the live 30-day Postgres stats, and return a single unified response.

---

## 4. Open Questions (User Feedback Required)

> [!IMPORTANT]
> Please review the following architectural decisions:

1.  **Which Cloud Provider for S3?**
    *   *(Recommended)* **Cloudflare R2**: Fully compatible with AWS S3 APIs but has **zero egress (download) fees**. Since DuckDB fetches byte ranges over the network, R2 is 100% free for access traffic, whereas AWS S3 will incur minor egress network fees.
    *   **AWS S3**: Traditional industry standard. Easy to set up if you already have an AWS account.
2.  **Retention Period (Active postgres days)**:
    *   Is **30 days** the right size for the primary transactional database? Keeping it to 30 days is extremely fast, but we can set it to 60 or 90 days if your live models require a longer active buffer.
3.  **Cron Scheduling Platform**:
    *   Where should the weekly archival worker run?
        *   Option A: A simple scheduled workflow inside your existing Railway container.
        *   Option B: A scheduled GitHub Action running once a week (highly reliable and free).

---

## 5. Verification & Safety Plan

*   **Dry Run Support**: The `archive_news.py` script will support a `--dry-run` flag which runs the export, saves the Parquet file locally for inspection, but does *not* upload it or delete rows from Supabase.
*   **Data Integrity Check**: The script will verify that the number of rows exported to the Parquet file matches exactly with the row count in Supabase before executing the `DELETE` statement.
*   **Automatic Rollover**: If an upload to S3 fails, the deletion step is skipped entirely to prevent any possible data loss.
