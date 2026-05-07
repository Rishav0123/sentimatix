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

statements = [

# v_daily_sentiment: one row per (stock, day), no date filtering
"""
CREATE OR REPLACE VIEW public.v_daily_sentiment AS
SELECT
    n.yfin_symbol,
    n.stock_name,
    DATE(n.published_at)  AS day,
    COUNT(*)              AS article_count,
    AVG(n.sentiment_score) FILTER (WHERE n.sentiment_score IS NOT NULL) AS avg_sentiment,
    AVG(n.confidence)     FILTER (WHERE n.confidence IS NOT NULL)       AS avg_confidence,
    BOOL_OR(n.is_volatile) AS any_volatile
FROM public.news n
WHERE n.yfin_symbol IS NOT NULL
GROUP BY n.yfin_symbol, n.stock_name, DATE(n.published_at)
""",

# v_stock_momentum: uses most-recent article date as anchor instead of CURRENT_DATE
"""
CREATE OR REPLACE VIEW public.v_stock_momentum AS
WITH anchor AS (
    -- Use the most recent article as "today" (handles historical backfills)
    SELECT MAX(DATE(published_at)) AS latest_day FROM public.news
),
daily AS (
    SELECT d.* FROM public.v_daily_sentiment d
),
last_7d AS (
    SELECT
        d.yfin_symbol,
        d.stock_name,
        AVG(d.avg_sentiment)   AS sentiment_7d,
        SUM(d.article_count)   AS articles_7d
    FROM daily d, anchor a
    WHERE d.day > a.latest_day - INTERVAL '7 days'
    GROUP BY d.yfin_symbol, d.stock_name
),
prev_7d AS (
    SELECT
        d.yfin_symbol,
        AVG(d.avg_sentiment)   AS sentiment_prev_7d
    FROM daily d, anchor a
    WHERE d.day > a.latest_day - INTERVAL '14 days'
      AND d.day <= a.latest_day - INTERVAL '7 days'
    GROUP BY d.yfin_symbol
),
last_30d_stats AS (
    SELECT
        d.yfin_symbol,
        AVG(d.article_count)   AS avg_daily_articles,
        STDDEV(d.article_count) AS stddev_daily_articles
    FROM daily d, anchor a
    WHERE d.day > a.latest_day - INTERVAL '30 days'
    GROUP BY d.yfin_symbol
),
latest_day AS (
    SELECT d.yfin_symbol, d.article_count AS today_count
    FROM daily d, anchor a
    WHERE d.day = a.latest_day
)
SELECT
    l.yfin_symbol,
    l.stock_name,
    ROUND(l.sentiment_7d::numeric, 4)                                   AS sentiment_7d,
    ROUND(COALESCE(p.sentiment_prev_7d, 0)::numeric, 4)                 AS sentiment_prev_7d,
    ROUND((l.sentiment_7d - COALESCE(p.sentiment_prev_7d, 0))::numeric, 4) AS momentum_slope,
    CASE
        WHEN l.sentiment_7d > COALESCE(p.sentiment_prev_7d, 0) + 0.05  THEN 'improving'
        WHEN l.sentiment_7d < COALESCE(p.sentiment_prev_7d, 0) - 0.05  THEN 'declining'
        ELSE 'stable'
    END AS momentum_label,
    l.articles_7d,
    COALESCE(t.today_count, 0)                                          AS articles_today,
    ROUND(COALESCE(s.avg_daily_articles, 0)::numeric, 2)                AS avg_daily_articles_30d,
    CASE
        WHEN COALESCE(s.stddev_daily_articles, 0) = 0 THEN 0
        ELSE ROUND(
            (COALESCE(t.today_count, 0) - COALESCE(s.avg_daily_articles, 0))
            / s.stddev_daily_articles, 2
        )
    END AS volume_z_score
FROM last_7d l
LEFT JOIN prev_7d        p ON l.yfin_symbol = p.yfin_symbol
LEFT JOIN last_30d_stats s ON l.yfin_symbol = s.yfin_symbol
LEFT JOIN latest_day     t ON l.yfin_symbol = t.yfin_symbol
""",

# API-friendly function
"""
CREATE OR REPLACE FUNCTION public.get_stock_momentum(p_symbol text)
RETURNS TABLE (
    yfin_symbol        text,
    stock_name         text,
    sentiment_7d       numeric,
    sentiment_prev_7d  numeric,
    momentum_slope     numeric,
    momentum_label     text,
    articles_7d        bigint,
    articles_today     bigint,
    avg_daily_articles numeric,
    volume_z_score     numeric
)
LANGUAGE sql STABLE
AS $$
    SELECT
        yfin_symbol::text,
        stock_name::text,
        sentiment_7d,
        sentiment_prev_7d,
        momentum_slope,
        momentum_label::text,
        articles_7d,
        articles_today,
        avg_daily_articles_30d,
        volume_z_score
    FROM public.v_stock_momentum
    WHERE yfin_symbol = p_symbol
    LIMIT 1;
$$
"""
]

for i, sql in enumerate(statements, 1):
    name = sql.strip().split('\n')[0][:80]
    try:
        cur.execute(sql)
        print(f"[{i}] OK: {name}")
    except Exception as e:
        print(f"[{i}] ERROR: {e}")

cur.close()
conn.close()
print("\nPhase 3 migration (v2) complete.")
