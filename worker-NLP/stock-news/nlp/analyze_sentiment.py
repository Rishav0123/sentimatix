from keybert import KeyBERT
import logging
from supabase import create_client
import openai
import json
# Load OpenAI API key from environment variable
import os
openai.api_key = os.getenv("OPENAI_API_KEY")
import asyncio

# Create logs directory if it doesn't exist
import os
from datetime import datetime
from pathlib import Path

log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

# Set up logging to both file and console
log_file = log_dir / f"sentiment_analyzer_{datetime.now().strftime('%Y%m%d')}.log"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),  # Log to file
        logging.StreamHandler()         # Log to console
    ]
)
logger = logging.getLogger(__name__)

logger.info(f"Starting sentiment analysis, logging to {log_file}")

# Supabase configuration
SUPABASE_URL = "https://uqvouptulubydignwtkv.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVxdm91cHR1bHVieWRpZ253dGt2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTk5MzQ1MTUsImV4cCI6MjA3NTUxMDUxNX0.0PtQ_9FVKzFL6pTVOHFoEZbTk5477-RyeH_XR2B12m8"


class SentimentAnalyzer:
    def __init__(self):
        """Initialize the analyzer with Supabase client and KeyBERT model"""
        self.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        self.keyword_model = KeyBERT()

    def enrich_batch_with_llm(self, articles: list) -> list:
        """
    Use OpenAI LLM to analyze a batch of news articles for sentiment, using only extracted keywords.
    Expects articles as a list of dicts with 'id' and 'keywords'.
    Returns a list of dicts with id, sentiment, and sentiment_score.
        """
        prompt = (
            "You are a financial news analyst. For each news article below, you are given a set of keywords extracted from the article. "
            "Based only on these keywords, return a JSON object with keys: id, sentiment (positive/negative/neutral), "
            "and sentiment_score (between -1 and 1, 1 decimal). Return a JSON array of results.\n\n"
        )
        for article in articles:
            keywords_str = ', '.join(article.get('keywords', []))
            prompt += f"ID: {article['id']}\nKeywords: {keywords_str}\n\n"
        prompt += (
            "Respond in this format:\n"
            "[\n"
            "  {\"id\": \"1\", \"sentiment\": \"positive\", \"sentiment_score\": 0.8},\n"
            "  ...\n"
            "]"
        )
        print(prompt)
        try:
            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=2048
            )
            result = json.loads(response.choices[0].message.content)
            print(result)
            return result
        except Exception as e:
            logger.error(f"OpenAI batch enrichment error: {str(e)}")
            # Return neutral for all in case of error
            return [
                {
                    "id": article['id'],
                    "sentiment": "neutral",
                    "sentiment_score": 0.0
                } for article in articles
            ]

    async def get_unanalyzed_news(self) -> list:
        """Get news articles that haven't been analyzed yet (no sentiment or no score), and extract keywords using KeyBERT."""
        try:
            response = await asyncio.to_thread(
                lambda: self.supabase.table("news")
                .select("*")
                .or_("sentiment.is.null,sentiment_score.is.null")  # Get articles missing either value
                .execute()
            )
            news_list = response.data if response.data is not None else []
            print(news_list)
            # Extract keywords for each article
            results = []
            for article in news_list:
                content = (article.get('content') or '') + ' ' + (article.get('title') or '')
                keywords = self.keyword_model.extract_keywords(content, keyphrase_ngram_range=(1, 3), stop_words='english', top_n=10)
                keywords = [kw for kw, _ in keywords]
                results.append({
                    'id': article['id'],
                    'keywords': keywords
                })
            return results
        except Exception as e:
            logger.error(f"Error fetching unanalyzed news: {str(e)}")
            return []



    async def update_news_enrichment(self, news_id: int, enrichment: dict):
        """Update the news article in the database with enrichment fields (no summary, no entities)"""
        try:
            await asyncio.to_thread(
                lambda: self.supabase.table("news")
                .update({
                    "sentiment": enrichment.get("sentiment"),
                    "sentiment_score": enrichment.get("sentiment_score")
                })
                .eq("id", news_id)
                .execute()
            )
            logger.info(f"Updated news ID {news_id} with LLM enrichment: {enrichment}")
        except Exception as e:
            logger.error(f"Error updating enrichment for news ID {news_id}: {str(e)}")


async def main():
    analyzer = SentimentAnalyzer()
    news_articles = await analyzer.get_unanalyzed_news()
    logger.info(f"Found {len(news_articles)} unanalyzed news articles")
    # Batch size for LLM API calls (adjust as needed to save credits)
    BATCH_SIZE = 25
    total = len(news_articles)
    for i in range(0, total, BATCH_SIZE):
        batch = news_articles[i:i+BATCH_SIZE]
        logger.info(f"Processing batch {i//BATCH_SIZE+1}: News IDs {[a['id'] for a in batch]}")
        enrichments = analyzer.enrich_batch_with_llm(batch)
        # Map enrichments by id for easy lookup
        enrichments_by_id = {e['id']: e for e in enrichments}
        for article in batch:
            enrichment = enrichments_by_id.get(article['id'], {
                "sentiment": "neutral",
                "sentiment_score": 0.0
            })
            print(f"News ID {article['id']} enrichment result: {enrichment}")
            await analyzer.update_news_enrichment(article['id'], enrichment)
        if i + BATCH_SIZE < total:
            import time
            logger.info(f"Processed {i+BATCH_SIZE} of {total} articles. Waiting 2 seconds before next batch...")
            time.sleep(2)


if __name__ == "__main__":
    asyncio.run(main())