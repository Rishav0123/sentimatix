from datetime import datetime, timedelta
from dateutil import parser as dateutil_parser
import feedparser
import html
import logging
import re
import sys
import os
import json
from bs4 import BeautifulSoup
from pathlib import Path
import requests
import argparse

# Add the root directory to sys.path
sys.path.append(str(Path(__file__).parent.parent))
from utilities.load_keywords_scrape import fetch_stock_keywords
from utilities.store_news_article import store_news_article
from utilities.check_existing_news import check_existing_news

try:
    from scrapers.agent_scrapers import enhanced_keyword_matching
except ImportError:
    from agent_scrapers import enhanced_keyword_matching

# Fallback Google News URL (now secondary option)
# Fallback Google News URL (Restricted to last 3 days with tbs=qdr:d3)
GOOGLE_NEWS_URL = f"https://news.google.com/search?q={{stock}}+finance+india&hl=en-IN&gl=IN&ceid=IN:en&tbs=qdr:d3"

# Direct RSS feeds from major Indian financial news sources (PRIMARY METHOD)
RSS_SOURCES = {
    "Economic Times - Markets": "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
    "Economic Times - Stocks": "https://economictimes.indiatimes.com/markets/stocks/rssfeeds/2146842.cms", 
    "Economic Times - Economy": "https://economictimes.indiatimes.com/news/economy/rssfeeds/1715249553.cms",
    "Moneycontrol": "https://www.moneycontrol.com/rss/MCtopnews.xml",
    "LiveMint - Markets": "https://www.livemint.com/rss/markets",
    "LiveMint - Money": "https://www.livemint.com/rss/money",
    "Business Standard - Markets": "https://www.business-standard.com/rss/markets-106.rss",
    "Business Standard - Economy": "https://www.business-standard.com/rss/economy-102.rss",
    "Financial Express": "https://www.financialexpress.com/market/rss",
    "Bloomberg Quint": "https://www.bloombergquint.com/feed/markets",
    "Reuters India Business": "https://feeds.reuters.com/reuters/INbusinessNews",
    "CNBC TV18": "https://www.cnbctv18.com/rss/market.xml"
}

def is_financially_relevant_context(text, keyword):
    """
    Check if the keyword appears in a financially relevant context.
    This helps reduce false positives by ensuring the article is actually about finance/business.
    """
    # Financial context indicators
    financial_indicators = [
        # Market/Trading terms
        'stock', 'share', 'market', 'trading', 'investor', 'investment', 'portfolio',
        'nifty', 'sensex', 'bse', 'nse', 'equity', 'mutual fund', 'ipo', 'listing',
        
        # Financial performance
        'profit', 'loss', 'revenue', 'earnings', 'dividend', 'buyback', 'results',
        'quarter', 'q1', 'q2', 'q3', 'q4', 'financial year', 'fy', 'annual',
        
        # Business operations
        'company', 'corporate', 'business', 'industry', 'sector', 'enterprise',
        'management', 'board', 'ceo', 'cfo', 'chairman', 'director',
        
        # Economic indicators
        'economy', 'economic', 'gdp', 'inflation', 'rbi', 'sebi', 'rupee',
        'currency', 'fiscal', 'budget', 'policy', 'rate', 'bank', 'banking',
        
        # Investment terms
        'fund', 'capital', 'debt', 'credit', 'loan', 'finance', 'financial',
        'valuation', 'price', 'value', 'worth', 'cost', 'expense',
        
        # Market sentiment
        'bullish', 'bearish', 'rally', 'correction', 'volatile', 'trend',
        'growth', 'decline', 'surge', 'drop', 'gain', 'fall'
    ]
    
    # Check if any financial indicators appear near the keyword (within reasonable distance)
    text_lower = text.lower()
    
    # Find all positions of the keyword
    keyword_positions = []
    start = 0
    while True:
        pos = text_lower.find(keyword.lower(), start)
        if pos == -1:
            break
        keyword_positions.append(pos)
        start = pos + 1
    
    # For each keyword occurrence, check surrounding context (100 characters before and after)
    context_window = 100
    for pos in keyword_positions:
        start_context = max(0, pos - context_window)
        end_context = min(len(text_lower), pos + len(keyword) + context_window)
        context = text_lower[start_context:end_context]
        
        # Check if any financial indicator is in this context
        for indicator in financial_indicators:
            if indicator in context:
                return True
    
    # Additional check: if the text contains multiple financial indicators, it's likely relevant
    indicator_count = sum(1 for indicator in financial_indicators if indicator in text_lower)
    if indicator_count >= 3:  # At least 3 financial terms suggest it's finance-related
        return True
    
    return False

def clean_html_content(text):
    """
    Clean HTML entities and unwanted characters from text content
    """
    if not text:
        return text
    
    # Decode HTML entities like &amp;nbsp;, &amp;, &quot;, etc.
    cleaned = html.unescape(text)
    
    # Remove HTML tags if any
    cleaned = re.sub(r'<[^>]+>', '', cleaned)
    
    # Remove extra whitespace characters including non-breaking spaces
    cleaned = re.sub(r'\xa0', ' ', cleaned)  # Non-breaking space
    cleaned = re.sub(r'\u00a0', ' ', cleaned)  # Unicode non-breaking space
    cleaned = re.sub(r'&nbsp;', ' ', cleaned)  # Any remaining &nbsp;
    cleaned = re.sub(r'\s+', ' ', cleaned)  # Multiple spaces to single space
    
    return cleaned.strip()

def clean_time_references(text):
    """
    Remove time references like '1 hour ago', '30 minutes ago', 'Yesterday', etc. from text
    Enhanced version with better patterns and author byline removal
    """
    if not text:
        return text
    
    # More comprehensive patterns to match time references anywhere in text
    time_patterns = [
        r'\b\d+\s*(hour|hours|hr|hrs|minute|minutes|min|mins)\s*ago\b',
        r'\b(today|yesterday|earlier today|this morning|this evening)\b',
        r'\b\d+\s*days?\s*ago\b',
        r'\bLive:\s*',
        r'\bBreaking:\s*',
        r'\bUpdate:\s*',
        r'\s*\d+\s*(minute|minutes|min|hour|hours|hr|day|days)\s*ago\s*',
        r'\s*Yesterday\s*',
        r'\s*Today\s*',
        r'\s*\d+\s*(min|hr)\s*',
        r'\s*\d+\s*(minute|minutes|hour|hours|day|days)\s*',
        r'By\s+[A-Za-z\s]+$',  # Remove "By Author Name" at the end
    ]
    
    cleaned_text = text
    for pattern in time_patterns:
        cleaned_text = re.sub(pattern, '', cleaned_text, flags=re.IGNORECASE)
    
    # Remove author bylines (patterns like "- Author Name" at the end)
    cleaned_text = re.sub(r'\s*-\s*[A-Z][a-z]+\s+[A-Z][a-z]+\s*$', '', cleaned_text)
    cleaned_text = re.sub(r'\s*\|\s*[A-Z][a-z]+\s+[A-Z][a-z]+\s*$', '', cleaned_text)
    
    # Clean up extra whitespace and trailing punctuation
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
    cleaned_text = re.sub(r'\s*[-|]\s*$', '', cleaned_text).strip()  # Remove trailing - or |
    
    return cleaned_text

def split_source_title(text):
    """
    Splits the text at the first occurrence of 'More' (case-insensitive).
    Returns (source, title). If 'More' not found, source is None, title is text.
    """
    if not text:
        return None, text
    parts = re.split(r'(?i)more', text, maxsplit=1)
    if len(parts) > 1:
        source = parts[0].strip()
        title = parts[1].strip()
        return source, title
    else:
        return None, text

def get_today_date():
    return datetime.now().strftime('%Y-%m-%d')

def pre_fetch_all_rss_articles(max_articles_per_source=50):
    """
    Fetch all news articles from direct RSS feeds.
    This is called once at the start of the batch execution.
    """
    all_articles = []
    
    for source_name, rss_url in RSS_SOURCES.items():
        try:
            # Use requests with headers to avoid 403 Forbidden
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
                "Accept": "application/rss+xml, application/xml, text/xml, */*"
            }
            logging.info(f"Pre-fetching RSS source: {source_name}")
            response = requests.get(rss_url, headers=headers, timeout=10)
            
            if response.status_code != 200:
                logging.warning(f"Failed to fetch {source_name} (Status {response.status_code}): {rss_url}")
                continue
                
            feed = feedparser.parse(response.text)
            
            # Check if feed was parsed successfully
            if not hasattr(feed, 'entries') or not feed.entries:
                logging.warning(f"No entries found in XML for {source_name} - {rss_url}")
                continue
                
            for entry in feed.entries[:max_articles_per_source]:
                # Extract article data
                article = {
                    'title': entry.get('title', '').strip(),
                    'url': entry.get('link', ''),  # ACTUAL ARTICLE URL!
                    'source': source_name,
                    'published': entry.get('published', ''),
                    'summary': entry.get('summary', entry.get('description', '')),
                    'author': entry.get('author', ''),
                    'category': entry.get('category', ''),
                    'content': entry.get('content', [{}])[0].get('value', '') if entry.get('content') else ''
                }
                
                # Clean HTML entities and time references from title and content
                if article['title']:
                    article['title'] = clean_html_content(article['title'])
                    article['title'] = clean_time_references(article['title'])
                
                if article['summary']:
                    article['summary'] = clean_html_content(article['summary'])
                
                if article['content']:
                    article['content'] = clean_html_content(article['content'])
                
                if article['url'] and article['title']:
                    article['scraped_at'] = datetime.now().isoformat()
                    all_articles.append(article)
                    
        except Exception as e:
            logging.error(f"Error pre-fetching from {source_name} ({rss_url}): {e}")
            continue
            
    # Remove duplicates based on URL
    seen_urls = set()
    unique_articles = []
    for article in all_articles:
        if article['url'] not in seen_urls:
            seen_urls.add(article['url'])
            unique_articles.append(article)
            
    logging.info(f"Pre-fetch complete. Total unique RSS articles retrieved: {len(unique_articles)}")
    return unique_articles

def filter_rss_articles_in_memory(all_rss_articles, keywords):
    """
    Filter the pre-fetched RSS articles in memory using keyword matching.
    """
    matched_articles = []
    
    for article in all_rss_articles:
        article_text = f"{article.get('title', '')}\n{article.get('summary', '')}"
        is_relevant, matched_kws, rel_score = enhanced_keyword_matching(article_text, keywords)
        
        if is_relevant:
            # Create a copy so we don't modify the shared pre-fetched articles
            matched_article = article.copy()
            matched_article['matched_keywords'] = matched_kws
            matched_article['relevance_score'] = rel_score
            
            if rel_score >= 3:
                matched_article['is_high_relevance'] = True
                
            matched_articles.append(matched_article)
            
    # Sort by publication date (newest first)
    def parse_date(date_str):
        try:
            if date_str:
                for fmt in ['%a, %d %b %Y %H:%M:%S %z', '%Y-%m-%dT%H:%M:%S%z', '%Y-%m-%d %H:%M:%S']:
                    try:
                        return datetime.strptime(date_str.split('+')[0].strip(), fmt.replace('%z', ''))
                    except:
                        continue
            return datetime.min
        except:
            return datetime.min
            
    matched_articles.sort(key=lambda x: parse_date(x['published']), reverse=True)
    return matched_articles

def fetch_stock_news(stock):
    """
    Fallback method using Google News HTML scraping
    This is SECONDARY method - provides obfuscated URLs
    """
    url = GOOGLE_NEWS_URL.format(stock=stock, date=get_today_date())
    response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    if response.status_code != 200:
        print(f"Failed to fetch news for {stock}: {response.status_code}")
        return []
    
    soup = BeautifulSoup(response.text, "html.parser")
    articles = []
    
    # New Google News Structure (2024+)
    # Articles are in div.IFHyqb or div.m5k28
    # Titles are in a.JtKRv
    for item in (soup.select("article") or soup.select("div.IFHyqb") or soup.select("div.m5k28")):
        # Try multiple selectors for title
        title_tag = (item.select_one("a.JtKRv") or 
                    item.select_one("h3 a") or 
                    item.select_one("h4 a") or
                    item.select_one("h3") or
                    item.select_one("h4"))
        
        link = title_tag.get('href') if title_tag and title_tag.name == 'a' else None
        title = title_tag.get_text(strip=True) if title_tag else None
        
        # Get full article text
        article_text = item.get_text(separator=' ', strip=True)
        
        # Try to extract title from article text if not found
        if not title and article_text:
            # Look for the main headline in the article text
            lines = article_text.split('\n')
            for line in lines:
                line = line.strip()
                if len(line) > 20 and not line.startswith('http'):  # Likely a title
                    title = line
                    break
        
        # Clean time references from title and article text
        if title:
            title = clean_html_content(title)
            title = clean_time_references(title)
        if article_text:
            article_text = clean_html_content(article_text)
            article_text = clean_time_references(article_text)
        
        # Extract source from article text (before "More")
        source_from_text = None
        if article_text and 'more' in article_text.lower():
            parts = re.split(r'(?i)more', article_text, maxsplit=1)
            if len(parts) > 1:
                potential_source = parts[0].strip()
                # Clean up source - remove common non-source text
                potential_source = re.sub(r'^\d+\s*(minute|minutes|hour|hours|day|days)\s*ago\s*', '', potential_source, flags=re.IGNORECASE)
                if potential_source and len(potential_source) < 50:  # Reasonable source length
                    source_from_text = potential_source
        
        # Split source and title using split_source_title
        source, clean_title = split_source_title(title)
        if not source:
            # New structure source selector
            source_tag = item.select_one("div.vr7PYb")
            source = source_tag.get_text(strip=True) if source_tag else (source_from_text or 'gnews')
        
        # Use article text as summary if we don't have a good title
        summary = article_text if article_text != title else None
        _, clean_summary = split_source_title(summary) if summary else (None, None)
        
        published = item.select_one("time")
        published_time = published.get('datetime') if published and published.has_attr('datetime') else None
        
        full_url = None
        if link:
            if link.startswith('./'):
                full_url = f"https://news.google.com{link[1:]}"
            elif link.startswith('/'):
                full_url = f"https://news.google.com{link}"
            else:
                full_url = link
        
        articles.append({
            "stock": stock,
            "title": clean_title,
            "source": source,
            "summary": clean_summary,
            "content": article_text,
            "url": full_url,
            "published": published_time,
            "scraped_at": datetime.now().isoformat()
        })
    
    return articles



def save_news(news, filename="article.json"):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(news, f, ensure_ascii=False, indent=2)

def main():
    # Add argparse to handle batches
    parser = argparse.ArgumentParser(description="Scrape Google News")
    parser.add_argument("--stocks-json", type=str, help="JSON string of stocks to process")
    parser.add_argument("--run-id", type=str, help="Run ID for tracking")
    args = parser.parse_args()

    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Unique log file for this batch (using PID to avoid conflicts in parallel)
    batch_suffix = f"_{args.run_id[:8]}" if args.run_id else ""
    pid_suffix = f"_pid{os.getpid()}"
    log_file = log_dir / f"gnews_{datetime.now().strftime('%Y%m%d')}{batch_suffix}{pid_suffix}.log"
    error_log_file = log_dir / f"gnews_error_{datetime.now().strftime('%Y%m%d')}{batch_suffix}{pid_suffix}.log"
    
    logger = logging.getLogger(__name__)
    logger.propagate = False
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    # File handler for info logs
    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setLevel(logging.INFO)
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    # Stream handler for console output
    sh = logging.StreamHandler()
    sh.setLevel(logging.INFO)
    sh.setFormatter(formatter)
    # Try to set encoding for stream handler if possible (Python 3.9+)
    if hasattr(sh, 'stream') and hasattr(sh.stream, 'reconfigure'):
        try:
            sh.stream.reconfigure(encoding='utf-8')
        except Exception:
            pass
    logger.addHandler(sh)
    # File handler for error logs
    eh = logging.FileHandler(error_log_file, encoding="utf-8")
    eh.setLevel(logging.ERROR)
    eh.setFormatter(formatter)
    logger.addHandler(eh)
    try:
        total_found = 0
        total_inserted = 0
        total_skipped = 0
        news_count_per_stock = {}
        all_news = []
        insert_report = {}

        if args.stocks_json:
            if os.path.exists(args.stocks_json):
                with open(args.stocks_json, 'r') as f:
                    stocks = json.load(f)
            else:
                stocks = json.loads(args.stocks_json)
            logger.info(f"Processing {len(stocks)} stocks from command line")
        else:
            stocks = fetch_stock_keywords()
            if not stocks:
                logger.info("No active stocks found in database")
                return
        
        # Pre-fetch all direct RSS feeds once to avoid redundant network requests inside the stock loop
        logger.info("Initializing pre-fetch of all direct RSS feeds...")
        prefetched_rss_articles = pre_fetch_all_rss_articles(max_articles_per_source=50)

        # 1. Collect all matched/candidate articles across all stocks in memory
        all_candidates = [] # List of dicts representing news data to insert
        stock_reports = {} # Maps stock_id to {'found': 0, 'inserted': 0, 'skipped': 0, 'stock_news_len': 0}
        
        for stock in stocks:
            id = stock['id']
            yfin_symbol = stock.get('yfin_symbol')
            keywords = []
            if stock.get('keyword_lst'):
                try:
                    kw_obj = json.loads(stock['keyword_lst']) if isinstance(stock['keyword_lst'], str) else stock['keyword_lst']
                    if isinstance(kw_obj, dict) and 'keyword' in kw_obj:
                        keywords = kw_obj['keyword']
                        logger.info("keywords list: %s", keywords)
                    elif isinstance(kw_obj, list):
                        keywords = kw_obj
                        logger.info("keywords list: %s", keywords)
                except Exception as e:
                    logger.error(f"Error parsing keywords for {id}: {e}")
            if not keywords:
                logger.info(f"No keywords found for {id}, skipping.")
                continue
            
            stock_news = []
            found = 0
            logger.info(f"Fetching news candidates for {id} using keywords: {keywords}")
            
            # Direct RSS feeds (filtered in-memory)
            try:
                logger.info(f"  -> Filtering pre-fetched RSS feeds in-memory for {id}")
                rss_news = filter_rss_articles_in_memory(prefetched_rss_articles, keywords)
                logger.info(f"  -> {len(rss_news)} relevant articles found from RSS feeds in-memory")
                found += len(rss_news)
                
                # Process RSS candidates
                for article in rss_news:
                    matched_keywords = article.get('matched_keywords', [])
                    if not matched_keywords:
                        continue
                        
                    title = article.get('title')
                    if not title or not str(title).strip():
                        summary = article.get('summary')
                        if summary and str(summary).strip():
                            title = summary
                        else:
                            continue
                    
                    published_date_str = None
                    try:
                        if article.get('published'):
                            parsed_date = dateutil_parser.parse(article.get('published'))
                            published_date_str = parsed_date.date().isoformat()
                        else:
                            published_date_str = datetime.now().date().isoformat()
                    except Exception as e:
                        logger.error(f"Error parsing RSS published_date: {e}")
                        published_date_str = "1970-01-01"
                        
                    # Date Filtering: Discard anything older than 15 days
                    try:
                        article_date = datetime.fromisoformat(published_date_str).date()
                        if article_date < (datetime.now().date() - timedelta(days=15)):
                            continue
                    except Exception as de:
                        logger.error(f"Error filtering RSS by date: {de}")
                    
                    source_name = article.get('source', 'RSS Feed')
                    if ' - ' in source_name:
                        source_name = source_name.split(' - ')[0]
                    
                    tags = matched_keywords + ["news", "rss"]
                    if article.get('relevance_score', 0) >= 3:
                        tags.append("relevance:high")

                    rss_news_data = {
                        "stock_id": id,
                        "title": title,
                        "content": clean_html_content(article.get('content') or article.get('summary') or ''),
                        "url": article.get('url', ''),
                        "source": source_name,
                        "published_at": article.get('published'),
                        "scraped_at": article.get('scraped_at'),
                        "tags": tags,
                        "sentiment": None,
                        "sentiment_score": None,
                        "yfin_symbol": yfin_symbol,
                        "stock_name": stock.get('stock_name', ''),
                        "published_date": published_date_str
                    }
                    all_candidates.append(rss_news_data)
                    
                stock_news.extend(rss_news)
                
            except Exception as e:
                logger.error(f"Error with RSS feeds for {id}: {e}")
            
            # Google News HTML scraping fallback
            if len(stock_news) < 1:  
                logger.info(f"  -> Supplementing with Google News HTML scraping for {id}")
                for kw in keywords:
                    if len(kw.strip()) <= 2:
                        continue
                    try:
                        news = fetch_stock_news(kw)
                    except Exception as e:
                        logger.error(f"Error fetching Google News for keyword '{kw}': {e}")
                        continue
                    logger.info(f"  -> {len(news)} articles found for keyword '{kw}' from Google News")
                    found += len(news)
                    
                    filtered_news = []
                    for article in news:
                        article_text = f"{article.get('title', '')}\n{article.get('summary', '')}"
                        is_relevant, matched_kws, rel_score = enhanced_keyword_matching(article_text, [kw])
                        if is_relevant and rel_score >= 2:
                            article['matched_keywords'] = matched_kws
                            article['relevance_score'] = rel_score
                            filtered_news.append(article)
                    
                    for article in filtered_news:
                        title = article.get('title')
                        if not title or not str(title).strip():
                            summary = article.get('summary')
                            if summary and str(summary).strip():
                                title = summary
                            else:
                                title = None
                        
                        published_date_str = None
                        try:
                            pub_at = article.get('published')
                            if pub_at:
                                parsed_date = dateutil_parser.parse(pub_at)
                                published_date_str = parsed_date.date().isoformat()
                            else:
                                published_date_str = datetime.now().date().isoformat()
                        except Exception as e:
                            logger.error(f"Error parsing Google News published_date '{article.get('published')}': {e}")
                            published_date_str = "1970-01-01"
                            
                        # Date Filtering
                        try:
                            article_date = datetime.fromisoformat(published_date_str).date()
                            if article_date < (datetime.now().date() - timedelta(days=15)):
                                continue
                        except Exception as de:
                            logger.error(f"Error filtering by date: {de}")
 
                        tags = article.get('matched_keywords', [kw]) + ["news", "google_news"]
                        if article.get('relevance_score', 0) >= 3:
                            tags.append("relevance:high")
 
                        gnews_data = {
                            "stock_id": id,
                            "title": title,
                            "content": clean_html_content(article.get('content') or article.get('summary') or ''),
                            "url": article.get('url', ''),
                            "source": article.get('source', 'gnews'),
                            "published_at": article.get('published'),
                            "scraped_at": article.get('scraped_at'),
                            "tags": tags,
                            "sentiment": None,
                            "sentiment_score": None,
                            "yfin_symbol": yfin_symbol,
                            "stock_name": stock.get('stock_name', ''),
                            "published_date": published_date_str
                        }
                        if not gnews_data['title'] or not str(gnews_data['title']).strip():
                            continue
                        all_candidates.append(gnews_data)
                    stock_news.extend(filtered_news)
            
            stock_reports[id] = {"found": found, "inserted": 0, "skipped": 0, "stock_news_len": len(stock_news)}

        # 2. Batch check existing news in database
        logger.info(f"Batch checking duplicates for {len(all_candidates)} candidates in Supabase...")
        existing_urls = set()
        existing_titles = set()
        
        candidate_urls = [art['url'].strip() for art in all_candidates if art.get('url')]
        candidate_titles = [art['title'].strip() for art in all_candidates if art.get('title')]
        candidate_symbols = list(set(art['yfin_symbol'] for art in all_candidates))
        
        if candidate_urls or candidate_titles:
            try:
                from utilities.load_keywords_scrape import get_supabase_client
                supabase = get_supabase_client()
                
                # Query by URLs
                if candidate_urls:
                    res_url = supabase.table('news').select('url, yfin_symbol').in_('url', candidate_urls).in_('yfin_symbol', candidate_symbols).execute()
                    if res_url.data:
                        for row in res_url.data:
                            if row.get('url'):
                                existing_urls.add((row['url'].strip(), row['yfin_symbol']))
                                
                # Query by Titles
                if candidate_titles:
                    res_title = supabase.table('news').select('title, yfin_symbol').in_('title', candidate_titles).in_('yfin_symbol', candidate_symbols).execute()
                    if res_title.data:
                        for row in res_title.data:
                            if row.get('title'):
                                existing_titles.add((row['title'].strip(), row['yfin_symbol']))
            except Exception as e:
                logger.error(f"Error batch fetching existing news: {e}")
                
        # 3. Deduplicate in-memory
        to_insert = []
        for art in all_candidates:
            url = art.get('url', '').strip()
            title = art.get('title', '').strip()
            sym = art['yfin_symbol']
            stock_id = art['stock_id']
            
            is_dup = False
            if url and (url, sym) in existing_urls:
                is_dup = True
            elif title and (title, sym) in existing_titles:
                is_dup = True
                
            if is_dup:
                stock_reports[stock_id]['skipped'] += 1
                total_skipped += 1
            else:
                to_insert.append(art)
                stock_reports[stock_id]['inserted'] += 1
                total_inserted += 1
                
        # 4. Perform a single batch insert!
        if to_insert:
            logger.info(f"Batch inserting {len(to_insert)} new articles to Supabase...")
            try:
                supabase = get_supabase_client()
                supabase.table('news').insert(to_insert).execute()
                logger.info(f"✅ Successfully batch inserted {len(to_insert)} articles.")
            except Exception as e:
                logger.error(f"❌ Error during batch insert: {e}")
                logger.info("Falling back to one-by-one insert...")
                for art in to_insert:
                    try:
                        supabase.table('news').insert(art).execute()
                    except Exception as fe:
                        logger.error(f"Failed to insert single article: {fe}")
        else:
            logger.info("No new articles to insert.")
            
        total_found = sum(r['found'] for r in stock_reports.values())
        
        # 5. Output report summary compatible with orchestrator
        for stock in stocks:
            id = stock['id']
            sym = stock['yfin_symbol']
            report = stock_reports.get(id, {'inserted': 0, 'skipped': 0, 'stock_news_len': 0})
            insert_report[id] = {"inserted": report['inserted'], "skipped": report['skipped']}
            news_count_per_stock[id] = report['stock_news_len']
            
        logger.info(f"\nTOTAL: Found={total_found}, Inserted={total_inserted}, Skipped={total_skipped}")
        
        # Output metrics for the orchestrator to capture
        metrics_summary = {}
        for stock in stocks:
            sym = stock['yfin_symbol']
            report = insert_report.get(stock['id'], {'inserted': 0, 'skipped': 0})
            metrics_summary[sym] = f"inserted:{report['inserted']} skipped:{report['skipped']}"
        
        print(f"\nMETRICS: {json.dumps(metrics_summary)}")

        logger.info("\nSummary: News articles per stock:")
        for stock_id, count in news_count_per_stock.items():
            logger.info(f"{stock_id}: {count}")
        logger.info("\nInsert/Skip Report per stock:")
    except Exception as e:
        with open(error_log_file, "a", encoding="utf-8") as ef:
            ef.write(f"[FATAL ERROR] {datetime.now().isoformat()} - {str(e)}\n")
        print(f"[FATAL ERROR] {str(e)}")

if __name__ == "__main__":
    main()
