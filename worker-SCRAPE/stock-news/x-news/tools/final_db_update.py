import json
import os
import re
from supabase import create_client
from dotenv import load_dotenv
from tqdm import tqdm

# Manual fixes for common mis-matches or missing high-cap stocks
MANUAL_FIXES = {
    "TATACONSUM.NS": {"MC1": "tataconsumerproducts", "MC2": "TT", "Status": "Matched"},
    "M&M.NS": {"MC1": "mahindramahindra", "MC2": "MM", "Status": "Matched"},
    "LODHA.NS": {"MC1": "macrotechdevelopers", "MC2": "MD04", "Status": "Matched"},
    "HAL.NS": {"MC1": "hindustanaeronautics", "MC2": "HAL", "Status": "Matched"},
    "MARUTI.NS": {"MC1": "marutisuzukiindia", "MC2": "MS24", "Status": "Matched"},
    "SBILIFE.NS": {"MC1": "sbilifeinsurancecompany", "MC2": "SLI03", "Status": "Matched"},
    "HINDUNILVR.NS": {"MC1": "hindustanunilever", "MC2": "HU", "Status": "Matched"},
    "HINDZINC.NS": {"MC1": "hindustanzinc", "MC2": "HZ", "Status": "Matched"},
    "DRREDDY.NS": {"MC1": "drreddyslaboratories", "MC2": "DRL", "Status": "Matched"},
    "DIVISLAB.NS": {"MC1": "divislaboratories", "MC2": "DL03", "Status": "Matched"},
    "ULTRACEMCO.NS": {"MC1": "ultratechcement", "MC2": "UTC01", "Status": "Matched"},
}

def is_valid_match(stock):
    mc1 = (stock.get('MC1') or "").lower()
    symbol = (stock.get('Symbol') or "").split('.')[0].lower()
    name = (stock.get('NSE_Name') or "").lower()
    
    # Simple validation: mc1 should contain part of symbol or part of name
    # Or symbol should be in mc1
    if symbol in mc1.replace("-", ""):
        return True
    
    # Check words in name
    name_words = re.findall(r'\w+', name)
    # Filter out common words like 'limited', 'india', 'corporation', 'limited'
    ignore = {'limited', 'india', 'corporation', 'corp', 'ltd', 'industries', 'ind', 'services'}
    important_words = [w for w in name_words if w not in ignore and len(w) > 2]
    
    for word in important_words:
        if word in mc1:
            return True
            
    return False

def finalize_mapping():
    with open('full_mapping_v2.json', 'r') as f:
        mapping = json.load(f)
        
    print(f"Total stocks: {len(mapping)}")
    
    final_count = 0
    for stock in mapping:
        symbol = stock['Symbol']
        
        # Apply manual fixes
        if symbol in MANUAL_FIXES:
            stock.update(MANUAL_FIXES[symbol])
            final_count += 1
            continue
            
        # Validate existing matches
        if stock['Status'] in ['Matched', 'Verify'] and stock['MC1']:
            if not is_valid_match(stock):
                # Reset if invalid
                print(f"Invalidating match: {symbol} -> {stock['MC1']} (Name: {stock['NSE_Name']})")
                stock['MC1'] = None
                stock['MC2'] = None
                stock['Status'] = 'Missing'
            else:
                final_count += 1
                
    print(f"\nFinal count of valid matches: {final_count}")
    
    with open('full_mapping_final.json', 'w') as f:
        json.dump(mapping, f, indent=2)
    print("Saved to full_mapping_final.json")

def update_db():
    load_dotenv('d:/sentimatix/worker-SCRAPE/stock-news/x-news/.env')
    url = os.environ.get('SUPABASE_URL')
    key = os.environ.get('SUPABASE_KEY')
    supabase = create_client(url, key)
    
    with open('full_mapping_final.json', 'r') as f:
        mapping = json.load(f)
        
    valid_stocks = [s for s in mapping if s['Status'] in ['Matched', 'Verify'] and s['MC1'] and s['MC2']]
    
    print(f"Updating {len(valid_stocks)} stocks in Supabase...")
    
    update_count = 0
    for stock in tqdm(valid_stocks):
        try:
            supabase.table('stocks').update({
                'mc_link_1': stock['MC1'],
                'mc_link_2': stock['MC2']
            }).eq('yfin_symbol', stock['Symbol']).execute()
            update_count += 1
        except Exception as e:
            print(f"Error updating {stock['Symbol']}: {e}")
            
    print(f"Successfully updated {update_count} stocks.")

if __name__ == "__main__":
    finalize_mapping()
    confirm = input("Proceed with database update? (yes/no): ")
    if confirm.lower() == 'yes':
        update_db()
