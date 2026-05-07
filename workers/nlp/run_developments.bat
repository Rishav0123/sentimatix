@echo off
REM Hourly Stock Developments Processor
REM Run this with Windows Task Scheduler every hour

cd /d "%~dp0"
python process_developments.py >> logs\developments_%date:~-4,4%%date:~-10,2%%date:~-7,2%.log 2>&1
