-- Setup Supabase Vector Database for RAG
-- Run this script in your Supabase SQL Editor

-- 1. Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Create news_embeddings table for RAG
CREATE TABLE IF NOT EXISTS public.news_embeddings (
    id BIGSERIAL PRIMARY KEY,
    news_id TEXT NOT NULL UNIQUE,
    embedding vector(1536) NOT NULL,  -- OpenAI text-embedding-3-small dimension
    
    -- Metadata for filtering
    symbol TEXT,
    title TEXT,
    content_preview TEXT,
    published_at TIMESTAMP WITH TIME ZONE,
    sentiment TEXT CHECK (sentiment IN ('positive', 'negative', 'neutral')),
    sentiment_score FLOAT,
    source TEXT,
    url TEXT,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. Create indexes for performance
CREATE INDEX IF NOT EXISTS news_embeddings_symbol_idx ON public.news_embeddings(symbol);
CREATE INDEX IF NOT EXISTS news_embeddings_published_at_idx ON public.news_embeddings(published_at);
CREATE INDEX IF NOT EXISTS news_embeddings_sentiment_idx ON public.news_embeddings(sentiment);

-- 4. Create vector similarity index (HNSW for fast approximate search)
CREATE INDEX IF NOT EXISTS news_embeddings_embedding_idx 
ON public.news_embeddings 
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- 5. Create function for semantic search with filtering
CREATE OR REPLACE FUNCTION match_news_embeddings(
    query_embedding vector(1536),
    match_threshold float DEFAULT 0.7,
    match_count int DEFAULT 6,
    filter_symbol text DEFAULT NULL,
    filter_start_date timestamp DEFAULT NULL,
    filter_end_date timestamp DEFAULT NULL
)
RETURNS TABLE (
    news_id text,
    title text,
    content_preview text,
    published_at timestamp with time zone,
    symbol text,
    sentiment text,
    sentiment_score float,
    source text,
    url text,
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        ne.news_id,
        ne.title,
        ne.content_preview,
        ne.published_at,
        ne.symbol,
        ne.sentiment,
        ne.sentiment_score,
        ne.source,
        ne.url,
        1 - (ne.embedding <=> query_embedding) AS similarity
    FROM public.news_embeddings ne
    WHERE
        (filter_symbol IS NULL OR ne.symbol = filter_symbol)
        AND (filter_start_date IS NULL OR ne.published_at >= filter_start_date)
        AND (filter_end_date IS NULL OR ne.published_at <= filter_end_date)
        AND (1 - (ne.embedding <=> query_embedding)) > match_threshold
    ORDER BY similarity DESC
    LIMIT match_count;
END;
$$;

-- 6. Create trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_news_embeddings_updated_at
BEFORE UPDATE ON public.news_embeddings
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- 7. Grant permissions (adjust role name as needed)
ALTER TABLE public.news_embeddings ENABLE ROW LEVEL SECURITY;

-- Create policy to allow service role full access
CREATE POLICY "Service role can do everything"
ON public.news_embeddings
FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

-- Create policy for anon/authenticated users to read
CREATE POLICY "Anon and authenticated can read"
ON public.news_embeddings
FOR SELECT
TO anon, authenticated
USING (true);

-- 8. Create view for monitoring
CREATE OR REPLACE VIEW public.news_embeddings_stats AS
SELECT
    COUNT(*) AS total_embeddings,
    COUNT(DISTINCT symbol) AS unique_symbols,
    MIN(published_at) AS oldest_article,
    MAX(published_at) AS newest_article,
    COUNT(*) FILTER (WHERE sentiment = 'positive') AS positive_count,
    COUNT(*) FILTER (WHERE sentiment = 'negative') AS negative_count,
    COUNT(*) FILTER (WHERE sentiment = 'neutral') AS neutral_count,
    AVG(sentiment_score) AS avg_sentiment_score
FROM public.news_embeddings;

-- Grant access to stats view
GRANT SELECT ON public.news_embeddings_stats TO anon, authenticated, service_role;

-- Confirm setup
SELECT 'Vector database setup complete!' AS status;
SELECT * FROM public.news_embeddings_stats;
