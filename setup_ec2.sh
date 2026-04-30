#!/bin/bash
# ==============================================================================
# Sentimatix EC2 Environment Setup Script (Ubuntu 24.04 / 22.04 LTS)
# ==============================================================================
# Run this script on a fresh EC2 instance to install all dependencies for
# Selenium, Playwright, Python, and the Scraper/NLP workers.
# ==============================================================================

set -e

echo "=== Updating System Packages ==="
sudo apt update && sudo apt upgrade -y

echo "=== Installing Python and Essentials ==="
sudo apt install -y python3-pip python3-venv wget curl git unzip xvfb libxi6 libgconf-2-4

echo "=== Installing Google Chrome (for Selenium/Playwright) ==="
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo apt install -y ./google-chrome-stable_current_amd64.deb
rm google-chrome-stable_current_amd64.deb

echo "=== Setting up Python Virtual Environment ==="
python3 -m venv ~/sentimatix_env
source ~/sentimatix_env/bin/activate

echo "=== Installing Python Dependencies ==="
# Install core dependencies (ensure requirements.txt exists in the project root or adjust path)
pip install --upgrade pip
pip install selenium webdriver_manager supabase requests beautifulsoup4 pandas python-dotenv feedparser python-dateutil psycopg2-binary
pip install torch transformers sentence-transformers
pip install playwright
playwright install firefox chromium
playwright install-deps

echo "======================================================================"
echo "Setup Complete!"
echo "Next Steps:"
echo "1. Upload your code to ~/sentimatix"
echo "2. Upload your .env and tg_session.session files"
echo "3. Run: crontab -e to schedule the pipeline"
echo "======================================================================"
