import os
import json
from collections import defaultdict
from dotenv import load_dotenv
from supabase import create_client

def analyze_all():
    load_dotenv(r'd:\sentimatix\worker-SCRAPE\stock-news\x-news\.env')
    supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

    # Fetch all active stocks with keyword data
    print("Fetching stocks...")
    all_stocks = []
    page_size = 1000
    offset = 0
    while True:
        res = supabase.table('stocks').select('id,yfin_symbol,stock_name,keyword_lst,is_active').eq('is_active', True).range(offset, offset + page_size - 1).execute()
        if not res.data: break
        all_stocks.extend(res.data)
        if len(res.data) < page_size: break
        offset += page_size

    print(f"Fetching recent news coverage per stock...")
    # Get news counts per stock via yfin_symbol
    news_res = supabase.table('news').select('yfin_symbol').execute()
    news_count_by_symbol = defaultdict(int)
    for n in news_res.data:
        if n.get('yfin_symbol'):
            news_count_by_symbol[n['yfin_symbol']] += 1

    # ── Analysis categories ──
    no_keywords = []            # Stocks with no keyword_lst at all
    only_symbol = []            # Keywords = just the symbol/ticker
    only_full_name = []         # Keywords = just the full company name
    too_many_keywords = []      # > 5 keywords (over-specified or redundant)
    single_keyword = []         # Only 1 keyword (likely underpowered)
    two_keywords = []           # 2 keywords
    good_keywords = []          # 3-5 keywords (sweet spot)
    zero_news = []              # Active but got 0 news ever
    low_news = []               # 1-5 articles ever
    high_coverage = []          # 50+ articles

    all_kw_set = set()
    kw_count_distribution = defaultdict(int)
    
    for stock in all_stocks:
        symbol = stock['yfin_symbol']
        stock_id = stock['id']
        name = stock.get('stock_name', '')
        raw = stock.get('keyword_lst')

        news_count = news_count_by_symbol.get(symbol, 0)

        kws = []
        if raw:
            try:
                parsed = raw if isinstance(raw, dict) else json.loads(raw)
                if isinstance(parsed, dict) and 'keyword' in parsed:
                    kws = [str(k).strip() for k in parsed['keyword'] if str(k).strip()]
            except:
                pass

        kw_count_distribution[len(kws)] += 1
        for k in kws:
            all_kw_set.add(k.lower())

        if not kws:
            no_keywords.append((symbol, name, news_count))
        elif len(kws) == 1:
            single_keyword.append((symbol, name, kws, news_count))
        elif len(kws) == 2:
            two_keywords.append((symbol, name, kws, news_count))
        elif 3 <= len(kws) <= 5:
            good_keywords.append((symbol, name, kws, news_count))
        elif len(kws) > 5:
            too_many_keywords.append((symbol, name, kws, news_count))

        if news_count == 0:
            zero_news.append((symbol, name, kws))
        elif news_count <= 5:
            low_news.append((symbol, name, news_count))
        elif news_count >= 50:
            high_coverage.append((symbol, name, news_count))

    # ── Write Report ──
    out = []
    out.append("# Full Stock & Keyword Health Report\n")
    out.append(f"Total active stocks: {len(all_stocks)}")
    out.append(f"Total unique keywords (lowercase): {len(all_kw_set)}\n")

    out.append("## Keyword Count Distribution")
    for n in sorted(kw_count_distribution.keys()):
        out.append(f"  {n} keywords: {kw_count_distribution[n]} stocks")

    out.append(f"\n## News Coverage Summary")
    out.append(f"  Stocks with ZERO news: {len(zero_news)}")
    out.append(f"  Stocks with 1-5 news articles: {len(low_news)}")
    out.append(f"  Stocks with 50+ news articles: {len(high_coverage)}")

    out.append(f"\n## Problem Categories")
    out.append(f"  No keywords at all: {len(no_keywords)}")
    out.append(f"  Only 1 keyword (underpowered): {len(single_keyword)}")
    out.append(f"  2 keywords (marginal): {len(two_keywords)}")
    out.append(f"  3-5 keywords (sweet spot): {len(good_keywords)}")
    out.append(f"  6+ keywords (over-specified): {len(too_many_keywords)}")

    out.append(f"\n## Stocks with NO Keywords")
    for sym, name, nc in sorted(no_keywords):
        out.append(f"  {sym} | {name} | news: {nc}")

    out.append(f"\n## Stocks with Only 1 Keyword")
    for sym, name, kws, nc in sorted(single_keyword):
        out.append(f"  {sym} | {name} | kw: {kws} | news: {nc}")

    out.append(f"\n## Stocks with 6+ Keywords (potentially bloated)")
    for sym, name, kws, nc in sorted(too_many_keywords, key=lambda x: len(x[2]), reverse=True):
        out.append(f"  {sym} | {name} | {len(kws)} kws | news: {nc}")

    out.append(f"\n## Zero-News Active Stocks (top 50)")
    for sym, name, kws in sorted(zero_news)[:50]:
        out.append(f"  {sym} | {name} | kws: {len(kws)}")

    report = "\n".join(out)
    print(report)

    with open(r'd:\sentimatix\scratch\stock_keyword_health.md', 'w', encoding='utf-8') as f:
        f.write(report)
    print("\nReport saved to d:\\sentimatix\\scratch\\stock_keyword_health.md")

if __name__ == "__main__":
    analyze_all()
