"""
Symbol normalization helpers to bridge backend and RAG conventions.

Conventions observed:
- Backend price/news endpoints accept bare symbols (e.g., HDFCBANK) and internally match both with and without ".NS".
- yfinance-style symbols often include the ".NS" suffix for Indian equities (e.g., HDFCBANK.NS).
- RAG embeddings typically stored with the yfinance-style symbol.

This module provides helpers to normalize and generate variants safely.
"""

from typing import Tuple, List


def normalize_symbol(symbol: str) -> Tuple[str, str]:
    """
    Return a tuple of (display_symbol, yfin_symbol).

    - display_symbol: symbol without the .NS suffix (e.g., "HDFCBANK")
    - yfin_symbol: symbol guaranteed to have .NS suffix (e.g., "HDFCBANK.NS")
    """
    s = (symbol or "").strip().upper()
    if not s:
        return "", ""
    if s.endswith(".NS"):
        return s[:-3], s
    return s, f"{s}.NS"


def symbol_variants(symbol: str) -> List[str]:
    """
    Return common variants to try across systems.

    Example: "HDFCBANK" -> ["HDFCBANK", "HDFCBANK.NS"]
             "HDFCBANK.NS" -> ["HDFCBANK.NS", "HDFCBANK"]
    """
    disp, yfin = normalize_symbol(symbol)
    variants = []
    if yfin:
        variants.append(yfin)
    if disp:
        variants.append(disp)
    # Maintain order: prefer yfin first for RAG matches
    # Ensure uniqueness while preserving order
    seen = set()
    ordered = []
    for v in variants:
        if v and v not in seen:
            seen.add(v)
            ordered.append(v)
    return ordered
