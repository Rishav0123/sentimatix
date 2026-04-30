"""
Phase 2: Stock Embedding Worker
Generates vector embeddings for all stocks and stores them in Supabase.
Run this once (and re-run whenever you add new stocks).

Model: all-MiniLM-L6-v2 (384-dim, free, local, fast)
"""

import psycopg2
from sentence_transformers import SentenceTransformer
import os

DB_PARAMS = {
    "host": "aws-1-ap-southeast-2.pooler.supabase.com",
    "port": 5432,
    "database": "postgres",
    "user": "postgres.hdsntducurmhossannue",
    "password": "Wallposter27@"
}

MODEL_NAME = "all-MiniLM-L6-v2"


def build_stock_search_text(stock_name: str, yfin_symbol: str, sector: str) -> str:
    """
    Build a rich text representation for embedding.
    More context = better semantic matching.
    E.g., "HDFC Bank HDFCBANK.NS Banking financial services india"
    """
    parts = [stock_name]
    
    # Add ticker without .NS suffix for alias matching
    if yfin_symbol:
        parts.append(yfin_symbol.replace(".NS", "").replace(".BO", ""))
    
    # Add common short-form aliases
    aliases = {
        "HDFC Bank": ["HDFC", "Housing Development Finance", "HDFCBANK"],
        "HDFC Life": ["HDFC Life Insurance", "HDFCLIFE"],
        "Reliance Industries": ["Reliance", "RIL", "Mukesh Ambani", "Jio", "RELIANCE"],
        "Tata Consultancy Services": ["TCS", "Tata Consultancy", "TCS.NS"],
        "Tata Motors": ["Tata", "TATAMOTORS", "Jaguar"],
        "State Bank of India": ["SBI", "State Bank", "SBIN"],
        "Oil and Natural Gas Corporation": ["ONGC", "Oil India"],
        "Bharat Petroleum": ["BPCL", "Bharat Petro"],
        "Hindustan Petroleum": ["HPCL", "Hindustan Petro"],
        "Larsen & Toubro": ["L&T", "LT", "Larsen Toubro", "LT.NS"],
        "Maruti Suzuki": ["Maruti", "MARUTI", "Suzuki India"],
        "HCL Technologies": ["HCL", "HCLTECH"],
        "Tech Mahindra": ["Tech Mah", "TECHM"],
        "Bajaj Finance": ["Bajaj Fin", "BAJFINANCE"],
        "Bajaj Finserv": ["Bajaj", "BAJAJFINSV"],
        "ICICI Bank": ["ICICI", "ICICIBANK"],
        "Axis Bank": ["Axis", "AXISBANK"],
        "Kotak Mahindra Bank": ["Kotak", "KOTAKBANK", "Kotak Bank"],
        "Wipro": ["Wipro", "WIPRO"],
        "Infosys": ["Infy", "INFY", "Infosys BPM"],
        "Sun Pharmaceutical": ["Sun Pharma", "SUNPHARMA"],
        "Adani Enterprises": ["Adani", "ADANIENT", "Gautam Adani"],
        "Adani Ports": ["Adani Ports", "ADANIPORTS"],
        "ITC": ["ITC", "ITC Ltd"],
        "Asian Paints": ["Asian Paints", "ASIANPAINT"],
        "Titan Company": ["Titan", "TITAN"],
        "UltraTech Cement": ["UltraTech", "ULTRACEMCO"],
        "Nestle India": ["Nestle", "NESTLEIND", "Maggi"],
        "Divi's Laboratories": ["Divis", "DIVISLAB"],
        "Dr. Reddy's Laboratories": ["Dr Reddys", "DRREDDY"],
        "Cipla": ["Cipla", "CIPLA"],
    }
    
    for name, alias_list in aliases.items():
        if name.lower() in stock_name.lower():
            parts.extend(alias_list)
            break
    
    if sector:
        parts.append(sector)
    
    return " ".join(parts)


def run():
    print(f"Loading model: {MODEL_NAME}...")
    model = SentenceTransformer(MODEL_NAME)
    
    print("Connecting to database...")
    conn = psycopg2.connect(**DB_PARAMS)
    conn.autocommit = True
    cur = conn.cursor()
    
    # Fetch all stocks
    cur.execute("SELECT id, stock_name, yfin_symbol, sector FROM public.stocks;")
    stocks = cur.fetchall()
    print(f"Found {len(stocks)} stocks to embed.\n")
    
    updated = 0
    for stock_id, stock_name, yfin_symbol, sector in stocks:
        search_text = build_stock_search_text(
            stock_name or "", yfin_symbol or "", sector or ""
        )
        
        # Generate embedding
        embedding = model.encode(search_text).tolist()
        
        # Write to database (pgvector accepts Python lists)
        cur.execute(
            "UPDATE public.stocks SET name_embedding = %s::vector WHERE id = %s;",
            (embedding, stock_id)
        )
        updated += 1
        print(f"[{updated:3d}/{len(stocks)}] {stock_name:<35} -> Embedded: '{search_text[:60]}...'")
    
    print(f"\nDone. Updated {updated} stocks with embeddings.")
    cur.close()
    conn.close()


if __name__ == "__main__":
    run()
