-- Table to store identified stock developments/events
CREATE TABLE IF NOT EXISTS stock_developments (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    development_date TIMESTAMP NOT NULL,
    title VARCHAR(500) NOT NULL,
    summary TEXT NOT NULL,
    category VARCHAR(50), -- e.g., 'earnings', 'merger', 'regulatory', 'product', 'financial'
    sentiment VARCHAR(20), -- 'positive', 'negative', 'neutral'
    impact_score DECIMAL(3,2), -- 0.00 to 1.00
    source_article_ids INTEGER[], -- Array of news article IDs used
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Index for fast lookups
CREATE INDEX idx_stock_developments_symbol ON stock_developments(symbol);
CREATE INDEX idx_stock_developments_date ON stock_developments(development_date DESC);
CREATE INDEX idx_stock_developments_symbol_date ON stock_developments(symbol, development_date DESC);

-- Add comment
COMMENT ON TABLE stock_developments IS 'Stores AI-identified key developments for stocks, updated hourly';
