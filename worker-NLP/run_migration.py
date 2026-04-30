import psycopg2

DB_PARAMS = {
    "host": "aws-1-ap-southeast-2.pooler.supabase.com",
    "port": 5432,
    "database": "postgres",
    "user": "postgres.hdsntducurmhossannue",
    "password": "Wallposter27@"
}

conn = psycopg2.connect(**DB_PARAMS)
conn.autocommit = True
cur = conn.cursor()

# Step 1: Add embedding column
try:
    cur.execute("ALTER TABLE public.stocks ADD COLUMN IF NOT EXISTS name_embedding vector(384);")
    print("OK: Added name_embedding column")
except Exception as e:
    print(f"SKIP: {e}")

# Step 2: Create HNSW index
try:
    cur.execute("CREATE INDEX IF NOT EXISTS stocks_name_embedding_idx ON public.stocks USING hnsw (name_embedding vector_cosine_ops);")
    print("OK: Created HNSW index")
except Exception as e:
    print(f"SKIP index: {e}")

# Step 3: Create match function
try:
    cur.execute("""
CREATE OR REPLACE FUNCTION public.match_stock_by_name(
  query_embedding vector(384),
  match_threshold float DEFAULT 0.6,
  match_count int DEFAULT 3
)
RETURNS TABLE (
  id uuid,
  stock_name varchar,
  yfin_symbol varchar,
  sector varchar,
  similarity float
)
LANGUAGE sql STABLE
AS $$
  SELECT
    s.id,
    s.stock_name,
    s.yfin_symbol,
    s.sector,
    1 - (s.name_embedding <=> query_embedding) AS similarity
  FROM public.stocks s
  WHERE s.name_embedding IS NOT NULL
    AND 1 - (s.name_embedding <=> query_embedding) > match_threshold
  ORDER BY s.name_embedding <=> query_embedding
  LIMIT match_count;
$$;
""")
    print("OK: Created match_stock_by_name function")
except Exception as e:
    print(f"SKIP function: {e}")

cur.close()
conn.close()
print("Migration complete.")
