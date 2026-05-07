@echo off
REM Sentiment Update Scheduler for Windows
REM Run this batch file every hour via Windows Task Scheduler

cd /d "D:\sentimatix"
python scripts/sentiment_updater.py

REM Log the execution
echo %date% %time% - Sentiment update completed >> sentiment_update.log