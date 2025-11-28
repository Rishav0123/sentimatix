-- Add indexes and helpers for yfin_symbol on stock_prices
-- Run this in Supabase SQL editor or psql against your database

-- 1) Ensure column exists (no-op if already present)
-- ALTER TABLE public.stock_prices ADD COLUMN IF NOT EXISTS yfin_symbol varchar NULL;

-- 2) Composite PK already exists on (stock_id, date)
-- Create indexes to support symbol-based lookups and time-bounded scans
CREATE INDEX IF NOT EXISTS idx_stock_prices_yfin_symbol
  ON public.stock_prices USING btree (yfin_symbol);

CREATE INDEX IF NOT EXISTS idx_stock_prices_yfin_symbol_date
  ON public.stock_prices USING btree (yfin_symbol, date);

-- 3) Helpful partial index if most yfin_symbol rows use .NS suffix
CREATE INDEX IF NOT EXISTS idx_stock_prices_yfin_symbol_ns
  ON public.stock_prices USING btree (yfin_symbol)
  WHERE yfin_symbol LIKE '%.NS';

-- 3b) Optional: ensure one row per (yfin_symbol, date)
CREATE UNIQUE INDEX IF NOT EXISTS uq_stock_prices_yfin_symbol_date
  ON public.stock_prices (yfin_symbol, date)
  WHERE yfin_symbol IS NOT NULL;

-- 4) Keep updated_at fresh on updates
CREATE OR REPLACE FUNCTION public.set_updated_at()
RETURNS trigger AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_set_updated_at ON public.stock_prices;
CREATE TRIGGER trg_set_updated_at
BEFORE UPDATE ON public.stock_prices
FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

-- 5) Optional: Foreign key to stocks table (uncomment if stocks.id exists)
-- ALTER TABLE public.stock_prices
--   ADD CONSTRAINT fk_stock_prices_stock
--   FOREIGN KEY (stock_id)
--   REFERENCES public.stocks(id)
--   ON DELETE CASCADE;

-- 6) Optional view: latest price per yfin_symbol
CREATE OR REPLACE VIEW public.v_latest_prices AS
SELECT sp.*
FROM public.stock_prices sp
JOIN (
  SELECT yfin_symbol, MAX(date) AS max_date
  FROM public.stock_prices
  WHERE yfin_symbol IS NOT NULL
  GROUP BY yfin_symbol
) t
ON sp.yfin_symbol = t.yfin_symbol AND sp.date = t.max_date;

-- 7) (Re)create trigger to compute change columns on insert
-- Assumes calculate_all_price_changes() is already defined
DROP TRIGGER IF EXISTS trg_calculate_all_price_changes ON public.stock_prices;
CREATE TRIGGER trg_calculate_all_price_changes
BEFORE INSERT ON public.stock_prices
FOR EACH ROW EXECUTE FUNCTION calculate_all_price_changes();
