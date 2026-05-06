import os
import json
import yfinance as yf
from dotenv import load_dotenv
from supabase import create_client

load_dotenv(r'd:\sentimatix\worker-SCRAPE\stock-news\x-news\.env')
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

def get_prefixes(name, num_words):
    name_clean = name.strip()
    if name_clean.lower().startswith('the '):
        name_clean = name_clean[4:].strip()
    words = name_clean.split()
    if len(words) <= num_words:
        return name_clean
    return " ".join(words[:num_words])

MISSING_STOCKS = {
    'ZOMATO.NS': 'Zomato Limited',
    'HAPPYMIND.NS': 'Happiest Minds Technologies Limited',
    'MAZAGON.NS': 'Mazagon Dock Shipbuilders Limited',
}

# Sector mapping hints for known stocks
SECTOR_HINTS = {
    'ZOMATO.NS': 'Consumer Cyclical',
    'NYKAA.NS': 'Consumer Cyclical',
    'PAYTM.NS': 'Technology',
    'SWIGGY.NS': 'Consumer Cyclical',
    'POLICYBZR.NS': 'Financial Services',
    'MAPMYINDIA.NS': 'Technology',
    'IXIGO.NS': 'Consumer Cyclical',
    'OLAELEC.NS': 'Consumer Cyclical',
    'MOBIKWIK.NS': 'Financial Services',
    'IRFC.NS': 'Financial Services',
    'RVNL.NS': 'Industrials',
    'NHPC.NS': 'Utilities',
    'SJVN.NS': 'Utilities',
    'RECLTD.NS': 'Financial Services',
    'PFC.NS': 'Financial Services',
    'IREDA.NS': 'Financial Services',
    'MAZAGON.NS': 'Industrials',
    'MIDHANI.NS': 'Industrials',
}

# Brand name aliases for search
BRAND_ALIASES = {
    'ZOMATO.NS': 'Zomato',
    'NYKAA.NS': 'Nykaa',
    'PAYTM.NS': 'Paytm',
    'SWIGGY.NS': 'Swiggy',
    'POLICYBZR.NS': 'PolicyBazaar',
    'MAPMYINDIA.NS': 'MapMyIndia',
    'IXIGO.NS': 'ixigo',
    'OLAELEC.NS': 'Ola Electric',
    'MOBIKWIK.NS': 'MobiKwik',
    'HAPPYMIND.NS': 'Happiest Minds',
    'RECLTD.NS': 'REC',
    'IRFC.NS': 'IRFC',
    'RVNL.NS': 'RVNL',
    'NHPC.NS': 'NHPC',
    'SJVN.NS': 'SJVN',
    'PFC.NS': 'PFC',
    'IREDA.NS': 'IREDA',
    'MAZAGON.NS': 'Mazagon Dock',
    'LODHA.NS': 'Lodha',
    'MANKIND.NS': 'Mankind Pharma',
    'WESTLIFE.NS': "McDonald's India",
}

added = 0
skipped = 0

for symbol, default_name in MISSING_STOCKS.items():
    short = symbol.replace('.NS', '')

    # Try to fetch metadata from yfinance
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.fast_info
        name = getattr(info, 'company_name', None) or default_name
        sector = SECTOR_HINTS.get(symbol, 'Unknown')
        exchange = 'NSE'
        country = 'India'
    except Exception as e:
        name = default_name
        sector = SECTOR_HINTS.get(symbol, 'Unknown')
        exchange = 'NSE'
        country = 'India'

    # Build smart keywords
    p2 = get_prefixes(name, 2)
    p3 = get_prefixes(name, 3)
    kws = [name, p3, p2, short]
    alias = BRAND_ALIASES.get(symbol)
    if alias and alias.lower() not in [k.lower() for k in kws]:
        kws.append(alias)
    kws = list(dict.fromkeys(kws))  # dedup preserve order

    row = {
        'yfin_symbol': symbol,
        'stock_name': name,
        'sector': sector,
        'exchange': exchange,
        'country': country,
        'is_active': True,
        'keyword_lst': json.dumps({"keyword": kws}),
        'mc_link_1': '',
        'mc_link_2': '',
    }

    try:
        # Check if it somehow exists (edge case)
        existing = supabase.table('stocks').select('id').eq('yfin_symbol', symbol).execute()
        if existing.data:
            print(f"[SKIP] {symbol} already exists")
            skipped += 1
            continue

        supabase.table('stocks').insert(row).execute()
        print(f"[ADDED] {symbol} | {name} | kws: {kws}")
        added += 1
    except Exception as e:
        print(f"[ERROR] {symbol}: {e}")

print(f"\nDone. Added: {added}, Skipped: {skipped}")
