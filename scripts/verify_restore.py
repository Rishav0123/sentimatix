import psycopg2

DB_PARAMS = {
    "host": "aws-1-ap-southeast-2.pooler.supabase.com",
    "port": 5432,
    "database": "postgres",
    "user": "postgres.hdsntducurmhossannue",
    "password": "Wallposter27@"
}

def verify():
    print("Connecting to database for verification...")
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        cur = conn.cursor()
        
        # Get list of tables in public schema
        cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        tables = [r[0] for r in cur.fetchall()]
        
        print("\nTable Row Counts:")
        for table in tables:
            try:
                cur.execute(f"SELECT COUNT(*) FROM public.\"{table}\"")
                count = cur.fetchone()[0]
                print(f"- {table}: {count}")
            except Exception as e:
                print(f"- {table}: Error checking count ({e})")
        
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    verify()
