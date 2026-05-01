import psycopg2

DB_PARAMS = {"host":"aws-1-ap-southeast-2.pooler.supabase.com","port":5432,"database":"postgres","user":"postgres.hdsntducurmhossannue","password":"Wallposter27@"}
conn = psycopg2.connect(**DB_PARAMS)
cur = conn.cursor()

cur.execute("SELECT COUNT(*) FROM public.news;")
total = cur.fetchone()[0]

cur.execute("SELECT COUNT(*) FROM public.news WHERE sentiment_score IS NULL;")
missing_sentiment = cur.fetchone()[0]

cur.execute("SELECT COUNT(*) FROM public.news WHERE sentiment_score IS NOT NULL AND confidence IS NULL;")
missing_confidence = cur.fetchone()[0]

cur.execute("SELECT COUNT(*) FROM public.news WHERE sentiment_score IS NOT NULL;")
done = cur.fetchone()[0]

print(f"Total articles         : {total:,}")
print(f"Sentiment done         : {done:,}")
print(f"Missing sentiment_score: {missing_sentiment:,}")
print(f"Has score, missing conf: {missing_confidence:,}")
print(f"Completion             : {done/total*100:.1f}%")

cur.close()
conn.close()
