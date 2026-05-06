import os
import json
from dotenv import load_dotenv
from supabase import create_client

def analyze_person_names():
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

    # Heuristic for person names:
    # 2-3 words, no corporate suffixes, starts with common Indian name patterns
    person_indicators = {
        'aditya', 'deepak', 'aarti', 'vijay', 'shriram', 'krishna', 'lakshmi', 
        'ganesh', 'rahul', 'amit', 'sanjay', 'anita', 'sunil', 'rajesh', 
        'ajay', 'prakash', 'ashok', 'vinod', 'manish', 'suresh', 'ram',
        'shanthi', 'lal', 'mohan', 'kumar', 'singh', 'sharma', 'gupta', 'jain',
        'anand', 'arvind', 'atmaram', 'balaji', 'bhagwan', 'bharat', 'brij',
        'chandra', 'dayal', 'dharam', 'ganpat', 'gopal', 'govind', 'hari',
        'ishwar', 'jagdish', 'kishore', 'madhav', 'madhusudan', 'mahendra',
        'mangal', 'moti', 'narayan', 'narendra', 'om', 'pradeep', 'purushottam',
        'rachesh', 'radhey', 'raghuvir', 'rajendra', 'ramesh', 'ratan', 'shankar',
        'shiva', 'shyam', 'tulsi', 'umashankar', 'uttam', 'vasudev'
    }
    
    corporate_indicators = {
        'ltd', 'limited', 'corp', 'corporation', 'inc', 'co', 'company', 
        'industries', 'ind', 'services', 'solutions', 'systems', 'tech', 
        'india', 'indian', 'asia', 'asian', 'global', 'intl', 'international',
        'bank', 'finance', 'capital', 'steel', 'power', 'energy', 'cement',
        'agro', 'pharma', 'chem', 'motors', 'auto', 'textiles', 'retail',
        'hotels', 'infra', 'engineering', 'projects', 'logistics', 'shipping',
        'drugs', 'surfactants', 'fertilizers', 'nitrite', 'benzoplast', 'housing',
        'builders', 'lifestyle', 'fashion', 'money', 'real', 'estates', 'retail',
        'leyland', 'paints', 'cement', 'petro', 'chemicals', 'wires', 'cables',
        'labs', 'laboratory', 'diagnostic', 'medical', 'hospital', 'healthcare'
    }

    person_names = []
    others = []

    for kw in sorted(list(all_kws)):
        words = kw.split()
        kw_lower = kw.lower()
        
        # Heuristic: 2 words, first word in indicators, no corporate indicators
        is_person = False
        if 2 <= len(words) <= 3:
            first_word = words[0].lower()
            last_word = words[-1].lower()
            
            # If first or last word is a common name part
            if first_word in person_indicators or last_word in person_indicators:
                # Check for corporate words
                has_corp = any(c in kw_lower for c in corporate_indicators)
                if not has_corp:
                    is_person = True
        
        if is_person:
            person_names.append(kw)
        else:
            others.append(kw)

    print(f"\nTotal unique keywords: {len(all_kws)}")
    print(f"Likely person-name keywords: {len(person_names)}")
    
    print("\nSample of identified person names:")
    for name in person_names[:50]:
        print(f"- {name}")
    
    # Save results
    with open(r'd:\sentimatix\scratch\person_names_report.txt', 'w', encoding='utf-8') as f:
        f.write(f"Total Keywords: {len(all_kws)}\n")
        f.write(f"Identified Person Names: {len(person_names)}\n\n")
        f.write("Full List:\n")
        for name in person_names:
            f.write(f"{name}\n")

if __name__ == "__main__":
    analyze_person_names()
