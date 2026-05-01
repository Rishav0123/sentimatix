# Sentimatix EC2 Deployment Guide

This guide explains how to migrate your local scrapers and NLP engine to a dedicated Ubuntu EC2 instance (or any VPS like DigitalOcean). This ensures your scrapers run 24/7, handles Selenium headless browsing seamlessly, and keeps your Telegram sessions alive without losing state.

## 1. Provision the Server

1. **Launch an Instance**:
   - Provider: AWS EC2 (or DigitalOcean, Linode, etc.)
   - OS: **Ubuntu 24.04 LTS** (or 22.04 LTS)
   - Size: `t3.small` (AWS) or a $6-$12/mo Droplet. You need at least 2GB of RAM for Selenium/Playwright and FinBERT to run comfortably.
   - Storage: 20GB General Purpose SSD.
2. **Assign an Elastic IP**: This prevents the IP from changing when you restart the server, which is good for whitelist rules or avoiding IP-reputation issues.
3. **Open Ports**: Open Port 22 (SSH). You do not need HTTP/HTTPS ports open for the scraper worker.

## 2. Connect and Upload Code

1. Connect to your instance via SSH:
   ```bash
   ssh -i your-key.pem ubuntu@YOUR_EC2_IP
   ```
2. Upload your entire `sentimatix` directory from your local machine to the EC2 instance using SCP (or SFTP via FileZilla, or push/pull from GitHub).
   ```bash
   # From your local machine:
   scp -i your-key.pem -r d:\sentimatix ubuntu@YOUR_EC2_IP:~/sentimatix
   ```
   **CRITICAL**: Ensure the `tg_session.session` file and your `.env` files are uploaded!

## 3. Run the Setup Script

Once the code is on the server, SSH in and run the automated setup script. This will install Python, Google Chrome, Playwright, and all required packages.

```bash
cd ~/sentimatix
chmod +x setup_ec2.sh
./setup_ec2.sh
```

## 4. Test the Pipeline

Before automating, run the master pipeline script manually to verify Chrome, Telegram, and Supabase connections are working.

```bash
# Activate the virtual environment
source ~/sentimatix_env/bin/activate

# Run the master pipeline
python run_pipeline.py
```

Watch the output. It should sequentially run:
1. Web Scrapers
2. Sentiment Analyzer
3. Momentum Updater

## 5. Automate with Cron

Set up a Cron job to run the pipeline automatically on a schedule (e.g., every day at 6:00 PM UTC).

1. Open the crontab editor:
   ```bash
   crontab -e
   ```
2. Add the following line to the bottom of the file (adjust the time as needed):
   ```bash
   # Run daily at 18:00 (6:00 PM) UTC
   0 18 * * * /home/ubuntu/sentimatix_env/bin/python /home/ubuntu/sentimatix/run_pipeline.py >> /home/ubuntu/sentimatix/pipeline.log 2>&1
   ```

## Troubleshooting

- **Telegram Asks for Phone Number**: This means your `tg_session.session` file was not uploaded to the server or is in the wrong directory.
- **Selenium/Playwright Errors**: If it complains about a missing browser, run `playwright install chromium` inside the active virtual environment.
- **Out of Memory (OOM)**: If the script is killed silently during the NLP step, FinBERT might be using too much RAM. Consider upgrading the instance to a `t3.medium` or adding a swapfile (`sudo fallocate -l 2G /swapfile && sudo chmod 600 /swapfile && sudo mkswap /swapfile && sudo swapon /swapfile`).
