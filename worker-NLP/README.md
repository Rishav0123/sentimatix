# Sentiment Analysis Script

This folder contains a Python script for performing sentiment analysis on news articles and updating a Supabase table with the results.

## Features
- Analyzes sentiment of news articles using NLP techniques
- Updates the `news` table in Supabase with two columns:
  - `sentiment`: The detected sentiment (e.g., positive, negative, neutral)
  - `sentiment_score`: The numerical score representing sentiment strength
- Designed to run locally as a cron job every hour

## Usage
1. **Install dependencies**
   - Run `pip install -r requirements.txt` in the `nlp` directory.
2. **Configure Supabase credentials**
   - Ensure your Supabase API keys and connection details are set in the script or environment variables.
3. **Set up the cron job**
   - Schedule the script (`analyze_sentiment.py`) to run every hour using your system's task scheduler or cron.

## Folder Structure
- `analyze_sentiment.py`: Main script for sentiment analysis and database update
- `requirements.txt`: Python dependencies
- `logs/`: Log files and output

## Example Cron Job (Windows)
You can use Task Scheduler to run the script every hour. For Linux/Mac, add a line to your crontab:
```
0 * * * * python /path/to/nlp/analyze_sentiment.py
```

## License
MIT
