@echo off
cd /d %~dp0
python fetch_prices.py > price_fetcher_log_%date:~-4,4%%date:~-10,2%%date:~-7,2%.txt 2>&1