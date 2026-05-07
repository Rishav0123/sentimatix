import json
from collections import Counter

try:
    with open('temp_stock_kws.json', 'r') as f:
        stocks = json.load(f)
except FileNotFoundError:
    print("Run the fetch script first.")
    exit(1)

single_word_kws = []
for s in stocks:
    kws = s.get('keyword_lst')
    if not kws: continue
    
    # parse
    if isinstance(kws, str):
        try:
            kws = json.loads(kws)
        except:
            continue
    if isinstance(kws, dict) and 'keyword' in kws:
        kws = kws['keyword']
    elif not isinstance(kws, list):
        continue
        
    for kw in kws:
        kw = str(kw).strip()
        # if it's a single word (no spaces)
        if ' ' not in kw and len(kw) > 0:
            single_word_kws.append((kw, s['yfin_symbol']))

counts = Counter([k.lower() for k, sym in single_word_kws])

generic_suspects = {
    'the', 'and', 'ltd', 'limited', 'inc', 'corp', 'corporation', 'co', 'company',
    'bank', 'india', 'indian', 'asian', 'global', 'international', 'national',
    'steel', 'power', 'energy', 'finance', 'capital', 'holdings', 'group',
    'enterprises', 'industries', 'technologies', 'services', 'solutions', 'systems',
    'network', 'media', 'food', 'agro', 'pharma', 'chem', 'cement', 'motors',
    'auto', 'textiles', 'retail', 'hotels', 'infra', 'engineering', 'projects',
    'logistics', 'shipping', 'marine', 'financial', 'mutual', 'insurance',
    'health', 'medical', 'digital', 'tech', 'telecom', 'entertainment',
    'chemicals', 'metals', 'electronics', 'consumer', 'city', 'star',
    'royal', 'king', 'smart', 'expert', 'master', 'pro', 'first', 'best',
    'top', 'premium', 'prime', 'core', 'base', 'root', 'source', 'cloud',
    'data', 'info', 'cyber', 'virtual', 'real', 'true', 'pure', 'clear',
    'bright', 'shine', 'glow', 'spark', 'flash', 'light', 'sun', 'moon',
    'sky', 'earth', 'land', 'water', 'air', 'fire', 'wind', 'storm', 'rain',
    'green', 'blue', 'red', 'white', 'black', 'gold', 'silver', 'diamond',
    'new', 'old', 'modern', 'classic', 'vintage', 'retro', 'future', 'next',
    'now', 'today', 'tomorrow', 'fast', 'quick', 'speed', 'rapid', 'swift',
    'slow', 'steady', 'safe', 'secure', 'guard', 'shield', 'protect', 'defend',
    'save', 'keep', 'hold', 'catch', 'grab', 'take', 'get', 'have', 'own',
    'share', 'give', 'send', 'receive', 'accept', 'bring', 'carry', 'move',
    'go', 'come', 'stay', 'wait', 'stop', 'start', 'begin', 'end', 'finish',
    'complete', 'done', 'ready', 'set', 'empower', 'prakash', 'shree', 'sri',
    'jai', 'hind', 'bharat', 'hindustan', 'oriental', 'occidental', 'northern',
    'southern', 'eastern', 'western', 'central', 'pacific', 'atlantic', 'european',
    'american', 'african', 'universal', 'cosmic', 'galaxy', 'nova', 'apex',
    'zenith', 'summit', 'peak', 'crest', 'majestic', 'grand', 'super', 'mega',
    'ultra', 'max', 'plus', 'advance', 'intelligent', 'brilliant', 'genius',
    'champion', 'hero', 'leader', 'pioneer', 'choice', 'select', 'elite',
    'nexus', 'link', 'connect', 'grid', 'matrix', 'web', 'net'
}

suspects_found = []
for (kw, sym) in single_word_kws:
    if kw.lower() in generic_suspects or len(kw) <= 2:
        suspects_found.append((kw, sym))

print(f'Total single words: {len(single_word_kws)}')
print(f'Generic suspect keywords found: {len(suspects_found)}')
print('Examples of bad keywords found:')
seen = set()
for kw, sym in suspects_found:
    if kw.lower() not in seen:
        print(f'- "{kw}" (used by {sym})')
        seen.add(kw.lower())
    if len(seen) >= 20: break

# Count how many total unique bad ones we found
print(f"\nTotal unique bad keywords found: {len(seen)}")
