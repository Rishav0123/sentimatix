import os
import json
from dotenv import load_dotenv
from supabase import create_client

def get_prefixes(name, num_words):
    name_clean = name.strip()
    if name_clean.lower().startswith('the '):
        name_clean = name_clean[4:].strip()
    words = name_clean.split()
    if len(words) <= num_words:
        return name_clean
    return " ".join(words[:num_words])

load_dotenv(r'd:\sentimatix\workers/scrape\stock-news\x-news\.env')
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

missing_kw_symbols = [
    'ASAHISONG.NS', 'ATLASCYCLE.NS', 'CHAMBLFERT.NS',
    'COMSYN.NS', 'MINDACORP.NS', 'PARAS.NS'
]

res = supabase.table('stocks').select('id,yfin_symbol,stock_name').in_('yfin_symbol', missing_kw_symbols).execute()

for stock in res.data:
    symbol = stock['yfin_symbol']
    name = stock['stock_name']
    short = symbol.replace('.NS', '')
    p2 = get_prefixes(name, 2)
    p3 = get_prefixes(name, 3)
    kws = list(dict.fromkeys([name, p3, p2, short]))
    new_value = {"keyword": kws}
    print(f"[{symbol}] -> {kws}")
    supabase.table('stocks').update({'keyword_lst': json.dumps(new_value)}).eq('id', stock['id']).execute()

print(f"\nDone. Fixed {len(res.data)} stocks.")
