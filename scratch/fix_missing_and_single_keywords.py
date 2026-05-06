import os
import json
from dotenv import load_dotenv
from supabase import create_client
from collections import defaultdict

def get_prefixes(name, num_words):
    name_clean = name.strip()
    if name_clean.lower().startswith('the '):
        name_clean = name_clean[4:].strip()
    words = name_clean.split()
    if len(words) <= num_words:
        return name_clean
    return " ".join(words[:num_words])

def fix_keywords():
    load_dotenv(r'd:\sentimatix\worker-SCRAPE\stock-news\x-news\.env')
    supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

    # ── Fix 1: Stocks with NO keywords ──────────────────────────────────────
    missing_kw_symbols = [
        'ASAHISONG.NS', 'ATLASCYCLE.NS', 'CHAMBLFERT.NS',
        'COMSYN.NS', 'MINDACORP.NS', 'PARAS.NS'
    ]

    print("=== FIX 1: Stocks with no keywords ===")
    res = supabase.table('stocks').select('id,yfin_symbol,stock_name').in_('yfin_symbol', missing_kw_symbols).execute()

    for stock in res.data:
        symbol = stock['yfin_symbol']
        name = stock['stock_name']
        short = symbol.replace('.NS', '')

        # Build a smart default: full name + 2-word prefix + symbol
        p2 = get_prefixes(name, 2)
        p3 = get_prefixes(name, 3)

        kws = list(dict.fromkeys([name, p3, p2, short]))  # dedup, keep order
        new_value = {"keyword": kws}

        print(f"[{symbol}] {name} -> keywords: {kws}")
        supabase.table('stocks').update({'keyword_lst': json.dumps(new_value)}).eq('id', stock['id']).execute()

    print(f"\n✅ Fixed {len(res.data)} stocks with no keywords.\n")

    # ── Fix 2: Find all 1-word keywords and expand them ─────────────────────
    print("=== FIX 2: Finding single-word keywords ===")

    all_stocks = []
    page_size = 1000
    offset = 0
    while True:
        r = supabase.table('stocks').select('id,yfin_symbol,stock_name,keyword_lst').eq('is_active', True).range(offset, offset + page_size - 1).execute()
        if not r.data: break
        all_stocks.extend(r.data)
        if len(r.data) < page_size: break
        offset += page_size

    single_word_kw_stocks = []
    
    for stock in all_stocks:
        symbol = stock['yfin_symbol']
        name = stock.get('stock_name', '')
        raw = stock.get('keyword_lst')
        if not raw: continue

        try:
            parsed = raw if isinstance(raw, dict) else json.loads(raw)
            kws = parsed.get('keyword', []) if isinstance(parsed, dict) else []
        except:
            continue

        # Find single-word keywords
        single_words = [k for k in kws if k and ' ' not in str(k).strip() and len(str(k).strip()) > 1]
        
        if single_words:
            single_word_kw_stocks.append((stock, kws, single_words))

    print(f"Stocks with at least one single-word keyword: {len(single_word_kw_stocks)}")
    
    # Preview first 20
    for stock, kws, singles in single_word_kw_stocks[:20]:
        print(f"  [{stock['yfin_symbol']}] Single-word kws: {singles} | Full: {kws}")

    # ── Fix 2b: Expand single-word keywords that are just the first word of company name ──
    print("\n=== FIX 2b: Expanding inadequate single-word keywords ===")
    
    # Rules for symbols/acronyms that should be KEPT as-is (uppercase, ≤5 chars)
    def is_ticker_like(kw):
        return kw.isupper() and len(kw) <= 6

    fixed_count = 0
    for stock, kws, single_words in single_word_kw_stocks:
        symbol = stock['yfin_symbol']
        name = stock.get('stock_name', '')
        short = symbol.replace('.NS', '')

        new_kws = list(kws)  # start from existing
        changed = False

        for kw in single_words:
            kw_lower = kw.lower()
            # Keep if it's a ticker-like symbol (e.g., TCS, RELIANCE, ITC)
            if is_ticker_like(kw):
                continue
            # Keep if it matches the NSE symbol (short form)
            if kw_lower == short.lower():
                continue
            
            # This single word is likely a name-fragment — replace it with 2-word prefix
            name_clean = name.strip()
            if name_clean.lower().startswith('the '):
                name_clean = name_clean[4:].strip()
            
            # Only remove if this single word matches the first word of company name
            first_word = name_clean.split()[0].lower() if name_clean else ''
            if kw_lower == first_word:
                # Remove it — it'll be replaced by the prefix
                new_kws = [k for k in new_kws if k != kw]
                changed = True

        # Ensure the 2-word prefix and 3-word prefix are there
        p2 = get_prefixes(name, 2)
        p3 = get_prefixes(name, 3)
        for prefix in [p2, p3]:
            if prefix and prefix.lower() not in [k.lower() for k in new_kws]:
                new_kws.append(prefix)
                changed = True

        # Always ensure symbol is present
        if short.lower() not in [k.lower() for k in new_kws]:
            new_kws.append(short)
            changed = True

        new_kws = list(dict.fromkeys(new_kws))

        if changed:
            fixed_count += 1
            print(f"  [{symbol}] {kws} -> {new_kws}")
            supabase.table('stocks').update({'keyword_lst': json.dumps({"keyword": new_kws})}).eq('id', stock['id']).execute()

    print(f"\n✅ Fixed {fixed_count} stocks with inadequate single-word keywords.")

    # ── Final summary of remaining single-word keywords (that we intentionally kept) ──
    print("\n=== REMAINING single-word keywords (intentionally kept - ticker symbols) ===")
    kept_singles = []
    for stock, kws, singles in single_word_kw_stocks:
        still_single = [k for k in singles if is_ticker_like(k) or k.lower() == stock['yfin_symbol'].replace('.NS', '').lower()]
        if still_single:
            kept_singles.append((stock['yfin_symbol'], still_single))
    print(f"  Count: {len(kept_singles)} (these are all ticker symbols — intentional)")

if __name__ == "__main__":
    fix_keywords()
