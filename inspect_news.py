import psycopg2

DB_PARAMS = {"host":"aws-1-ap-southeast-2.pooler.supabase.com","port":5432,"database":"postgres","user":"postgres.hdsntducurmhossannue","password":"Wallposter27@"}
conn = psycopg2.connect(**DB_PARAMS)
cur = conn.cursor()

cur.execute("SELECT column_name FROM information_schema.columns WHERE table_schema='public' AND table_name='news' ORDER BY ordinal_position;")
cols = [r[0] for r in cur.fetchall()]
print("news columns:", cols)

cur.execute("SELECT yfin_symbol, stock_name, sentiment, sentiment_score, confidence, published_at FROM public.news WHERE sentiment_score IS NOT NULL LIMIT 5;")
print("\nSample rows with sentiment:")
for r in cur.fetchall():
    print(" ", r)

cur.execute("SELECT COUNT(*) FROM public.news WHERE yfin_symbol IS NOT NULL;")
print("\nRows with yfin_symbol:", cur.fetchone()[0])

cur.execute("SELECT COUNT(*) FROM public.news WHERE sentiment_score IS NOT NULL;")
print("Rows with sentiment_score:", cur.fetchone()[0])

cur.close()
conn.close()
