import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

def create_table():
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_KEY')
    supabase = create_client(url, key)
    
    sql = """
    CREATE TABLE IF NOT EXISTS public.scraper_reports (
        id uuid DEFAULT extensions.uuid_generate_v4() NOT NULL PRIMARY KEY,
        scraper_name text NOT NULL,
        run_id uuid,
        timestamp timestamp with time zone DEFAULT now(),
        total_inserted integer DEFAULT 0,
        stock_counts jsonb DEFAULT '{}'::jsonb
    );
    """
    
    try:
        # Check if we can run SQL via RPC
        response = supabase.rpc('exec_sql', {'sql': sql}).execute()
        print("Table 'scraper_reports' created/verified successfully via RPC.")
    except Exception as e:
        print(f"Could not create table via RPC: {e}")
        print("\nPlease run the following SQL in your Supabase SQL Editor:")
        print(sql)

if __name__ == "__main__":
    create_table()
