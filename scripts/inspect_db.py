import psycopg2

DB_PARAMS = {
    "host": "aws-1-ap-southeast-2.pooler.supabase.com",
    "port": 5432,
    "database": "postgres",
    "user": "postgres.hdsntducurmhossannue",
    "password": "Wallposter27@"
}

conn = psycopg2.connect(**DB_PARAMS)
cur = conn.cursor()

# Get columns of stocks table
cur.execute("""
    SELECT column_name, data_type, character_maximum_length
    FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = 'stocks'
    ORDER BY ordinal_position;
""")
print("=== STOCKS TABLE SCHEMA ===")
for row in cur.fetchall():
    print(f"  {row[0]}: {row[1]}")

# Sample a few rows
cur.execute("SELECT stock_name, yfin_symbol, sector, country FROM public.stocks LIMIT 5;")
print("\n=== SAMPLE ROWS ===")
for row in cur.fetchall():
    print(f"  {row[0]} | {row[1]} | {row[2]} | {row[3]}")

# Check if pgvector is enabled
cur.execute("SELECT extname FROM pg_extension WHERE extname = 'vector';")
has_vector = cur.fetchone()
print(f"\n=== PGVECTOR ENABLED: {bool(has_vector)} ===")

cur.close()
conn.close()
