"""
Quick demo of MCP system capabilities
"""
import requests
import json

MCP_URL = "http://localhost:8001/call"
API_KEY = "stockify-mcp-2025"
headers = {"X-API-Key": API_KEY}

print("=" * 80)
print("MCP + RAG SYSTEM DEMO")
print("=" * 80)

# Test 1: RAG Stats
print("\n1. Vector Database Stats:")
r = requests.post(MCP_URL, json={"name": "get_rag_stats", "arguments": {}}, headers=headers)
stats = r.json()["result"]["vector_db_stats"]
print(f"   - Total embeddings: {stats['total_embeddings']}")
print(f"   - Unique symbols: {stats['unique_symbols']}")
print(f"   - Vector dimension: {stats['vector_dimension']}")

# Test 2: News Sentiment for HDFC Bank
print("\n2. News Sentiment Analysis (HDFCBANK):")
r = requests.post(MCP_URL, json={
    "name": "get_news_sentiment",
    "arguments": {
        "symbol": "HDFCBANK",
        "start_date": "2025-11-10",
        "end_date": "2025-11-17",
        "top_n": 3
    }
}, headers=headers)
news = r.json()["result"]
print(f"   - Found {len(news)} news articles")
for i, article in enumerate(news[:2], 1):
    print(f"   {i}. {article['title'][:60]}...")
    print(f"      Sentiment: {article['sentiment']} ({article['sentiment_score']:.2f})")

# Test 3: Sentiment Aggregate
print("\n3. Sentiment Aggregate:")
r = requests.post(MCP_URL, json={
    "name": "get_sentiment_aggregate",
    "arguments": {
        "symbol": "HDFCBANK",
        "start_date": "2025-10-30",
        "end_date": "2025-11-17"
    }
}, headers=headers)
agg = r.json()["result"]
print(f"   - Total articles: {agg['total_articles']}")
print(f"   - Average sentiment: {agg['avg_sentiment']:.3f}")
print(f"   - Positive: {agg['sentiment_breakdown']['positive_pct']:.1f}%")
print(f"   - Neutral: {agg['sentiment_breakdown']['neutral_pct']:.1f}%")

print("\n" + "=" * 80)
print("✅ MCP System is operational!")
print("=" * 80)
print("\nNote: Stock price data requires symbol format alignment")
print("      RAG evidence requires matching symbols in vector DB")
