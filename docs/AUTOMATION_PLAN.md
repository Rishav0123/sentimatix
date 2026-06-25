# Automation Guide - Sentiment Updates & Weekly News Archival

This document outlines the architecture, setup procedures, and code templates for automating the two core recurring background processes in Sentimatix:

1. **Sentiment Moving Averages Update** (Daily): Recalculating 7-day and 30-day sentiment averages for stocks in `update_sentiment_moving_avg.py`.
2. **Weekly News Archival & Pruning** (Weekly): Moving articles older than 60 days to compressed Snappy Parquet files on Cloudflare R2 and pruning the transactional Supabase database via `archive_news.py`.

---

## 1. High-Level Automation Blueprint

```
                     ┌────────────────────────┐
                     │   Sentimatix Backend   │
                     └────────────────────────┘
                      /                      \
                     /                        \
      [Process A: Daily]                     [Process B: Weekly]
             |                                       |
    Sentiment Averages                       News Archival Pipeline
             |                                       |
  ┌──────────────────────┐               ┌────────────────────────┐
  │ Option 1 (Preferred) │               │  Option A (Preferred)  │
  │ Supabase pg_cron     │               │  GitHub Actions Runner │
  │ - $0 Server Cost     │               │  - Clean sandboxed run │
  │ - Sub-ms DB latency  │               │  - Free secure environment│
  └──────────────────────┘               └────────────────────────┘
             |                                       |
  ┌──────────────────────┐               ┌────────────────────────┐
  │ Option 2 (Python)    │               │  Option B (Railway)    │
  │ GitHub Actions Cron  │               │  Railway Cron Service  │
  │ - Daily Python run   │               │  - Internal cron worker│
  └──────────────────────┘               └────────────────────────┘
```

---

## 2. Sentiment Moving Averages Automation (Daily)

This process updates the `sentiment_7d` and `sentiment_30d` fields on active stocks in the `stocks` table using sentiment scores from the `news` table.

### Option A: Supabase Natively via `pg_cron` (Recommended)
Since the script `scripts/update_sentiment_moving_avg.py` runs a single, highly-optimized SQL query, we can bypass python entirely and execute it natively inside the Postgres engine. This has zero latency, zero server costs, and zero environment vulnerabilities.

#### Setup Instructions:
1. Go to your **Supabase Dashboard** -> **Database** -> **Extensions**.
2. Enable the **`pg_cron`** extension.
3. Open the **SQL Editor** in Supabase and run the following command to schedule the daily task at 12:00 AM UTC:

```sql
-- Enable pg_cron if not already enabled
CREATE EXTENSION IF NOT EXISTS pg_cron;

-- Schedule the sentiment moving averages update daily at 12:00 AM UTC
SELECT cron.schedule(
    'update-sentiment-moving-averages', -- Unique Job Name
    '0 0 * * *',                         -- Cron Schedule (Daily at Midnight UTC)
    $$
    UPDATE public.stocks s
    SET
        sentiment_7d          = sub.avg_7d,
        sentiment_30d         = sub.avg_30d,
        sentiment_updated_at  = NOW(),
        updated_at            = NOW()
    FROM (
        SELECT
            stock_id,
            ROUND(
                AVG(sentiment_score) FILTER (
                    WHERE published_at >= NOW() - INTERVAL '7 days'
                      AND sentiment_score IS NOT NULL
                )::numeric, 4
            ) AS avg_7d,
            ROUND(
                AVG(sentiment_score) FILTER (
                    WHERE published_at >= NOW() - INTERVAL '30 days'
                      AND sentiment_score IS NOT NULL
                )::numeric, 4
            ) AS avg_30d
        FROM public.news
        WHERE stock_id IS NOT NULL
        GROUP BY stock_id
    ) sub
    WHERE s.id = sub.stock_id
      AND s.is_active = TRUE;
    $$
);
```

#### Monitoring `pg_cron` Jobs:
You can check if the job is running successfully by querying the logs inside your Supabase SQL Editor:
```sql
-- View all scheduled jobs
SELECT * FROM cron.job;

-- View execution logs and history
SELECT * FROM cron.job_run_details ORDER BY start_time DESC LIMIT 50;
```

---

## 3. Weekly News Archival & Pruning Automation (Weekly)

The archival process fetches historical news older than 60 days, compresses it into snappy-compressed Parquet files, uploads them to Cloudflare R2, and safely prunes those rows from Supabase. Because this script utilizes `pandas`, `pyarrow`, and `boto3`, it **must** run in a Python runtime environment.

### Option A: GitHub Actions (Recommended)
GitHub Actions provides reliable, completely free runner instances with built-in storage to write the temporary `.parquet` files before uploading to R2.

#### Setup Instructions:
1. In your GitHub Repository, go to **Settings** -> **Secrets and variables** -> **Actions** -> **New repository secret**.
2. Add the following secrets from your production API `.env` file:
   * `SUPABASE_URL`
   * `SUPABASE_KEY`
   * `S3_ACCESS_KEY_ID`
   * `S3_SECRET_ACCESS_KEY`
   * `S3_ENDPOINT_URL`
   * `S3_BUCKET_NAME`
   * `S3_REGION`

3. Create the folder `.github/workflows/` at the root of your repository (if it doesn't already exist).
4. Create the workflow file `archive_news.yml` inside it:

```yaml
# .github/workflows/archive_news.yml
name: Weekly News Archival & Database Pruning

on:
  schedule:
    # Runs every Sunday at 01:00 AM UTC
    - cron: '0 1 * * 0'
  workflow_dispatch: # Allows manual trigger from the GitHub UI

jobs:
  archive-news:
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout Repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install pandas pyarrow supabase boto3 python-dotenv psycopg2-binary

      - name: Run Archival Pipeline
        env:
          SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
          SUPABASE_KEY: ${{ secrets.SUPABASE_KEY }}
          S3_ACCESS_KEY_ID: ${{ secrets.S3_ACCESS_KEY_ID }}
          S3_SECRET_ACCESS_KEY: ${{ secrets.S3_SECRET_ACCESS_KEY }}
          S3_BUCKET_NAME: ${{ secrets.S3_BUCKET_NAME }}
          S3_ENDPOINT_URL: ${{ secrets.S3_ENDPOINT_URL }}
          S3_REGION: ${{ secrets.S3_REGION }}
        run: |
          # Create temporary data/archive directory in runner
          mkdir -p d:/sentimatix/data/archive
          # Execute the archive script (retaining last 60 days of news in primary Postgres)
          python workers/archive/archive_news.py --retention-days 60
```

---

### Option B: Railway Cron Service
If you want to keep everything running under the same ecosystem as your FastAPI backend, you can provision a separate lightweight worker instance in your Railway project to execute scheduled commands.

#### Setup Instructions:
1. Click **+ New** in your Railway dashboard -> **GitHub Repo** (select Sentimatix).
2. Go to the service **Settings**.
3. Under **Deploy**, find the **Cron Schedule** field and enter:
   `0 1 * * 0` (Cron for running every Sunday at 1:00 AM UTC).
4. Set the **Start Command** to execute the pipeline:
   ```bash
   pip install -r requirements.txt && python workers/archive/archive_news.py --retention-days 60
   ```
5. Ensure all necessary S3, Cloudflare, and Supabase variables are shared or linked into this service variables settings.

---

### Option C: Administrative API Endpoints (Alternative Trigger)
If you prefer triggering these scripts via external cron triggers (like Better Stack, Cron-Job.org, or standard webhooks), you can expose them as secure, authenticated API endpoints inside your FastAPI router.

Add this securely to your API router structure:

```python
# apps/api/routers/admin.py
from fastapi import APIRouter, Header, HTTPException, BackgroundTasks
import subprocess
import os

router = APIRouter(prefix="/admin", tags=["admin"])

@router.post("/trigger-archival")
def trigger_archival(
    background_tasks: BackgroundTasks,
    x_admin_token: str = Header(None)
):
    # Verify the incoming token with INTERNAL_SERVICE_KEY from your .env
    if x_admin_token != os.getenv("INTERNAL_SERVICE_KEY"):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # Run in a background thread to prevent HTTP request timeouts
    def run_archiver():
        subprocess.run(["python", "workers/archive/archive_news.py", "--retention-days", "60"])
        
    background_tasks.add_task(run_archiver)
    return {"status": "Archival process triggered in background."}
```

Triggering it via a remote web cron service is simple:
```bash
curl -X POST https://your-railway-api.up.railway.app/admin/trigger-archival \
  -H "x-admin-token: YOUR_INTERNAL_SERVICE_KEY"
```

---

## 4. Local Automation via Windows Task Scheduler (Testing & Local Development)

If you are running the system on a local Windows machine, you can schedule executing the scripts directly using your local Python virtual environment (`d:\sentimatix\venv`).

### Step 1: Create PowerShell Runners
Create helper execution files to invoke the virtual environment and run the scripts:

#### For Sentiment Updates (`d:\sentimatix\run_sentiment_updater.ps1`):
```powershell
cd d:\sentimatix
.\venv\Scripts\python.exe scripts/update_sentiment_moving_avg.py >> logs/sentiment_cron.log 2>&1
```

#### For Archival Pipeline (`d:\sentimatix\run_archiver.ps1`):
```powershell
cd d:\sentimatix
.\venv\Scripts\python.exe workers/archive/archive_news.py --retention-days 60 >> logs/archival_cron.log 2>&1
```

### Step 2: Schedule Tasks in Windows
1. Search and open **Task Scheduler** in the Windows Start Menu.
2. Click **Create Basic Task** on the right panel.
3. Name your task (e.g., `Sentimatix Weekly Archival`).
4. Set the trigger to **Weekly** -> select **Sunday** -> select your desired execution time (e.g., 2:00 AM).
5. Set Action to **Start a program**.
6. Set:
   * **Program/script**: `powershell.exe`
   * **Add arguments**: `-ExecutionPolicy Bypass -File d:\sentimatix\run_archiver.ps1`
7. Click Finish.
8. Repeat the same setup for the daily sentiment updater script with a daily trigger.
