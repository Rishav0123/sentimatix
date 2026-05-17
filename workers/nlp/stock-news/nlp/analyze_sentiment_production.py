import os
import logging
from datetime import datetime
from pathlib import Path
from supabase import create_client
from transformers import pipeline
import asyncio
import re
from collections import Counter
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def parse_keyword_lst(kw_data) -> list:
    """Parse keyword_lst JSONB field into a flat list of alias strings."""
    if not kw_data:
        return []
    try:
        if isinstance(kw_data, str):
            import json
            kw_data = json.loads(kw_data)
        if isinstance(kw_data, dict):
            return kw_data.get('keyword', [])
        if isinstance(kw_data, list):
            return kw_data
    except Exception as e:
        return []
    return []

# Keywords that are too generic for entity-level clause extraction
# (identified from live keyword_lst analysis — all other short keywords are valid tickers)
ENTITY_SEARCH_BLOCKLIST = {'global', 'take'}

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
SUPABASE_URL = os.environ.get("SUPABASE_URL") or "https://hdsntducurmhossannue.supabase.co"
SUPABASE_KEY = os.environ.get("SUPABASE_KEY") or "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imhkc250ZHVjdXJtaG9zc2FubnVlIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzczNjM0MTAsImV4cCI6MjA3NTUxMDUxNX0.aTghWk2f96wEVkVkmp0QlNoj274RKqJHKGLPu9F226s"

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

    async def fetch_keyword_map(self, stock_ids: list) -> dict:
        """Pre-fetch keyword_lst for all stock_ids in a batch."""
        if not stock_ids:
            return {}
        try:
            # Remove any None values and deduplicate
            clean_ids = list(set([sid for sid in stock_ids if sid]))
            if not clean_ids:
                return {}
                
            response = await asyncio.to_thread(
                lambda: self.supabase.table('stocks')
                    .select('id, keyword_lst')
                    .in_('id', clean_ids)
                    .execute()
            )
            result = {}
            for row in (response.data or []):
                result[row['id']] = parse_keyword_lst(row.get('keyword_lst'))
            return result
        except Exception as e:
            logger.error(f"Error fetching keyword map: {e}")
            return {}

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

    def _apply_heuristics(self, text, pos, neg, neu):
        text_lower = text.lower()
        
        pos_patterns = [r'narrower than expected.*loss', r'debt reduction', r'beat.*estimates', r'raised.*guidance', r'better than expected']
        neg_patterns = [r'missed.*estimates', r'lowered.*guidance', r'wider than expected.*loss']
        double_neg_patterns = [r'not\s+(?:declining|falling|losing|missing|down|bad|worse)']
        
        for p in pos_patterns:
            if re.search(p, text_lower):
                pos += 0.4
                neg = max(0, neg - 0.2)
                
        for p in neg_patterns:
            if re.search(p, text_lower):
                neg += 0.4
                pos = max(0, pos - 0.2)
                
        for p in double_neg_patterns:
            if re.search(p, text_lower):
                neg = neg * 0.5
                neu += neg * 0.5
                
        total = pos + neg + neu
        if total > 0:
            pos /= total
            neg /= total
            neu /= total
            
        return pos, neg, neu

    def _calculate_advanced_score(self, pos, neg, neu, text):
        import math
        
        is_volatile = False
        if pos > 0.4 and neg > 0.4:
            label = 'CONFLICTED'
            is_volatile = True
        else:
            max_prob = max(pos, neg, neu)
            if max_prob == pos:
                label = 'positive'
            elif max_prob == neg:
                label = 'negative'
            else:
                label = 'neutral'
                
        confidence = max(pos, neg, neu)
        if confidence < 0.5 and not is_volatile:
            label = 'neutral'
            
        raw_score = pos - neg
        adjusted_score = raw_score * (1 - neu)
        
        word_count = len(text.split())
        length_factor = min(1.0, math.log10(max(10, word_count)) / 2.5)
        
        final_score = round(adjusted_score * length_factor, 4)
        
        return {
            "sentiment": label,
            "sentiment_score": final_score,
            "confidence": round(confidence, 4),
            "is_volatile": is_volatile
        }

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

    def analyze_text_probs(self, text):
        """Analyze full text and return average probabilities"""
        chunks = self._chunk_text(text)
        pos_list = []
        neg_list = []
        neu_list = []
        
        for chunk in chunks:
            try:
                result = self.sentiment(chunk)
                prob_dict = self._normalize_scores(result)
                pos_list.append(prob_dict.get('positive', 0.0))
                neg_list.append(prob_dict.get('negative', 0.0))
                neu_list.append(prob_dict.get('neutral', 0.0))
            except Exception as e:
                logger.error(f"Error analyzing chunk: {e}")
                continue
        
        if not pos_list:
            return 0.0, 0.0, 1.0
            
        avg_pos = sum(pos_list) / len(pos_list)
        avg_neg = sum(neg_list) / len(neg_list)
        avg_neu = sum(neu_list) / len(neu_list)
        
        return self._apply_heuristics(text, avg_pos, avg_neg, avg_neu)

    def analyze_text(self, text):
        """Analyze full text and return advanced sentiment object"""
        pos, neg, neu = self.analyze_text_probs(text)
        return self._calculate_advanced_score(pos, neg, neu, text)

    def extract_entity_clauses(self, text: str, entity_name: str, aliases: list = None) -> list:
        """
        Advanced entity context extraction with prioritized alias matching.
        Builds a prioritized search list (longest → shortest), tries each alias, 
        and merges all found contexts.
        """
        # Build search list: entity_name first, then aliases, longest→shortest
        all_terms = ([entity_name] if entity_name else []) + (aliases or [])
        
        seen = set()
        search_terms = []
        for t in all_terms:
            if not t: continue
            t_clean = t.strip()
            t_lower = t_clean.lower()
            if t_clean and t_lower not in seen and t_lower not in ENTITY_SEARCH_BLOCKLIST:
                seen.add(t_lower)
                search_terms.append(t_clean)
        
        # Sort longest→shortest so more specific terms are tried first
        search_terms.sort(key=len, reverse=True)

        all_contexts = []
        seen_contexts = set()

        for term in search_terms:
            term_lower = term.lower()
            pattern = r'\b' + re.escape(term_lower) + r'\b'
            
            # Split by sentence first
            sentences = re.split(r'[.!?]+\s*', text)
            
            for sentence in sentences:
                sentence = sentence.strip()
                if len(sentence) < 10:
                    continue
                
                # Check if this alias appears in this sentence
                if re.search(pattern, sentence.lower()):
                    # Strategy A: Split by commas AND conjunctions
                    clause_separators = r'[,;]\s*|(?:\s+(?:while|but|however|meanwhile|whereas|although|though)\s+)'
                    clauses = re.split(clause_separators, sentence)
                    
                    found_in_this_sentence = False
                    for clause in clauses:
                        clause = clause.strip()
                        if re.search(pattern, clause.lower()):
                            if clause not in seen_contexts:
                                all_contexts.append(clause)
                                seen_contexts.add(clause)
                                found_in_this_sentence = True
                    
                    # Fallback phrase extraction if no specific clause matched
                    if not found_in_this_sentence:
                        match = re.search(pattern, sentence.lower())
                        if match:
                            start_pos = match.start()
                            phrase_start = 0
                            for i in range(start_pos - 1, -1, -1):
                                if sentence[i] in '.,;':
                                    phrase_start = i + 1
                                    break
                            phrase_end = len(sentence)
                            for i in range(start_pos, len(sentence)):
                                if sentence[i] in '.,;':
                                    phrase_end = i
                                    break
                            phrase = sentence[phrase_start:phrase_end].strip()
                            if phrase and len(phrase) > 10 and phrase not in seen_contexts:
                                all_contexts.append(phrase)
                                seen_contexts.add(phrase)
            
            # If we found matches for a long/specific term, we could potentially stop, 
            # but merging results from multiple aliases is safer for comprehensive sentiment.
            # However, if we already have good contexts, we don't necessarily need to keep looking for shorter ones.
            if all_contexts and len(term) > 10:
                break

        # Strategy 2: If still no good contexts found, use broader search for ANY alias
        if not all_contexts:
            for term in search_terms:
                term_lower = term.lower()
                idx = text.lower().find(term_lower)
                if idx != -1:
                    start = max(0, idx - 50)
                    end = min(len(text), idx + 100)
                    context = text[start:end].strip()
                    if len(context) > 20:
                        all_contexts.append(context)
                        break # Found one match in broader search, that's enough

        return all_contexts if all_contexts else [text]

    def analyze_entity(self, entity_name, text, aliases=None):
        """
        Analyze sentiment specifically for an entity using improved context extraction with alias support
        """
        contexts = self.extract_entity_clauses(text, entity_name, aliases=aliases)
        
        if not contexts:
            logger.warning(f"No context found for entity {entity_name}, using full text")
            return self.analyze_text(text)
            
        pos_list = []
        neg_list = []
        neu_list = []
        
        for context in contexts:
            pos, neg, neu = self.analyze_text_probs(context)
            pos_list.append(pos)
            neg_list.append(neg)
            neu_list.append(neu)
            
        avg_pos = sum(pos_list) / len(pos_list)
        avg_neg = sum(neg_list) / len(neg_list)
        avg_neu = sum(neu_list) / len(neu_list)
        
        combined_text = " ".join(contexts)
        result = self._calculate_advanced_score(avg_pos, avg_neg, avg_neu, combined_text)
        logger.debug(f"Entity {entity_name} combined contexts -> {result}")
        return result

    async def get_unanalyzed_news_batch(self, limit=100):
        """Get a batch of news articles that need sentiment analysis using self-expanding time windows to leverage published_at index"""
        from datetime import datetime, timedelta, timezone
        
        # We query using progressively larger windows to leverage the index on published_at
        # 1. 3 days: captures normal daily runs and weekend lag (extremely fast)
        # 2. 14 days: captures recent backlogs (very fast)
        # 3. 60 days: captures older backlog (fast)
        windows = [3, 14, 60]
        
        for days in windows:
            try:
                since_date = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
                logger.info(f"Scanning for unanalyzed news since {since_date} ({days} days)...")
                
                response = await asyncio.to_thread(
                    lambda: self.supabase.table("news")
                    .select("id, title, content, stock_id, stock_name, published_at")
                    .is_("sentiment", "null")
                    .is_("sentiment_score", "null")
                    .gte("published_at", since_date)
                    .limit(limit)
                    .execute()
                )
                
                data = response.data or []
                if data:
                    logger.info(f"Found {len(data)} unanalyzed articles in the {days}-day window.")
                    return data
                    
            except Exception as e:
                logger.warning(f"Query for {days}-day window failed or timed out: {str(e)}")
                continue
                
        # Fallback: If no recent articles are found, try one last time with no time filter
        # But we limit it to a very small size (limit=10) to minimize sequential scan effort
        try:
            logger.info("No recent unanalyzed articles found. Trying fallback full table scan with small limit...")
            response = await asyncio.to_thread(
                lambda: self.supabase.table("news")
                .select("id, title, content, stock_id, stock_name, published_at")
                .is_("sentiment", "null")
                .is_("sentiment_score", "null")
                .limit(min(limit, 10))
                .execute()
            )
            return response.data or []
        except Exception as e:
            logger.error(f"Fallback full table scan failed: {str(e)}")
            return []

    async def update_news_sentiment(self, news_id, enrichment):
        """Update news article with sentiment data"""
        try:
            await asyncio.to_thread(
                lambda: self.supabase.table("news")
                .update({
                    "sentiment": enrichment["sentiment"],
                    "sentiment_score": enrichment["sentiment_score"],
                    "confidence": enrichment.get("confidence"),
                    "is_volatile": enrichment.get("is_volatile")
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
    
    print("[TEST] TESTING WITH DATABASE-LIKE RECORDS")
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
        
        label = sentiment_result['sentiment']
        score = sentiment_result['sentiment_score']
        conf = sentiment_result.get('confidence', 'N/A')
        volatile = sentiment_result.get('is_volatile', False)
        print(f"  Sentiment : {label} ({score:+.4f})")
        print(f"  Confidence: {conf:.4f}" if isinstance(conf, float) else f"  Confidence: {conf}")
        print(f"  Volatile  : {volatile}")
        
        # Show the context that was analyzed
        contexts = analyzer.extract_entity_clauses(full_text, stock_name)
        print(f"Analyzed context: {contexts}")
        print()

async def main():
    """Main function - Production sentiment analysis loop with robust batching"""
    import sys
    
    logger.info("Starting Production Sentiment Analysis")
    analyzer = ProductionSentimentAnalyzer()
    
    batch_size = 100
    max_total_process = 5000  # Cap maximum processed in one run to avoid infinite loop
    processed_count = 0
    
    logger.info(f"Processing unanalyzed news in batches of {batch_size} (Cap: {max_total_process})")
    
    while processed_count < max_total_process:
        # Fetch the next batch of unanalyzed articles
        news_articles = await analyzer.get_unanalyzed_news_batch(limit=batch_size)
        batch_count = len(news_articles)
        
        if batch_count == 0:
            logger.info("No more unanalyzed records found.")
            break
            
        logger.info(f"Fetched batch of {batch_count} unanalyzed news records to process...")
        
        # Pre-fetch keyword map for all stocks in this batch
        stock_ids = [a.get('stock_id') for a in news_articles if a.get('stock_id')]
        keyword_map = await analyzer.fetch_keyword_map(stock_ids)
        logger.info(f"Loaded keyword map for {len(keyword_map)} stocks in this batch")
        
        for article in news_articles:
            try:
                # Get the stock name and aliases for this specific record
                stock_id = article.get('stock_id')
                stock_name = article.get('stock_name', '')
                aliases = keyword_map.get(stock_id, [])
                
                title = article.get('title', '')
                content = article.get('content', '')
                full_text = f"{title} {content}".strip()
                
                if not stock_name and not aliases:
                    logger.warning(f"No stock_identity for article {article['id']}, using document-level analysis")
                    sentiment_result = analyzer.analyze_text(full_text)
                else:
                    # Analyze sentiment specifically for this stock in the context of the article
                    sentiment_result = analyzer.analyze_entity(stock_name, full_text, aliases=aliases)
                
                # Update the record with sentiment
                await analyzer.update_news_sentiment(article['id'], sentiment_result)
                
                processed_count += 1
                
                # Progress logging
                if processed_count % 10 == 0:
                    print(f"Processed {processed_count} articles | Stock: {stock_name[:20]:<20} | Sentiment: {sentiment_result['sentiment']}")
                    logger.info(f"Progress: {processed_count} articles processed")
                
            except Exception as e:
                logger.error(f"Error processing article {article['id']}: {str(e)}")
                # To prevent an infinite loop on a corrupted article that repeatedly fails to update:
                # We mark it as FAILED in the database so subsequent batches ignore it.
                try:
                    await analyzer.update_news_sentiment(article['id'], {
                        "sentiment": "FAILED",
                        "sentiment_score": 0.0,
                        "confidence": 0.0,
                        "is_volatile": False
                    })
                except Exception as update_err:
                    logger.error(f"Failed to mark article {article['id']} as FAILED: {str(update_err)}")
                
                processed_count += 1
                continue
                
        logger.info(f"Finished batch of {batch_count} articles. Total processed so far: {processed_count}")
    
    logger.info(f"Sentiment analysis pipeline completed. Total processed: {processed_count}")
    print(f"\n[SUCCESS] Completed analysis for {processed_count} records")

if __name__ == "__main__":
    asyncio.run(main())