import os
import logging
from datetime import datetime
from pathlib import Path
from supabase import create_client
from transformers import pipeline
import asyncio

# Configure logging
def setup_logging():
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / f"sentiment_local_{datetime.now().strftime('%Y%m%d')}.log"
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__), log_file

logger, log_file = setup_logging()
logger.info(f"Starting local sentiment analysis, logging to {log_file}")

# Supabase configuration
SUPABASE_URL = os.environ.get("SUPABASE_URL") or "https://uqvouptulubydignwtkv.supabase.co"
SUPABASE_KEY = os.environ.get("SUPABASE_KEY") or "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVxdm91cHR1bHVieWRpZ253dGt2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTk5MzQ1MTUsImV4cCI6MjA3NTUxMDUxNX0.0PtQ_9FVKzFL6pTVOHFoEZbTk5477-RyeH_XR2B12m8"

class LocalSentimentAnalyzer:
    def __init__(self):
        self.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        self.sentiment = pipeline(
            "sentiment-analysis",
            model="ProsusAI/finbert"
        )

    def analyze(self, text):
        # Truncate to 256 chars for model compatibility
        res = self.sentiment(text[:256])[0]
        label = res['label'].lower()
        # Map to positive/negative/neutral
        if label == 'positive':
            sentiment = 'positive'
            score = round(res['score'], 2)
        elif label == 'negative':
            sentiment = 'negative'
            score = -round(res['score'], 2)
        else:
            sentiment = 'neutral'
            score = 0.0
        return {"sentiment": sentiment, "sentiment_score": score}

    async def get_unanalyzed_news(self):
        try:
            response = await asyncio.to_thread(
                lambda: self.supabase.table("news")
                .select("*")
                .or_("sentiment.is.null,sentiment_score.is.null")
                .execute()
            )
            print("found total analyzed news articles" + str(len(response.data) if response.data else 0))
            return response.data if response.data is not None else []
        except Exception as e:
            logger.error(f"Error fetching news: {str(e)}")
            return []

    async def update_news(self, news_id, enrichment):
        try:
            await asyncio.to_thread(
                lambda: self.supabase.table("news")
                .update({
                    "sentiment": enrichment["sentiment"],
                    "sentiment_score": enrichment["sentiment_score"]
                })
                .eq("id", news_id)
                .execute()
            )
            logger.info(f"Updated news ID {news_id} with {enrichment}")
        except Exception as e:
            logger.error(f"Error updating news ID {news_id}: {str(e)}")

async def main():
    analyzer = LocalSentimentAnalyzer()
    news_articles = await analyzer.get_unanalyzed_news()
    logger.info(f"Found {len(news_articles)} unanalyzed news articles")
    for article in news_articles:
        content = (article.get('content') or '') + ' ' + (article.get('title') or '')
        enrichment = analyzer.analyze(content)
        logger.info(f"News ID {article['id']} enrichment: {enrichment}")
        print(f"Title: {article.get('title', '').strip()}\nSentiment: {enrichment['sentiment']} | Score: {enrichment['sentiment_score']}\n")
        await analyzer.update_news(article['id'], enrichment)

if __name__ == "__main__":
    asyncio.run(main())
