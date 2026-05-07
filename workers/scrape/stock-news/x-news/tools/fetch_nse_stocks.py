import requests
import pandas as pd
import os

def download_nse_stocks():
    url = "https://archives.nseindia.com/content/equities/EQUITY_L.csv"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
    }
    
    print(f"Downloading from {url}...")
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        # Save raw CSV
        csv_path = "nse_stocks.csv"
        with open(csv_path, "wb") as f:
            f.write(response.content)
        print(f"Saved to {csv_path}")
        
        # Read and clean
        df = pd.read_csv(csv_path)
        print(f"Total stocks found: {len(df)}")
        
        # Save as JSON for easier use
        json_path = "nse_stocks.json"
        df.to_json(json_path, orient="records", indent=2)
        print(f"Saved to {json_path}")
        
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    download_nse_stocks()
