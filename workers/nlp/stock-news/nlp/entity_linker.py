"""
Phase 2: Semantic Entity Linker
Replaces regex-based company detection with vector similarity search.

Usage:
    from entity_linker import SemanticEntityLinker
    linker = SemanticEntityLinker()
    stocks = linker.find_stocks(title="HDFC Bank Ltd posts record profits")
    # -> [{"stock_name": "HDFC Bank", "yfin_symbol": "HDFCBANK.NS", "similarity": 0.91}]
"""

import psycopg2
from sentence_transformers import SentenceTransformer
from functools import lru_cache
from typing import List, Dict

DB_PARAMS = {
    "host": "aws-1-ap-southeast-2.pooler.supabase.com",
    "port": 5432,
    "database": "postgres",
    "user": "postgres.hdsntducurmhossannue",
    "password": "Wallposter27@"
}

MODEL_NAME = "all-MiniLM-L6-v2"

# Similarity thresholds
STRONG_MATCH_THRESHOLD = 0.65   # High confidence: definitely this stock
WEAK_MATCH_THRESHOLD = 0.50     # Low confidence: possible match

# Fast lookup: alias/ticker -> canonical stock name
# This handles all known short-forms without any ML
ALIAS_LOOKUP = {
    # Tickers (without .NS/.BO)
    "TCS": "Tata Consultancy Services",
    "INFY": "Infosys",
    "INFY": "Infosys",
    "RIL": "Reliance Industries",
    "RELIANCE": "Reliance Industries",
    "SBI": "State Bank of India",
    "HDFC": "HDFC Bank",
    "HDFCBANK": "HDFC Bank",
    "ICICI": "ICICI Bank",
    "ICICIBANK": "ICICI Bank",
    "WIPRO": "Wipro",
    "HCLTECH": "HCL Technologies",
    "HCL": "HCL Technologies",
    "TECHM": "Tech Mahindra",
    "BAJFINANCE": "Bajaj Finance",
    "BAJAJFINSV": "Bajaj Finserv",
    "AXISBANK": "Axis Bank",
    "KOTAKBANK": "Kotak Mahindra Bank",
    "KOTAK": "Kotak Mahindra Bank",
    "ONGC": "Oil and Natural Gas Corporation",
    "BPCL": "Bharat Petroleum",
    "HPCL": "Hindustan Petroleum",
    "SBIN": "State Bank of India",
    "ADANIENT": "Adani Enterprises",
    "ADANIPORTS": "Adani Ports",
    "SUNPHARMA": "Sun Pharmaceutical",
    "DRREDDY": "Dr. Reddy's Laboratories",
    "CIPLA": "Cipla",
    "TITAN": "Titan Company",
    "TATAMOTORS": "Tata Motors",
    "ULTRACEMCO": "UltraTech Cement",
    "NESTLEIND": "Nestle India",
    "DIVISLAB": "Divi's Laboratories",
    "ASIANPAINT": "Asian Paints",
    "MARUTI": "Maruti Suzuki",
    "ITC": "ITC",
    # Common names / informal names
    "Infy": "Infosys",
    "Jio": "Reliance Industries",
    "Mukesh Ambani": "Reliance Industries",
    "Bajaj Fin": "Bajaj Finance",
    "L&T": "Larsen & Toubro",
    "LT": "Larsen & Toubro",
    "Tech Mah": "Tech Mahindra",
    "Dr Reddys": "Dr. Reddy's Laboratories",
    "Sun Pharma": "Sun Pharmaceutical",
    "UltraTech": "UltraTech Cement",
    "Maggi": "Nestle India",
    "Jaguar": "Tata Motors",
    "Divis": "Divi's Laboratories",
    "Gautam Adani": "Adani Enterprises",
    "Housing Development Finance": "HDFC Bank",
}


class SemanticEntityLinker:
    _instance = None  # Singleton pattern to avoid reloading model

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        print(f"Loading embedding model: {MODEL_NAME}...")
        self.model = SentenceTransformer(MODEL_NAME)
        self.conn = psycopg2.connect(**DB_PARAMS)
        print("Semantic Entity Linker ready.")
        self._initialized = True

    def _exact_match(self, text: str):
        """Fast alias/ticker lookup. Returns stock info dict or None."""
        text_lower = text.lower()
        
        cur = self.conn.cursor()
        for alias, canonical_name in ALIAS_LOOKUP.items():
            if alias.lower() in text_lower:
                cur.execute(
                    "SELECT id, stock_name, yfin_symbol, sector FROM public.stocks WHERE stock_name ILIKE %s LIMIT 1;",
                    (canonical_name,)
                )
                row = cur.fetchone()
                if row:
                    cur.close()
                    return {
                        "stock_id": row[0],
                        "stock_name": row[1],
                        "yfin_symbol": row[2],
                        "sector": row[3],
                        "similarity": 1.0,  # Perfect match via alias
                        "match_type": "exact"
                    }
        cur.close()
        return None

    def find_stocks(
        self,
        title: str,
        content: str = "",
        threshold: float = STRONG_MATCH_THRESHOLD,
        max_results: int = 3
    ) -> List[Dict]:
        """
        Hybrid search: exact alias match first, then vector similarity fallback.
        """
        results = []
        
        # Step 1: Exact alias/ticker match (fast, no ML)
        search_text = f"{title} {content}".strip()
        exact = self._exact_match(search_text)
        if exact:
            exact["match_type"] = "exact"
            results.append(exact)
            return results
        
        # Step 2: Vector similarity fallback for long-form names
        embedding = self.model.encode(title if len(title.split()) > 4 else search_text).tolist()
        
        cur = self.conn.cursor()
        cur.execute(
            "SELECT * FROM public.match_stock_by_name(%s::vector, %s, %s);",
            (embedding, threshold, max_results)
        )
        rows = cur.fetchall()
        cur.close()
        
        for row in rows:
            results.append({
                "stock_id": row[0],
                "stock_name": row[1],
                "yfin_symbol": row[2],
                "sector": row[3],
                "similarity": round(row[4], 4),
                "match_type": "vector"
            })
        
        return results

    def find_stocks_multi_threshold(self, title: str, content: str = "") -> Dict:
        """
        Returns stocks with confidence tier labels for API output.
        - 'strong': exact alias match or similarity >= STRONG_MATCH_THRESHOLD
        - 'possible': similarity >= WEAK_MATCH_THRESHOLD
        """
        strong = self.find_stocks(title, content, threshold=STRONG_MATCH_THRESHOLD)
        # Only run weak search if strong search returned no results and no exact match
        if strong and strong[0].get("match_type") == "exact":
            return {"strong_matches": strong, "possible_matches": []}
        
        all_matches = self.find_stocks(title, content, threshold=WEAK_MATCH_THRESHOLD)
        weak = [m for m in all_matches if m["similarity"] < STRONG_MATCH_THRESHOLD]
        
        return {
            "strong_matches": strong,
            "possible_matches": weak
        }

    def close(self):
        if self.conn:
            self.conn.close()


def test_linker():
    """Test the entity linker with sample news titles."""
    linker = SemanticEntityLinker()
    
    test_titles = [
        "HDFC Bank posts record Q4 profits as loan growth surges",
        "RIL shares rise after Mukesh Ambani's announcement",
        "Infy beats estimates in third quarter",
        "TCS wins deal narrower than expected loss",
        "Sensex gains 500 points; SBI, Kotak lead the rally",
        "Housing Development Finance sees strong recovery in FY26",
    ]
    
    print("=== SEMANTIC ENTITY LINKER TEST ===\n")
    for title in test_titles:
        print(f"Title: {title}")
        result = linker.find_stocks_multi_threshold(title)
        if result["strong_matches"]:
            for m in result["strong_matches"]:
                match_type = m.get('match_type', 'vector')
                print(f"  STRONG [{match_type}] -> {m['stock_name']} ({m['yfin_symbol']}) | sim={m['similarity']}")
        if result["possible_matches"]:
            for m in result["possible_matches"]:
                match_type = m.get('match_type', 'vector')
                print(f"  POSSIBLE [{match_type}]-> {m['stock_name']} ({m['yfin_symbol']}) | sim={m['similarity']}")
        if not result["strong_matches"] and not result["possible_matches"]:
            print("  No stock matched (below threshold)")
        print()


if __name__ == "__main__":
    test_linker()
