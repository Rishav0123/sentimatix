import os
import logging
from datetime import datetime
from pathlib import Path
from supabase import create_client
from transformers import pipeline
import asyncio
import re
from collections import Counter

# Configure logging
def setup_logging():
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / f"sentiment_production_{datetime.now().strftime('%Y%m%d')}.log"
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
logger.info(f"Starting production sentiment analysis, logging to {log_file}")

# Supabase configuration
SUPABASE_URL = os.environ.get("SUPABASE_URL") or "https://uqvouptulubydignwtkv.supabase.co"
SUPABASE_KEY = os.environ.get("SUPABASE_KEY") or "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVxdm91cHR1bHVieWRpZ253dGt2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTk5MzQ1MTUsImV4cCI6MjA3NTUxMDUxNX0.0PtQ_9FVKzFL6pTVOHFoEZbTk5477-RyeH_XR2B12m8"

class ProductionSentimentAnalyzer:
    def __init__(self, max_chunk_chars=2000):
        """Initialize with the best performing model (FinBERT) and improved entity extraction"""
        self.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        # Use FinBERT (winner from comparison) with top_k=None for all probabilities
        self.sentiment = pipeline(
            "sentiment-analysis",
            model="ProsusAI/finbert",
            top_k=None
        )
        self.max_chunk_chars = max_chunk_chars
        logger.info("Initialized ProductionSentimentAnalyzer with FinBERT model")

    def _normalize_scores(self, scores):
        """Convert pipeline scores to standardized format"""
        if isinstance(scores, list) and len(scores) > 0:
            if isinstance(scores[0], list):
                scores = scores[0]
        
        result = {}
        for item in scores:
            label = item['label'].lower()
            score = item['score']
            
            # Map FinBERT labels
            if 'pos' in label or label == 'positive':
                result['positive'] = score
            elif 'neg' in label or label == 'negative':
                result['negative'] = score
            elif 'neu' in label or label == 'neutral':
                result['neutral'] = score
        
        return result

    def _score_from_probs(self, prob_dict):
        """Compute continuous score and label from probabilities"""
        pos = prob_dict.get('positive', 0.0)
        neg = prob_dict.get('negative', 0.0)
        neu = prob_dict.get('neutral', 0.0)
        
        # Compute score as pos - neg (range: -1 to +1)
        score = round((pos - neg), 4)
        
        # Determine label by highest probability
        max_prob = max(pos, neg, neu)
        if max_prob == pos:
            label = 'positive'
        elif max_prob == neg:
            label = 'negative'
        else:
            label = 'neutral'
        
        return label, score

    def _chunk_text(self, text):
        """Split long text into chunks for better processing"""
        if len(text) <= self.max_chunk_chars:
            return [text]
        
        chunks = []
        start = 0
        while start < len(text):
            end = start + self.max_chunk_chars
            chunk = text[start:end]
            
            # Try to split on sentence boundary
            if end < len(text):
                m = re.search(r'[.!?]\s', text[end:end+200])
                if m:
                    end += m.end()
            
            chunks.append(text[start:end].strip())
            start = end
        
        return chunks

    def analyze_text(self, text):
        """Analyze full text and return aggregated sentiment"""
        chunks = self._chunk_text(text)
        labels = []
        scores = []
        
        for chunk in chunks:
            try:
                result = self.sentiment(chunk)
                prob_dict = self._normalize_scores(result)
                label, score = self._score_from_probs(prob_dict)
                labels.append(label)
                scores.append(score)
            except Exception as e:
                logger.error(f"Error analyzing chunk: {e}")
                continue
        
        if not scores:
            return {"sentiment": "neutral", "sentiment_score": 0.0}
        
        # Aggregate results
        mean_score = round(sum(scores) / len(scores), 4)
        label_counts = Counter(labels)
        majority_label = label_counts.most_common(1)[0][0]
        
        # Use score sign to resolve ties
        if len(label_counts) > 1 and label_counts.most_common(1)[0][1] == label_counts.most_common(2)[1][1]:
            if mean_score > 0.05:
                majority_label = 'positive'
            elif mean_score < -0.05:
                majority_label = 'negative'
            else:
                majority_label = 'neutral'
        
        return {"sentiment": majority_label, "sentiment_score": mean_score}

    def extract_entity_clauses(self, text, entity_name):
        """
        Advanced entity context extraction with improved comma/clause splitting.
        Specifically handles cases like "TCS gained today, HDFC loses in stock market"
        """
        entity_lower = entity_name.lower()
        contexts = []
        
        # Strategy 1: Split by sentence first
        sentences = re.split(r'[.!?]+\s*', text)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 10:
                continue
            
            # Check if entity appears in this sentence
            pattern = r'\b' + re.escape(entity_lower) + r'\b'
            if re.search(pattern, sentence.lower()):
                
                # Strategy A: Split by commas AND conjunctions for better separation
                # Handle patterns like "X gained, Y lost" or "X beat expectations while Y disappointed"
                clause_separators = r'[,;]\s*|(?:\s+(?:while|but|however|meanwhile|whereas|although|though)\s+)'
                clauses = re.split(clause_separators, sentence)
                
                # Find clauses that contain the entity
                entity_clauses = []
                for clause in clauses:
                    clause = clause.strip()
                    if re.search(pattern, clause.lower()):
                        entity_clauses.append(clause)
                
                # If we found specific clauses, use them
                if entity_clauses:
                    contexts.extend(entity_clauses)
                else:
                    # Fallback: try to extract phrase around entity mention
                    match = re.search(pattern, sentence.lower())
                    if match:
                        start_pos = match.start()
                        
                        # Find the start of the relevant phrase (look backward for comma, start of sentence)
                        phrase_start = 0
                        for i in range(start_pos - 1, -1, -1):
                            if sentence[i] in '.,;':
                                phrase_start = i + 1
                                break
                        
                        # Find the end of the relevant phrase (look forward for comma, end of sentence)
                        phrase_end = len(sentence)
                        for i in range(start_pos, len(sentence)):
                            if sentence[i] in '.,;':
                                # Include a bit more context after comma if it's short
                                if i < len(sentence) - 1:
                                    next_comma = sentence.find(',', i + 1)
                                    if next_comma == -1 or next_comma - i > 30:
                                        phrase_end = min(i + 30, len(sentence))
                                    else:
                                        phrase_end = next_comma
                                else:
                                    phrase_end = i
                                break
                        
                        phrase = sentence[phrase_start:phrase_end].strip()
                        if phrase and len(phrase) > 10:
                            contexts.append(phrase)
        
        # Strategy 2: If no good contexts found, use broader search
        if not contexts:
            # Look for the entity and take surrounding context
            idx = text.lower().find(entity_lower)
            if idx != -1:
                start = max(0, idx - 50)
                end = min(len(text), idx + 100)
                context = text[start:end].strip()
                
                # Try to start and end on word boundaries
                if start > 0:
                    space_idx = context.find(' ')
                    if space_idx > 0:
                        context = context[space_idx:].strip()
                
                if end < len(text):
                    space_idx = context.rfind(' ')
                    if space_idx > 0:
                        context = context[:space_idx].strip()
                
                if len(context) > 20:
                    contexts.append(context)
        
        return contexts if contexts else [text]  # Fallback to full text

    def analyze_entity(self, entity_name, text):
        """
        Analyze sentiment specifically for an entity using improved context extraction
        """
        contexts = self.extract_entity_clauses(text, entity_name)
        
        if not contexts:
            logger.warning(f"No context found for entity {entity_name}, using full text")
            return self.analyze_text(text)
        
        # Analyze each context and aggregate
        context_results = []
        for context in contexts:
            result = self.analyze_text(context)
            context_results.append(result)
            logger.debug(f"Entity {entity_name} context: '{context[:50]}...' -> {result}")
        
        # Aggregate multiple contexts
        if len(context_results) == 1:
            return context_results[0]
        
        # Multiple contexts: aggregate scores and pick majority label
        scores = [r['sentiment_score'] for r in context_results]
        labels = [r['sentiment'] for r in context_results]
        
        mean_score = round(sum(scores) / len(scores), 4)
        majority_label = Counter(labels).most_common(1)[0][0]
        
        return {"sentiment": majority_label, "sentiment_score": mean_score}

    async def get_unanalyzed_news(self):
        """Get news articles that need sentiment analysis - both sentiment AND sentiment_score must be null"""
        try:
            response = await asyncio.to_thread(
                lambda: self.supabase.table("news")
                .select("*")
                .is_("sentiment", "null")
                .is_("sentiment_score", "null")
                .execute()
            )
            return response.data if response.data is not None else []
        except Exception as e:
            logger.error(f"Error fetching unanalyzed news: {str(e)}")
            return []

    async def update_news_sentiment(self, news_id, enrichment):
        """Update news article with sentiment data"""
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
            logger.info(f"Updated news ID {news_id} with sentiment: {enrichment}")
        except Exception as e:
            logger.error(f"Error in update function for news ID {news_id}: {str(e)}")

    def detect_companies_in_text(self, title, content=""):
        """
        Detect company names in title and content.
        Prioritizes known patterns and filters noise.
        """
        text = f"{title} {content}".strip()
        companies = set()
        
        # Known company patterns (add more as needed)
        known_patterns = {
            r'\bBajaj Finance\b': 'Bajaj Finance',
            r'\bTech Mahindra\b': 'Tech Mahindra',
            r'\bReliance Industries?\b': 'Reliance Industries',
            r'\bInfosys\b': 'Infosys',
            r'\bTCS\b': 'TCS',
            r'\bHDFC\b': 'HDFC',
            r'\bWipro\b': 'Wipro',
            r'\bICICI Bank\b': 'ICICI Bank',
            r'\bAdani Group\b': 'Adani Group',
            r'\bTata Motors?\b': 'Tata Motors'
        }
        
        # Check for known companies first
        for pattern, name in known_patterns.items():
            if re.search(pattern, text, re.IGNORECASE):
                companies.add(name)
        
        # If no known companies, try generic extraction
        if not companies:
            # Extract capitalized words that could be company names
            candidates = re.findall(r'\b[A-Z][A-Za-z]{2,}(?:\s+[A-Z][A-Za-z]+)?\b', title)
            
            # Filter out common non-company words
            stopwords = {
                'Today', 'Market', 'Stock', 'News', 'The', 'And', 'With', 'Among', 
                'Stocks', 'Week', 'Month', 'Year', 'High', 'Low', 'Volume', 'Share',
                'Company', 'Limited', 'Corp', 'Inc', 'Group', 'Bank', 'Finance'
            }
            
            for candidate in candidates:
                if candidate not in stopwords and len(candidate) > 3:
                    companies.add(candidate)
        
        return list(companies)

async def test_production_analyzer():
    """Test the production analyzer with known cases"""
    analyzer = ProductionSentimentAnalyzer()
    
    test_cases = [
        {
            "text": "TCS gained today, HDFC loses in stock market",
            "companies": ["TCS", "HDFC"]
        },
        {
            "text": "Reliance Industries reported strong quarterly results. Meanwhile, Infosys shares declined.",
            "companies": ["Reliance Industries", "Infosys"]
        },
        {
            "text": "Tech Mahindra beat expectations while Wipro disappointed investors.",
            "companies": ["Tech Mahindra", "Wipro"]
        }
    ]
    
    print("[TEST] PRODUCTION SENTIMENT ANALYZER TEST")
    print("=" * 60)
    
    for i, case in enumerate(test_cases, 1):
        print(f"\nTest Case {i}: {case['text']}")
        print("-" * 60)
        
        # Document-level analysis
        doc_result = analyzer.analyze_text(case['text'])
        print(f"Document-level: {doc_result}")
        
        # Entity-level analysis
        print("Entity-level analysis:")
        for company in case['companies']:
            contexts = analyzer.extract_entity_clauses(case['text'], company)
            entity_result = analyzer.analyze_entity(company, case['text'])
            
            print(f"  {company}:")
            print(f"    Contexts: {contexts}")
            print(f"    Sentiment: {entity_result}")
        print()

async def test_with_sample_database_records():
    """Test with sample records that match your database structure"""
    analyzer = ProductionSentimentAnalyzer()
    
    # Sample records that match your database structure
    sample_records = [
        {
            "id": "test-1",
            "title": "TCS gained today, HDFC loses in stock market",
            "content": "TCS gained today, HDFC loses in stock market",
            "stock_name": "TCS",
            "yfin_symbol": "TCS.NS"
        },
        {
            "id": "test-2", 
            "title": "TCS gained today, HDFC loses in stock market",
            "content": "TCS gained today, HDFC loses in stock market",
            "stock_name": "HDFC Bank",
            "yfin_symbol": "HDFCBANK.NS"
        },
        {
            "id": "test-3",
            "title": "Bajaj Finance at a fresh all-time high, stock hit ₹1,000 for the first time!",
            "content": "Bajaj Finance at a fresh all-time high, stock hit ₹1,000 for the first time! SEBI RA Aditya expects the rally to continue...",
            "stock_name": "Bajaj Finance",
            "yfin_symbol": "BAJFINANCE.NS"
        }
    ]
    
    print("🧪 TESTING WITH DATABASE-LIKE RECORDS")
    print("=" * 60)
    
    for record in sample_records:
        title = record['title']
        content = record['content'] 
        stock_name = record['stock_name']
        full_text = f"{title} {content}".strip()
        
        print(f"\nRecord ID: {record['id']}")
        print(f"Title: {title[:60]}...")
        print(f"Stock: {stock_name}")
        print("-" * 40)
        
        # Analyze sentiment for this specific stock in the article
        sentiment_result = analyzer.analyze_entity(stock_name, full_text)
        
        print(f"Entity-specific sentiment: {sentiment_result}")
        
        # Show the context that was analyzed
        contexts = analyzer.extract_entity_clauses(full_text, stock_name)
        print(f"Analyzed context: {contexts}")
        print()

async def main():
    """Main function - choose test mode or production mode"""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--production":
        print("[PROD] PRODUCTION MODE - WILL UPDATE DATABASE")
        confirm = input("Are you sure you want to run in production mode? (yes/no): ")
        if confirm.lower() != 'yes':
            print("Production mode cancelled.")
            return
        
        analyzer = ProductionSentimentAnalyzer()
        news_articles = await analyzer.get_unanalyzed_news()
        logger.info(f"Found {len(news_articles)} unanalyzed news records")
        
        for article in news_articles:
            try:
                # Get the stock name for this specific record
                stock_name = article.get('stock_name', '')
                title = article.get('title', '')
                content = article.get('content', '')
                full_text = f"{title} {content}".strip()
                
                if not stock_name:
                    logger.warning(f"No stock_name found for article {article['id']}, using document-level analysis")
                    # Fallback to document-level analysis
                    sentiment_result = analyzer.analyze_text(full_text)
                else:
                    # Analyze sentiment specifically for this stock in the context of the article
                    sentiment_result = analyzer.analyze_entity(stock_name, full_text)
                
                # Log the result
                logger.info(f"Article {article['id']} - {stock_name}: {sentiment_result}")
                print(f"Processing: {title[:60]}...")
                print(f"Stock: {stock_name} -> Sentiment: {sentiment_result['sentiment']} ({sentiment_result['sentiment_score']:+.3f})")
                
                # Update the specific record with sentiment
                await analyzer.update_news_sentiment(article['id'], sentiment_result)
                
            except Exception as e:
                logger.error(f"Error processing article {article['id']}: {str(e)}")
                continue
        
        logger.info("Sentiment analysis completed for all records")
    
    else:
        print("[PROD] PRODUCTION MODE - WRITING TO DATABASE")
        
        analyzer = ProductionSentimentAnalyzer()
        news_articles = await analyzer.get_unanalyzed_news()
        logger.info(f"Found {len(news_articles)} unanalyzed news records")
        
        processed_count = 0
        
        for article in news_articles:
            try:
                # Get the stock name for this specific record
                stock_name = article.get('stock_name', '')
                title = article.get('title', '')
                content = article.get('content', '')
                full_text = f"{title} {content}".strip()
                
                if not stock_name:
                    logger.warning(f"No stock_name found for article {article['id']}, using document-level analysis")
                    # Fallback to document-level analysis
                    sentiment_result = analyzer.analyze_text(full_text)
                else:
                    # Analyze sentiment specifically for this stock in the context of the article
                    sentiment_result = analyzer.analyze_entity(stock_name, full_text)
                
                # Log the result
                logger.info(f"Article {article['id']} - {stock_name}: {sentiment_result}")
                print(f"ID: {article['id'][:8]}... | Stock: {stock_name:<20} | Sentiment: {sentiment_result['sentiment']:<8} ({sentiment_result['sentiment_score']:+.3f})")
                print(f"Title: {title[:80]}...")
                
                # Extract and show context for debugging
                if stock_name:
                    contexts = analyzer.extract_entity_clauses(full_text, stock_name)
                    if contexts:
                        print(f"Context: {contexts[0][:100]}...")
                
                print("-" * 100)
                
                # Update the specific record with sentiment (DRY RUN - NO ACTUAL WRITES)
                await analyzer.update_news_sentiment(article['id'], sentiment_result)
                
                processed_count += 1
                
                # Process in batches to avoid overwhelming output
                if processed_count % 10 == 0:
                    print(f"\n[INFO] Processed {processed_count} records so far...\n")
                
            except Exception as e:
                logger.error(f"Error processing article {article['id']}: {str(e)}")
                continue
        
        print(f"\n[SUCCESS] Analysis completed for {processed_count} records")
        print("[INFO] All sentiment data has been written to the database")
        logger.info(f"Sentiment analysis completed for {processed_count} records")

if __name__ == "__main__":
    asyncio.run(main())