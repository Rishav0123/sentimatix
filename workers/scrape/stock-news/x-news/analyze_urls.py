import os, sys
sys.path.append(os.getcwd())
from utilities.get_active_stocks import get_supabase_client

def analyze_urls():
    supabase = get_supabase_client()
    # Get all active stocks with mc_links
    res = supabase.table('stocks').select('yfin_symbol, mc_link_1, mc_link_2').not_.is_('mc_link_1', 'null').execute()
    stocks = res.data
    
    print(f"Total stocks with MC links: {len(stocks)}")
    
    invalid_count = 0
    swapped_count = 0
    suspicious_count = 0
    
    for stock in stocks:
        link1 = stock['mc_link_1'].strip()
        link2 = stock['mc_link_2'].strip()
        
        # New logic: longer is company_name, shorter is symbol
        if len(link1) > len(link2):
            company = link1
            symbol = link2
            # Check if they were swapped in DB (DB expected link1=symbol, link2=company or vice versa)
            # Actually we just know we swapped them during construction
            swapped_count += 1
        else:
            company = link2
            symbol = link1
            
        # A valid symbol is usually 2-5 characters. If the *shorter* string is very long, it's garbage.
        # Also check if the "symbol" is just the yfin_symbol
        if len(symbol) > 6 or ".NS" in symbol or ".BO" in symbol or symbol.lower() == company.lower():
            invalid_count += 1
            if invalid_count <= 10:
                print(f"INVALID: {stock['yfin_symbol']} -> Company: {company}, Symbol: {symbol}")
        elif len(symbol) == 0 or len(company) == 0:
            invalid_count += 1
            
    print(f"\n--- Summary ---")
    print(f"Total Stocks: {len(stocks)}")
    print(f"Swapped Params (Handled by new logic): {swapped_count}")
    print(f"Invalid/Garbage Params (Will still fail): {invalid_count}")
    
if __name__ == "__main__":
    analyze_urls()
