import os
from supabase import create_client
from dotenv import load_dotenv
import json

load_dotenv()

def fetch_reports():
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_KEY')
    supabase = create_client(url, key)
    
    response = supabase.table('scraper_reports').select("*").order('timestamp', desc=True).limit(10).execute()
    
    if response.data:
        print(json.dumps(response.data, indent=2, default=str))
    else:
        print("No data found in scraper_reports.")

if __name__ == "__main__":
    fetch_reports()
