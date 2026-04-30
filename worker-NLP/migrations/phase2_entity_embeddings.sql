-- Phase 2: Semantic Entity Linker - Schema Migration
-- Run this in your Supabase SQL Editor

-- Step 1: Add embedding column to stocks table (384 dimensions for all-MiniLM-L6-v2)
ALTER TABLE public.stocks
ADD COLUMN IF NOT EXISTS name_embedding vector(384);

-- Step 2: Create an HNSW index for fast approximate nearest-neighbor search
CREATE INDEX IF NOT EXISTS stocks_name_embedding_idx
ON public.stocks
USING hnsw (name_embedding vector_cosine_ops);

-- Step 3: Create the match function for the news pipeline to call
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
