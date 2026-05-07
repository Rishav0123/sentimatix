import pandas as pd
import json
from supabase import create_client, Client

# Supabase configuration (copied from scrape_moneycontrol.py)
SUPABASE_URL = "https://uqvouptulubydignwtkv.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVxdm91cHR1bHVieWRpZ253dGt2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTk5MzQ1MTUsImV4cCI6MjA3NTUxMDUxNX0.0PtQ_9FVKzFL6pTVOHFoEZbTk5477-RyeH_XR2B12m8"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
# Download latest version

def get_active_stocks():
    try:
        response = supabase.table('stocks').select('id, stock_name, yfin_symbol, keyword_lst').eq('is_active', True).execute()
        return response.data
    except Exception as e:
        print(f"Error fetching stocks from database: {e}")
        return []

def main():
    stocks = get_active_stocks()
    if not stocks:
        print("No active stocks found in database")
        return
    path = "files/IndianFinancialNews.csv"
    df = pd.read_csv(f"{path}")

    df = pd.read_csv(f"{path}")

    all_matches = []
    for stock in stocks:
        id = stock['id']
        yfin_symbol = stock.get('yfin_symbol')
        keywords = []
        # Parse keywords from keyword_lst (JSON column)
        if stock.get('keyword_lst'):
            try:
                kw_obj = json.loads(stock['keyword_lst']) if isinstance(stock['keyword_lst'], str) else stock['keyword_lst']
                if isinstance(kw_obj, dict) and 'keyword' in kw_obj:
                    keywords = kw_obj['keyword']
                elif isinstance(kw_obj, list):
                    keywords = kw_obj
            except Exception as e:
                print(f"Error parsing keywords for {id}: {e}")
        if not keywords:
            continue
        for kw in keywords:
            # Case-insensitive substring match in Title or Description
            mask = df['Title'].str.contains(kw, case=False, na=False) | df['Description'].str.contains(kw, case=False, na=False)
            matches = df[mask]
            for _, row in matches.iterrows():
                all_matches.append({
                    'Date': row['Date'],
                    'Title': row['Title'],
                    'Description': row['Description'],
                    'yfin_symbol': yfin_symbol,
                    'tags' : [kw, "in"]
                })
    # Create a dataframe from all matches
    matches_df = pd.DataFrame(all_matches)
    print(f"\nTotal matched rows: {len(matches_df)}")
    print(matches_df)
        # Save to CSV
    matches_df.to_csv("matched_news.csv", index=False)
    print("Saved matched results to matched_news.csv")
        #print(df.head())
    #print("Active stocks:", stocks)
    #path = "files/IndianFinancialNews.csv"



#print("Path to dataset files:", path)

#df = pd.read_csv(f"{path}")



if __name__ == "__main__":
    main()