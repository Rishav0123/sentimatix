"""
MCP Server Client Examples

This demonstrates how to call the MCP server to perform stock analysis.
"""

import requests
from datetime import datetime, timedelta
import json

# MCP Server configuration
MCP_BASE_URL = "http://localhost:8001"
API_KEY = "stockify-mcp-2025"  # Update this to match MCP_API_KEY in .env

HEADERS = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}


def call_tool(tool_name: str, parameters: dict) -> dict:
    """Call a tool on the MCP server"""
    url = f"{MCP_BASE_URL}/call"
    payload = {
        "tool_name": tool_name,
        "parameters": parameters
    }
    
    print(f"\n{'='*80}")
    print(f"🔧 Calling tool: {tool_name}")
    print(f"📋 Parameters: {json.dumps(parameters, indent=2)}")
    print(f"{'='*80}\n")
    
    response = requests.post(url, json=payload, headers=HEADERS)
    response.raise_for_status()
    
    result = response.json()
    print(f"✅ Response:\n{json.dumps(result, indent=2)}\n")
    
    return result


def example_1_comprehensive_analysis():
    """Example 1: Comprehensive price change analysis (recommended)"""
    print("\n" + "="*80)
    print("EXAMPLE 1: Comprehensive Price Change Analysis")
    print("="*80)
    
    # Calculate date range (last 7 days)
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=7)
    
    result = call_tool(
        tool_name="explain_price_change",
        parameters={
            "symbol": "AAPL",
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        }
    )
    
    print("📊 This single call retrieved:")
    print("  • Stock summary (price changes, volatility)")
    print("  • Historical price data")
    print("  • News sentiment analysis")
    print("  • RAG-based evidence from news")
    print("  • Sentiment-price correlation")
    print("\n💡 Now feed this to an LLM to generate an explanation!")


def example_2_stock_tools():
    """Example 2: Using stock tools individually"""
    print("\n" + "="*80)
    print("EXAMPLE 2: Stock Tools")
    print("="*80)
    
    # Get stock summary
    call_tool(
        tool_name="get_stock_summary",
        parameters={
            "symbol": "TSLA",
            "period_days": 30
        }
    )
    
    # Get historical prices
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=14)
    
    call_tool(
        tool_name="get_historical_prices",
        parameters={
            "symbol": "TSLA",
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "aggregation_period": "1d"
        }
    )


def example_3_news_sentiment():
    """Example 3: News sentiment analysis"""
    print("\n" + "="*80)
    print("EXAMPLE 3: News Sentiment Analysis")
    print("="*80)
    
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=7)
    
    # Get individual news with sentiment
    call_tool(
        tool_name="get_news_sentiment",
        parameters={
            "symbol": "NVDA",
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "top_n": 5,
            "sentiment_filter": None  # Can be "positive", "negative", or "neutral"
        }
    )
    
    # Get aggregated sentiment
    call_tool(
        tool_name="get_sentiment_aggregate",
        parameters={
            "symbol": "NVDA",
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        }
    )


def example_4_rag_evidence():
    """Example 4: RAG semantic search"""
    print("\n" + "="*80)
    print("EXAMPLE 4: RAG Evidence Retrieval")
    print("="*80)
    
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=30)
    
    # Search for evidence about earnings
    call_tool(
        tool_name="get_rag_evidence",
        parameters={
            "symbol": "GOOGL",
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "query_text": "earnings report financial results revenue growth",
            "top_k": 5
        }
    )
    
    print("💡 This uses semantic search to find relevant news")
    print("   based on meaning, not just keyword matching!")


def example_5_correlation():
    """Example 5: Correlation analysis"""
    print("\n" + "="*80)
    print("EXAMPLE 5: Correlation Analysis")
    print("="*80)
    
    # Example price changes and sentiment scores
    price_changes = [1.5, -0.8, 2.3, -1.2, 0.5, 1.8, -0.3]
    sentiment_scores = [0.7, -0.4, 0.8, -0.6, 0.3, 0.9, -0.2]
    
    call_tool(
        tool_name="calculate_sentiment_price_correlation",
        parameters={
            "price_changes": price_changes,
            "sentiment_scores": sentiment_scores,
            "symbol": "MSFT"
        }
    )


def example_6_check_server_status():
    """Example 6: Check server health"""
    print("\n" + "="*80)
    print("EXAMPLE 6: Server Health Check")
    print("="*80)
    
    # Health check
    response = requests.get(f"{MCP_BASE_URL}/health")
    response.raise_for_status()
    print(f"Health: {json.dumps(response.json(), indent=2)}")
    
    # Get available tools
    response = requests.get(f"{MCP_BASE_URL}/tools")
    response.raise_for_status()
    tools = response.json()
    print(f"\nAvailable tools: {len(tools['tools'])}")
    for tool in tools['tools']:
        print(f"  • {tool['name']}: {tool['description'][:60]}...")


def example_7_llm_workflow():
    """Example 7: Complete LLM workflow"""
    print("\n" + "="*80)
    print("EXAMPLE 7: Complete LLM Workflow")
    print("="*80)
    
    # Step 1: User asks question
    user_query = "Why did Apple stock drop in the last week?"
    print(f"👤 User: {user_query}\n")
    
    # Step 2: LLM calls orchestrator tool
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=7)
    
    result = call_tool(
        tool_name="explain_price_change",
        parameters={
            "symbol": "AAPL",
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        }
    )
    
    # Step 3: LLM synthesizes response (simulated)
    print("\n🤖 LLM Response (simulated):")
    print("-" * 80)
    print(f"Based on my analysis of Apple (AAPL) from {start_date} to {end_date}:")
    print("\n📉 Price Movement:")
    if result.get("status") == "success" and "stock_summary" in result.get("result", {}):
        summary = result["result"]["stock_summary"]
        print(f"  • Price changed by {summary.get('change_percent', 'N/A')}%")
        print(f"  • Volatility: {summary.get('volatility_percent', 'N/A')}%")
    
    print("\n📰 News Sentiment:")
    if "sentiment_aggregate" in result.get("result", {}):
        agg = result["result"]["sentiment_aggregate"]
        print(f"  • Average sentiment: {agg.get('average_sentiment', 'N/A')}")
        print(f"  • News articles analyzed: {agg.get('total_articles', 0)}")
    
    print("\n🔍 Key Evidence:")
    if "rag_evidence" in result.get("result", {}):
        evidence = result["result"]["rag_evidence"]
        for i, item in enumerate(evidence[:3], 1):
            print(f"  {i}. {item.get('title', 'N/A')} ({item.get('published_at', 'N/A')})")
            print(f"     Relevance: {item.get('match_quality', 'N/A')}")
    
    print("\n📊 Correlation:")
    if "correlation" in result.get("result", {}):
        corr = result["result"]["correlation"]
        print(f"  • Sentiment-Price Correlation: {corr.get('correlation_coefficient', 'N/A')}")
        print(f"  • Strength: {corr.get('strength', 'N/A')}")
    
    print("-" * 80)


def main():
    """Run all examples"""
    print("\n" + "="*80)
    print("MCP SERVER CLIENT EXAMPLES")
    print("="*80)
    print("\n⚠️  Make sure:")
    print("  1. MCP server is running (python server/main.py)")
    print("  2. Update API_KEY in this file")
    print("  3. Vector DB is populated (run scripts/ingest_historical.py)")
    
    try:
        # Check server is running
        response = requests.get(MCP_BASE_URL, timeout=5)
        print(f"\n✅ Server is running: {response.json()['status']}")
    except Exception as e:
        print(f"\n❌ Server not reachable: {e}")
        print("\nStart the server with: python server/main.py")
        return
    
    # Run examples
    examples = [
        ("Comprehensive Analysis (RECOMMENDED)", example_1_comprehensive_analysis),
        ("Stock Tools", example_2_stock_tools),
        ("News Sentiment", example_3_news_sentiment),
        ("RAG Evidence", example_4_rag_evidence),
        ("Correlation", example_5_correlation),
        ("Server Status", example_6_check_server_status),
        ("LLM Workflow", example_7_llm_workflow)
    ]
    
    print("\n" + "="*80)
    print("SELECT AN EXAMPLE:")
    print("="*80)
    for i, (name, _) in enumerate(examples, 1):
        print(f"{i}. {name}")
    print("0. Run all examples")
    
    choice = input("\nEnter choice (0-7): ").strip()
    
    if choice == "0":
        for _, func in examples:
            try:
                func()
                input("\nPress Enter to continue to next example...")
            except Exception as e:
                print(f"❌ Error: {e}")
    elif choice.isdigit() and 1 <= int(choice) <= len(examples):
        try:
            examples[int(choice) - 1][1]()
        except Exception as e:
            print(f"❌ Error: {e}")
    else:
        print("Invalid choice")


if __name__ == "__main__":
    main()
