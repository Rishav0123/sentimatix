import os
from supabase import create_client, Client
from dotenv import load_dotenv
import pandas as pd

# Load environment variables
load_dotenv()
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

def get_table_schema():
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("Error: SUPABASE_URL and SUPABASE_KEY must be set in .env")
        return

    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # Query information_schema for the 'stocks' table
    # Note: Using rpc or direct sql query if allowed, 
    # but supabase-py doesn't have a direct 'sql' method for raw queries usually.
    # However, we can try to fetch a single row to see columns or use a custom function if exists.
    
    try:
        # Method 1: Fetch one row to get column names
        response = supabase.table('stocks').select('*').limit(1).execute()
        if response.data:
            columns = response.data[0].keys()
            print("Columns in 'stocks' table:")
            for col in columns:
                print(f"- {col}")
            return list(columns)
        else:
            print("Table 'stocks' is empty or not found.")
            return []
    except Exception as e:
        print(f"Error fetching schema: {e}")
        return []

if __name__ == "__main__":
    get_table_schema()
