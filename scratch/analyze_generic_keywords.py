import os
import json
from dotenv import load_dotenv
from supabase import create_client

def analyze_generic_keywords():
    load_dotenv(r'd:\sentimatix\worker-SCRAPE\stock-news\x-news\.env')
    supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

    print("Fetching keywords...")
    res = supabase.table('stocks').select('keyword_lst').eq('is_active', True).execute()
    
    all_kws = set()
    for r in res.data:
        lst = r.get('keyword_lst')
        if not lst: continue
        
        try:
            if isinstance(lst, str):
                lst = json.loads(lst)
            if isinstance(lst, dict) and 'keyword' in lst:
                for k in lst['keyword']:
                    all_kws.add(str(k).strip())
        except:
            continue

    generic_words = {
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
        'new', 'old', 'modern', 'classic', 'future', 'next', 'now', 'today',
        'fast', 'speed', 'rapid', 'safe', 'secure', 'guard', 'shield', 'protect',
        'all', 'any', 'some', 'many', 'this', 'that', 'such', 'what', 'which',
        'gujarat', 'tamilnadu', 'tamil', 'nadu', 'andhra', 'maharashtra', 'punjab',
        'karnataka', 'kerala', 'haryana', 'rajasthan', 'indianoil', 'industrial'
    }

    purely_generic = []
    partially_generic = []
    non_generic = []

    for kw in sorted(list(all_kws)):
        words = kw.lower().replace('&', '').replace('(', '').replace(')', '').replace('.', '').split()
        if not words: continue
        
        # Check if ALL words are in the generic list
        is_purely_generic = all(w in generic_words for w in words)
        
        # Check if ANY word is in the generic list
        has_generic = any(w in generic_words for w in words)
        
        if is_purely_generic:
            purely_generic.append(kw)
        elif has_generic:
            partially_generic.append(kw)
        else:
            non_generic.append(kw)

    print(f"\nTotal unique keywords: {len(all_kws)}")
    print(f"Purely generic keywords: {len(purely_generic)}")
    print(f"Partially generic keywords: {len(partially_generic)}")
    print(f"Non-generic keywords: {len(non_generic)}")
    
    print("\nSample of PURELY generic keywords:")
    for kw in purely_generic[:50]:
        print(f"- {kw}")
        
    # Save results
    with open(r'd:\sentimatix\scratch\generic_keywords_report.txt', 'w', encoding='utf-8') as f:
        f.write(f"Total Keywords: {len(all_kws)}\n")
        f.write(f"Purely Generic: {len(purely_generic)}\n")
        f.write(f"Partially Generic: {len(partially_generic)}\n")
        f.write(f"Non-Generic: {len(non_generic)}\n\n")
        f.write("Purely Generic List:\n")
        for kw in purely_generic:
            f.write(f"{kw}\n")

if __name__ == "__main__":
    analyze_generic_keywords()
