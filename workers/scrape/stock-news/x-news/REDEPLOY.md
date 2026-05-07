# Scraper Deployment & Maintenance Guide

## 1. Transferring Telegram Session
Since the Telegram scraper uses a local session file, you must transfer it to the EC2 instance to avoid logging in again.

From your local machine:
```bash
scp tg_session.session ubuntu@your-ec2-ip:/home/ubuntu/sentimatix/workers/scrape/stock-news/x-news/
```

## 2. Running the Scrapers
The `orchestrator.py` is the entry point. It automatically chunks the 2,200+ stocks and runs them in parallel.

To run manually:
```bash
docker compose run scraper python orchestrator.py
```

## 3. Automation (Cron)
To run the scrapers automatically every day at 1:00 AM, add a cron job on the EC2 host:

```bash
crontab -e
```

Add this line:
```cron
0 1 * * * cd /home/ubuntu/sentimatix/workers/scrape/stock-news/x-news && /usr/bin/docker compose run scraper python orchestrator.py >> /home/ubuntu/logs/cron_scrape.log 2>&1
```

## 4. Monitoring Logs
Check the orchestrator logs and individual scraper logs in the `logs/` directory:
```bash
tail -f logs/orchestrator.log
```
