import requests
import re
from bs4 import BeautifulSoup
import json
from datetime import datetime
import feedparser
import html
 
import logging
import re
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent / 'utilities'))
from utilities.load_keywords_scrape import fetch_stock_keywords
from utilities.check_existing_news import check_existing_news
from utilities.store_news_article import store_news_article
from datetime import datetime

# Fallback Google News URL (now secondary option)
GOOGLE_NEWS_URL = f"https://news.google.com/search?q={{stock}}+finance+india+{{date}}&hl=en-IN&gl=IN&ceid=IN:en"

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

def fetch_stock_news_direct_rss(keywords, max_articles_per_source=20):
    """
    Fetch stock news from direct RSS feeds that provide actual article URLs
    This is the PRIMARY method that provides real article URLs
    """
    all_articles = []
    
    for source_name, rss_url in RSS_SOURCES.items():
        try:
            # Add timeout and better error handling
            import socket
            socket.setdefaulttimeout(10)  # 10 second timeout
            
            feed = feedparser.parse(rss_url)
            
            # Check if feed was parsed successfully
            if not hasattr(feed, 'entries') or not feed.entries:
                logging.warning(f"No entries found for {source_name} - {rss_url}")
                continue
                
        except Exception as e:
            logging.error(f"Error fetching from {source_name} ({rss_url}): {e}")
            continue
        
        try:
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
                
                # Filter for stock/finance related content
                title_lower = article['title'].lower()
                summary_lower = article['summary'].lower()
                
                # Stock/finance keywords to filter relevant articles
                finance_keywords = [
                    'stock', 'market', 'share', 'nifty', 'sensex', 'bse', 'nse',
                    'equity', 'trading', 'investment', 'profit', 'loss', 'earning',
                    'revenue', 'financial', 'rupee', 'currency', 'economy',
                    'fund', 'ipo', 'dividend', 'quarter', 'q1', 'q2', 'q3', 'q4',
                    'fiscal', 'budget', 'inflation', 'gdp', 'rbi', 'sebi',
                    'mutual fund', 'portfolio', 'bullish', 'bearish', 'buyback'
                ]
                
                # Check if article is finance-related or matches keywords
                is_relevant = False
                
                # Check against finance keywords
                if any(keyword in title_lower for keyword in finance_keywords) or \
                   any(keyword in summary_lower for keyword in finance_keywords):
                    is_relevant = True
                
                # Check against user's stock keywords
                if keywords:
                    for keyword in keywords:
                        if keyword.lower() in title_lower or keyword.lower() in summary_lower:
                            is_relevant = True
                            break
                
                if is_relevant and article['url'] and article['title']:
                    # Add metadata for tracking
                    article['scraped_at'] = datetime.now().isoformat()
                    all_articles.append(article)
                    
        except Exception as e:
            logging.error(f"Error processing entries from {source_name}: {e}")
            continue
    
    # Sort by publication date (newest first)
    def parse_date(date_str):
        try:
            if date_str:
                # Try different date formats
                for fmt in ['%a, %d %b %Y %H:%M:%S %z', '%Y-%m-%dT%H:%M:%S%z', '%Y-%m-%d %H:%M:%S']:
                    try:
                        return datetime.strptime(date_str.split('+')[0].strip(), fmt.replace('%z', ''))
                    except:
                        continue
            return datetime.min
        except:
            return datetime.min
    
    all_articles.sort(key=lambda x: parse_date(x['published']), reverse=True)
    
    # Remove duplicates based on URL
    seen_urls = set()
    unique_articles = []
    
    for article in all_articles:
        if article['url'] not in seen_urls:
            seen_urls.add(article['url'])
            unique_articles.append(article)
            
    return unique_articles

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
    
    for item in soup.select("article"):
        # Try multiple selectors for title
        title_tag = (item.select_one("h3 a") or 
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
            source = source_from_text or 'gnews'
        
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
            "url": full_url,
            "published": published_time,
            "scraped_at": datetime.now().isoformat()
        })
    
    return articles



def save_news(news, filename="article.json"):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(news, f, ensure_ascii=False, indent=2)



def main():
    # Setup logging to logs/gnews_{date}.log and error logging to logs/gnews_error_{date}.log
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / f"gnews_{datetime.now().strftime('%Y%m%d')}.log"
    error_log_file = log_dir / f"gnews_error_{datetime.now().strftime('%Y%m%d')}.log"
    # Set up logging with UTF-8 encoding for all handlers
    logger = logging.getLogger(__name__)
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
        stocks = fetch_stock_keywords()
        if not stocks:
            logger.info("No active stocks found in database")
            return
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
            inserted = 0
            skipped = 0
            found = 0
            logger.info(f"Fetching news for {id} using keywords: {keywords}")
            
            # PRIMARY METHOD: Direct RSS feeds (provides actual article URLs)
            try:
                logger.info(f"  -> Using DIRECT RSS feeds for {id}")
                rss_news = fetch_stock_news_direct_rss(keywords, max_articles_per_source=50)  # Increased to 50 for more comprehensive coverage
                logger.info(f"  -> {len(rss_news)} articles found from RSS feeds")
                found += len(rss_news)
                
                # Process RSS articles
                for article in rss_news:
                    # Enhanced keyword matching with word boundaries and context awareness
                    article_text = f"{article.get('title', '')} {article.get('summary', '')}".lower()
                    keyword_match = False
                    matched_keywords = []
                    
                    for kw in keywords:
                        kw_lower = kw.lower().strip()
                        
                        # Skip very short keywords (1-2 chars) as they cause too many false positives
                        if len(kw_lower) <= 2:
                            logger.debug(f"Skipping very short keyword '{kw}' (length <= 2)")
                            continue
                        
                        # For short keywords (3-4 chars), use strict word boundary matching
                        if len(kw_lower) <= 4:
                            # Use word boundaries to avoid partial matches (e.g., "RIL" in "trillion")
                            pattern = r'\b' + re.escape(kw_lower) + r'\b'
                            if re.search(pattern, article_text):
                                # Additional context check for financial relevance
                                if is_financially_relevant_context(article_text, kw_lower):
                                    keyword_match = True
                                    matched_keywords.append(kw)
                                    logger.debug(f"✅ Strict match found for short keyword '{kw}' with financial context")
                                    break
                                else:
                                    logger.debug(f"⚠️ Keyword '{kw}' found but lacks financial context")
                        
                        # For medium keywords (5-8 chars), use word boundary but allow some flexibility
                        elif len(kw_lower) <= 8:
                            pattern = r'\b' + re.escape(kw_lower) + r'\b'
                            if re.search(pattern, article_text):
                                keyword_match = True
                                matched_keywords.append(kw)
                                logger.debug(f"✅ Medium keyword match found for '{kw}'")
                                break
                            # Also check for partial matches within compound words (e.g., "Axis" in "AxisBank")
                            elif kw_lower in article_text:
                                if is_financially_relevant_context(article_text, kw_lower):
                                    keyword_match = True
                                    matched_keywords.append(kw)
                                    logger.debug(f"✅ Partial match found for medium keyword '{kw}' with financial context")
                                    break
                        
                        # For longer keywords (9+ chars), allow partial matches but verify context
                        else:
                            if kw_lower in article_text:
                                if is_financially_relevant_context(article_text, kw_lower):
                                    keyword_match = True
                                    matched_keywords.append(kw)
                                    logger.debug(f"✅ Long keyword match found for '{kw}' with financial context")
                                    break
                                else:
                                    logger.debug(f"⚠️ Long keyword '{kw}' found but lacks financial context")
                    
                    if not keyword_match:
                        logger.debug(f"❌ No valid keyword matches found for article: {article.get('title', '')[:50]}...")
                        continue
                        
                    title = article.get('title')
                    if not title or not str(title).strip():
                        summary = article.get('summary')
                        if summary and str(summary).strip():
                            title = summary
                        else:
                            continue
                    
                    logger.info(f"Processing RSS article: title={title}, url={article.get('url')}, source={article.get('source')}")
                    
                    try:
                        if check_existing_news(title, article.get('published'), yfin_symbol):
                            skipped += 1
                            continue
                    except Exception as e:
                        logger.error(f"Network/API error checking for existing RSS news: {e}")
                        skipped += 1
                        continue
                    
                    # Parse published_date
                    published_date_str = None
                    try:
                        if article.get('published'):
                            # Try to parse RSS date format
                            from dateutil import parser
                            parsed_date = parser.parse(article.get('published'))
                            published_date_str = parsed_date.date().isoformat()
                        else:
                            published_date_str = datetime.now().date().isoformat()
                    except Exception as e:
                        logger.error(f"Error parsing RSS published_date: {e}")
                        published_date_str = datetime.now().date().isoformat()
                    
                    # Extract source name (remove "- Markets" etc. suffixes)
                    source_name = article.get('source', 'RSS Feed')
                    if ' - ' in source_name:
                        source_name = source_name.split(' - ')[0]
                    
                    rss_news_data = {
                        "id": id,
                        "title": title,
                        "content": clean_html_content(article.get('content') or article.get('summary') or ''),
                        "url": article.get('url', ''),  # ACTUAL ARTICLE URL!
                        "source": source_name,
                        "published_at": article.get('published'),
                        "scraped_at": article.get('scraped_at'),
                        "tags": matched_keywords + ["news", "rss"],  # Use only matched keywords
                        "sentiment": None,
                        "sentiment_score": None,
                        "yfin_symbol": yfin_symbol,
                        "published_date": published_date_str
                    }
                    
                    logger.debug(f"Inserting RSS news_data: {rss_news_data}")
                    try:
                        store_news_article(rss_news_data)
                        inserted += 1
                        logger.info(f"✅ Successfully stored RSS article: {title[:50]}...")
                    except Exception as e:
                        logger.error(f"❌ Error storing RSS news article: {e}")
                        logger.error(f"Failed article data: {rss_news_data}")
                        skipped += 1
                        
                stock_news.extend(rss_news)
                
            except Exception as e:
                logger.error(f"Error with RSS feeds for {id}: {e}")
            
            # FALLBACK METHOD: Google News HTML scraping (if RSS didn't get enough results)
            if len(stock_news) < 5:  # If we got less than 5 articles from RSS, supplement with Google News
                logger.info(f"  -> Supplementing with Google News HTML scraping for {id}")
                for kw in keywords:
                    # Skip very short keywords for Google News too
                    if len(kw.strip()) <= 2:
                        logger.debug(f"Skipping very short keyword '{kw}' for Google News (length <= 2)")
                        continue
                        
                    try:
                        news = fetch_stock_news(kw)
                    except Exception as e:
                        logger.error(f"Error fetching Google News for keyword '{kw}': {e}")
                        continue
                    logger.info(f"  -> {len(news)} articles found for keyword '{kw}' from Google News")
                    found += len(news)
                    
                    # Enhanced filtering for Google News
                    filtered_news = []
                    for article in news:
                        article_text = f"{article.get('title', '')} {article.get('summary', '')}".lower()
                        kw_lower = kw.lower().strip()
                        
                        # Apply same improved matching logic
                        if len(kw_lower) <= 4:
                            # Strict word boundary matching for short keywords
                            pattern = r'\b' + re.escape(kw_lower) + r'\b'
                            if re.search(pattern, article_text):
                                if is_financially_relevant_context(article_text, kw_lower):
                                    filtered_news.append(article)
                                    logger.debug(f"✅ Google News: Strict match for '{kw}' with financial context")
                        else:
                            # More flexible matching for longer keywords
                            if kw_lower in article_text:
                                if is_financially_relevant_context(article_text, kw_lower):
                                    filtered_news.append(article)
                                    logger.debug(f"✅ Google News: Match found for '{kw}' with financial context")
                    
                    for article in filtered_news:
                        # Use summary as fallback for title if title is missing/empty
                        title = article.get('title')
                        if not title or not str(title).strip():
                            summary = article.get('summary')
                            if summary and str(summary).strip():
                                title = summary
                            else:
                                title = None
                        
                        logger.info(f"Processing Google News article: title={title}, url={article.get('url')}")
                        try:
                            if check_existing_news(title, article.get('published'), yfin_symbol):
                                skipped += 1
                                continue
                        except Exception as e:
                            logger.error(f"Network/API error checking for existing Google News: {e}")
                            skipped += 1
                            continue
                        # Parse published_date as ISO string, fallback to today if parsing fails
                        published_date_str = None
                        try:
                            if article.get('published'):
                                published_date_str = datetime.fromisoformat(article.get('published')).date().isoformat()
                            else:
                                published_date_str = datetime.now().date().isoformat()
                        except Exception as e:
                            logger.error(f"Error parsing Google News published_date: {e}")
                            published_date_str = datetime.now().date().isoformat()
                        gnews_data = {
                            "id": id,
                            "title": title,
                            "content": None,
                            "url": article.get('url', ''),  # NOTE: These are Google News redirect URLs
                            "source": article.get('source', 'gnews'),
                            "published_at": article.get('published'),
                            "scraped_at": article.get('scraped_at'),
                            "tags": [kw, "news", "google_news"],
                            "sentiment": None,
                            "sentiment_score": None,
                            "yfin_symbol": yfin_symbol,
                            "published_date": published_date_str
                        }
                        # Skip and log if title is still missing/empty after fallback
                        if not gnews_data['title'] or not str(gnews_data['title']).strip():
                            logger.error(f"Skipping Google News article with missing/empty title. Data: {gnews_data}")
                            skipped += 1
                            continue
                        logger.debug(f"Inserting Google News data: {gnews_data}")
                        try:
                            store_news_article(gnews_data)
                            inserted += 1
                        except Exception as e:
                            logger.error(f"Network/API error inserting Google News: {e}. Data: {gnews_data}")
                            skipped += 1
                    stock_news.extend(filtered_news)
            logger.info(f"Summary for stock {yfin_symbol}: Found={found}, Inserted={inserted}, Skipped={skipped}")
            total_found += found
            total_inserted += inserted
            total_skipped += skipped
            news_count_per_stock[id] = len(stock_news)
            all_news.extend(stock_news)
            insert_report[id] = {"inserted": inserted, "skipped": skipped}
        logger.info(f"\nTOTAL: Found={total_found}, Inserted={total_inserted}, Skipped={total_skipped}")
        logger.info("\nSummary: News articles per stock:")
        for stock_id, count in news_count_per_stock.items():
            logger.info(f"{stock_id}: {count}")
        logger.info("\nInsert/Skip Report per stock:")
        # for stock_id, report in insert_report.items():
        #     logger.info(f"{stock_id}: Inserted={report['inserted']}, Skipped={report['skipped']}")
        # if all_news:
        #     save_news(all_news)
        #     logger.info(f"\nSaved {len(all_news)} articles to article.json")
        # else:
        #     logger.info("No news articles found.")
    except Exception as e:
        # Log to error file and print to console if logging fails early
        with open(error_log_file, "a", encoding="utf-8") as ef:
            ef.write(f"[FATAL ERROR] {datetime.now().isoformat()} - {str(e)}\n")
        print(f"[FATAL ERROR] {str(e)}")

if __name__ == "__main__":
    main()
