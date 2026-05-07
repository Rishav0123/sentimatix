import pandas as pd
import json
import os

def format_to_user_schema(csv_path, output_json_path):
    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} not found.")
        return

    # Read the official NSE CSV
    df = pd.read_csv(csv_path)
    
    # User's existing symbols (from the snippet provided)
    # This is just for comparison or to mark them.
    # We'll just generate the whole list in the new format.
    
    formatted_list = []
    
    for idx, row in df.iterrows():
        symbol = str(row['SYMBOL']).strip()
        name = str(row['NAME OF COMPANY']).strip()
        isin = str(row[' ISIN NUMBER']).strip()
        
        # Construct the object following the user's schema
        stock_obj = {
            "idx": idx,
            "yfin_symbol": f"{symbol}.NS",
            "exchange": "NSE",
            "is_active": True,
            "country": "IN",
            "type": "equity",
            "stock_name": name,
            "keyword_lst": json.dumps({"keyword": [name, symbol, name.split(' ')[0]]}),
            "isin": isin,
            "listing_date": str(row[' DATE OF LISTING']).strip(),
            # Placeholders for fields we don't have in the master CSV
            "sector": "Unknown", 
            "mc_link_1": "",
            "mc_link_2": "",
            "sentiment_30d": "0.00",
            "sentiment_7d": "0.00"
        }
        formatted_list.append(stock_obj)
    
    # Save to JSON
    with open(output_json_path, "w") as f:
        json.dump(formatted_list, f, indent=2)
    
    print(f"Successfully formatted {len(formatted_list)} stocks into {output_json_path}")

if __name__ == "__main__":
    format_to_user_schema("nse_stocks.csv", "nse_stocks_formatted.json")
