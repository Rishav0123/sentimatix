"""
RAG Evidence Retrieval Tool - Semantic search for historical context
"""

from typing import Dict, Any, List, Optional
import logging
from datetime import datetime

from rag.vectordb import get_vector_db
from rag.embeddings import generate_embedding
from server.tools.symbol_utils import symbol_variants

logger = logging.getLogger(__name__)


def get_rag_evidence(
    symbol: str,
    start_date: str,
    end_date: str,
    query_text: str,
    top_k: int = 6
) -> List[Dict[str, Any]]:
    """
    Retrieve relevant historical evidence using semantic search.
    
    This tool performs RAG (Retrieval-Augmented Generation) to find news articles
    and historical context that are semantically similar to the query.
    
    Args:
        symbol: Stock symbol to filter by
        start_date: Start date for filtering (YYYY-MM-DD)
        end_date: End date for filtering (YYYY-MM-DD)
        query_text: Natural language query (e.g., "reasons for price drop", "earnings miss")
        top_k: Number of results to return (default: 6)
    
    Returns:
        List of relevant documents with similarity scores, titles, URLs, and metadata
    """
    try:
        logger.info(f"RAG search: symbol={symbol}, query='{query_text[:50]}...', period={start_date} to {end_date}")
        
        # Expand query with domain-specific banking terms and company alias heuristics
        banking_terms = [
            "earnings", "quarterly results", "Q1", "Q2", "Q3", "Q4",
            "NIM", "net interest margin", "provisioning", "provisions",
            "asset quality", "GNPA", "NNPA", "slippages", "delinquencies",
            "CASA", "deposit growth", "credit growth", "loan growth",
            "RBI", "regulatory", "directive", "circular", "penalty",
            "capital adequacy", "CAR", "capital raise", "AT1", "QIP",
            "liquidity", "LCR", "margin", "NPA"
        ]
        # Heuristic alias: convert HDFCBANK -> "HDFC Bank" (and similar for *BANK, *LIFE) for better matching
        disp_symbol = symbol_variants(symbol)[-1]
        alias_terms: List[str] = []
        if disp_symbol:
            u = disp_symbol.upper()
            if u.endswith("BANK") and len(u) > 4:
                alias_terms.append((u[:-4] + " Bank").title())
            if u.endswith("LIFE") and len(u) > 4:
                alias_terms.append((u[:-4] + " Life").title())
        expanded_query = " ".join([query_text] + banking_terms + alias_terms)
        
        # Generate query embedding on the expanded query
        query_embedding = generate_embedding(expanded_query)
        
        # Perform adaptive vector search across symbol variants (.NS & bare)
        vector_db = get_vector_db()
        # Try progressively lower similarity thresholds to improve recall
        threshold_sequence = [0.7, 0.65, 0.6, 0.55, 0.5]
        all_results = []
        seen_ids = set()
        for threshold in threshold_sequence:
            for sym in symbol_variants(symbol):
                variant_results = vector_db.semantic_search(
                    query_embedding=query_embedding,
                    symbol=sym,
                    start_date=start_date,
                    end_date=end_date,
                    top_k=top_k,
                    min_similarity=threshold
                )
                for r in variant_results:
                    nid = r.get("news_id")
                    if nid and nid not in seen_ids:
                        seen_ids.add(nid)
                        r["_variant_symbol"] = sym
                        r["_variant_threshold"] = threshold
                        all_results.append(r)
            # If we have at least 3 results after this threshold, stop early
            if len(all_results) >= 3:
                break
        # Compute final scores with recency and symbol boosts, then sort
        def _compute_final_score(doc: Dict[str, Any]) -> float:
            sim = float(doc.get("similarity_score", 0.0))
            # Recency weight: exponential decay with 30-day half-life
            try:
                pub = doc.get("published_at")
                pub_dt = datetime.fromisoformat(str(pub).replace("Z", "+00:00")) if pub else None
                end_dt = datetime.fromisoformat(end_date)
                if pub_dt is None:
                    age_days = 999.0
                else:
                    age_days = max(0.0, (end_dt - pub_dt).days)
                recency_weight = 0.5 ** (age_days / 30.0)
            except Exception:
                recency_weight = 1.0
            # Symbol boost: exact symbol or alias mention
            doc_sym = (doc.get("symbol") or "").upper()
            variants = [v.upper() for v in symbol_variants(symbol)]
            symbol_boost = 1.0
            if doc_sym and doc_sym in variants:
                symbol_boost *= 1.08
            # Text mention boost (e.g., "HDFC Bank")
            hay = " ".join([
                str(doc.get("title", "")),
                str(doc.get("content_preview", ""))
            ]).lower()
            mentions = [a.lower() for a in alias_terms if a]
            if any(m in hay for m in mentions):
                symbol_boost *= 1.05
            final = sim * recency_weight * symbol_boost
            return final

        for d in all_results:
            d["_final_score"] = _compute_final_score(d)
        results = sorted(all_results, key=lambda d: d.get("_final_score", d.get("similarity_score", 0)), reverse=True)[:top_k]
        logger.info(
            f"Variant search collected {len(all_results)} raw results; returning top {len(results)} (thresholds tried: {threshold_sequence})"
        )
        
        if not results:
            logger.info(f"No RAG results found for {symbol} with query '{query_text[:30]}...'. Attempting fallback search without symbol filter...")
            try:
                # Broader candidate pool with a lower threshold to capture weaker but relevant matches
                fallback_results = vector_db.semantic_search(
                    query_embedding=query_embedding,
                    symbol=None,
                    start_date=start_date,
                    end_date=end_date,
                    top_k=top_k * 3,  # broader candidate pool
                    min_similarity=0.5  # lower threshold to increase recall
                )
                if fallback_results:
                    filtered = []
                    # Build simple text needles, including spaced/company-like variants
                    disp, yfin = symbol_variants(symbol)[-1], symbol_variants(symbol)[0]
                    # Base needles: exact symbol, bare symbol
                    needles = set()
                    needles.add((symbol or "").lower())
                    needles.add((symbol or "").lower().replace(".ns", ""))
                    needles.add((yfin or "").lower())
                    # Heuristic spaced forms (e.g., HDFCBANK -> "HDFC Bank")
                    bare = (disp or "").upper()
                    if bare.endswith("BANK") and len(bare) > 4:
                        spaced = bare[:-4] + " Bank"
                        needles.add(spaced.lower().strip())
                    if bare.endswith("LIFE") and len(bare) > 4:
                        spaced = bare[:-4] + " Life"
                        needles.add(spaced.lower().strip())
                    # Filter based on presence of any needle in title/content/symbol
                    for row in fallback_results:
                        haystack = " ".join([
                            str(row.get("title", "")),
                            str(row.get("content_preview", "")),
                            str(row.get("symbol", ""))
                        ]).lower()
                        if any(n in haystack for n in needles):
                            filtered.append(row)
                    # Rank filtered by similarity score
                    results = sorted(filtered, key=lambda d: d.get("similarity_score", 0), reverse=True)[:top_k]
                    logger.info(f"Fallback candidates: {len(fallback_results)}; filtered matches containing '{symbol}': {len(filtered)}; returning {len(results)}")
            except Exception as fe:
                logger.warning(f"Fallback RAG search failed: {fe}")
        if not results:
            logger.info(f"RAG evidence still empty after fallback for {symbol}")
            return []
        
        # Format results for LLM consumption
        evidence = []
        for i, doc in enumerate(results, 1):
            final_score = float(doc.get("_final_score", doc.get("similarity_score", 0)))
            evidence.append({
                "rank": i,
                "title": doc.get("title"),
                "summary": doc.get("content_preview"),
                "url": doc.get("url"),
                "source": doc.get("source"),
                "published_at": doc.get("published_at"),
                "sentiment": doc.get("sentiment"),
                "sentiment_score": doc.get("sentiment_score"),
                "relevance_score": round(final_score, 3),
                "raw_similarity": doc.get("similarity_score"),
                "match_quality": _get_match_quality(final_score)
            })

        logger.info(
            f"RAG returned {len(evidence)} evidence items (avg relevance: {sum(e['relevance_score'] for e in evidence) / len(evidence):.2f})"
        )

        return evidence
        
    except Exception as e:
        logger.error(f"Error in get_rag_evidence: {e}")
        return [{"error": str(e)}]


def _get_match_quality(similarity_score: float) -> str:
    """Convert similarity score to human-readable quality"""
    if similarity_score >= 0.9:
        return "EXCELLENT"
    elif similarity_score >= 0.8:
        return "HIGH"
    elif similarity_score >= 0.7:
        return "GOOD"
    elif similarity_score >= 0.6:
        return "MODERATE"
    else:
        return "LOW"


def get_rag_stats() -> Dict[str, Any]:
    """
    Get statistics about the RAG system.
    
    Returns:
        Dict with total embeddings, symbols, and database info
    """
    try:
        vector_db = get_vector_db()
        stats = vector_db.get_stats()
        
        return {
            "rag_system": "operational",
            "vector_db_stats": stats,
            "embedding_model": "text-embedding-3-small",
            "vector_dimension": 1536
        }
        
    except Exception as e:
        logger.error(f"Error getting RAG stats: {e}")
        return {"error": str(e)}


# Tool Schema for MCP
RAG_TOOLS_SCHEMA = [
    {
        "name": "get_rag_evidence",
        "description": "Retrieve semantically relevant historical news and context using RAG (Retrieval-Augmented Generation). Use this to find evidence for price movements, events, or trends.",
        "parameters": {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "Stock symbol to search for (e.g., AAPL, TSLA)"
                },
                "start_date": {
                    "type": "string",
                    "description": "Start date for filtering in YYYY-MM-DD format"
                },
                "end_date": {
                    "type": "string",
                    "description": "End date for filtering in YYYY-MM-DD format"
                },
                "query_text": {
                    "type": "string",
                    "description": "Natural language query describing what evidence to find (e.g., 'reasons for price drop', 'earnings announcements', 'regulatory issues')"
                },
                "top_k": {
                    "type": "integer",
                    "description": "Number of results to return (default: 6)",
                    "default": 6,
                    "minimum": 1,
                    "maximum": 20
                }
            },
            "required": ["symbol", "start_date", "end_date", "query_text"]
        }
    },
    {
        "name": "get_rag_stats",
        "description": "Get statistics about the RAG system (total embeddings, coverage, etc.)",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    }
]
