"""
Interactive Chat Interface for MCP Server

This provides a command-line chat interface to interact with the MCP server
using natural language queries.
"""

import requests
from datetime import datetime, timedelta
import json
import re
from typing import Optional

# MCP Server configuration
MCP_BASE_URL = "http://localhost:8001"
API_KEY = "stockify-mcp-2025"  # Update this to match MCP_API_KEY in .env

HEADERS = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}


class MCPChatInterface:
    """Interactive chat interface for MCP server"""
    
    def __init__(self, base_url: str = MCP_BASE_URL, api_key: str = API_KEY):
        self.base_url = base_url
        self.headers = {
            "X-API-Key": api_key,
            "Content-Type": "application/json"
        }
        self.history = []
        
    def check_connection(self) -> bool:
        """Check if MCP server is reachable"""
        try:
            response = requests.get(self.base_url, timeout=5)
            return response.status_code == 200
        except Exception:
            return False
    
    def parse_query(self, query: str) -> Optional[dict]:
        """Parse natural language query into tool call"""
        query_lower = query.lower()
        
        # Extract stock symbol
        symbol_match = re.search(r'\b([A-Z]{1,5})\b', query)
        symbol = symbol_match.group(1) if symbol_match else None
        
        # Extract time period
        days = 7  # default
        if "week" in query_lower or "7 day" in query_lower:
            days = 7
        elif "month" in query_lower or "30 day" in query_lower:
            days = 30
        elif "2 week" in query_lower or "14 day" in query_lower:
            days = 14
        elif "yesterday" in query_lower or "1 day" in query_lower:
            days = 1
        
        # Determine tool based on query intent
        if any(word in query_lower for word in ["why", "explain", "reason", "cause"]):
            # Comprehensive analysis
            if symbol:
                end_date = datetime.now().date()
                start_date = end_date - timedelta(days=days)
                return {
                    "tool_name": "explain_price_change",
                    "parameters": {
                        "symbol": symbol,
                        "start_date": start_date.isoformat(),
                        "end_date": end_date.isoformat()
                    }
                }
        
        elif any(word in query_lower for word in ["price", "stock", "performance"]):
            # Stock summary
            if symbol:
                return {
                    "tool_name": "get_stock_summary",
                    "parameters": {
                        "symbol": symbol,
                        "period_days": days
                    }
                }
        
        elif any(word in query_lower for word in ["news", "sentiment", "articles"]):
            # News sentiment
            if symbol:
                end_date = datetime.now().date()
                start_date = end_date - timedelta(days=days)
                return {
                    "tool_name": "get_news_sentiment",
                    "parameters": {
                        "symbol": symbol,
                        "start_date": start_date.isoformat(),
                        "end_date": end_date.isoformat(),
                        "top_n": 5
                    }
                }
        
        elif any(word in query_lower for word in ["find", "search", "evidence"]):
            # RAG search
            if symbol:
                end_date = datetime.now().date()
                start_date = end_date - timedelta(days=days)
                # Extract search query
                search_query = query_lower
                for word in ["find", "search", "evidence", "about", "for", symbol.lower()]:
                    search_query = search_query.replace(word, "")
                search_query = search_query.strip()
                
                return {
                    "tool_name": "get_rag_evidence",
                    "parameters": {
                        "symbol": symbol,
                        "start_date": start_date.isoformat(),
                        "end_date": end_date.isoformat(),
                        "query_text": search_query or "news",
                        "top_k": 5
                    }
                }
        
        return None
    
    def call_tool(self, tool_name: str, parameters: dict) -> dict:
        """Call a tool on the MCP server"""
        url = f"{self.base_url}/call"
        payload = {
            "tool_name": tool_name,
            "parameters": parameters
        }
        
        response = requests.post(url, json=payload, headers=self.headers)
        response.raise_for_status()
        
        return response.json()
    
    def format_response(self, tool_name: str, result: dict) -> str:
        """Format tool response into human-readable text"""
        if result.get("status") != "success":
            return f"❌ Error: {result.get('message', 'Unknown error')}"
        
        data = result.get("result", {})
        output = []
        
        if tool_name == "explain_price_change":
            # Format comprehensive analysis
            output.append("📊 COMPREHENSIVE ANALYSIS")
            output.append("=" * 80)
            
            # Stock summary
            if "stock_summary" in data:
                summary = data["stock_summary"]
                output.append(f"\n📈 Stock Performance:")
                output.append(f"  • Price Change: {summary.get('change_percent', 'N/A')}%")
                output.append(f"  • High: ${summary.get('high', 'N/A')}")
                output.append(f"  • Low: ${summary.get('low', 'N/A')}")
                output.append(f"  • Volatility: {summary.get('volatility_percent', 'N/A')}%")
                output.append(f"  • Avg Volume: {summary.get('average_volume', 'N/A'):,}")
            
            # Sentiment
            if "sentiment_aggregate" in data:
                agg = data["sentiment_aggregate"]
                output.append(f"\n📰 News Sentiment:")
                output.append(f"  • Average Sentiment: {agg.get('average_sentiment', 'N/A')}")
                output.append(f"  • Total Articles: {agg.get('total_articles', 0)}")
                output.append(f"  • Positive: {agg.get('positive_count', 0)}")
                output.append(f"  • Negative: {agg.get('negative_count', 0)}")
                output.append(f"  • Neutral: {agg.get('neutral_count', 0)}")
            
            # RAG evidence
            if "rag_evidence" in data:
                output.append(f"\n🔍 Key Evidence:")
                for i, item in enumerate(data["rag_evidence"][:5], 1):
                    output.append(f"\n  {i}. {item.get('title', 'N/A')}")
                    output.append(f"     Date: {item.get('published_at', 'N/A')}")
                    output.append(f"     Sentiment: {item.get('sentiment', 'N/A')} ({item.get('sentiment_score', 0):.2f})")
                    output.append(f"     Relevance: {item.get('match_quality', 'N/A')}")
                    output.append(f"     URL: {item.get('url', 'N/A')}")
            
            # Correlation
            if "correlation" in data:
                corr = data["correlation"]
                output.append(f"\n📊 Sentiment-Price Correlation:")
                output.append(f"  • Coefficient: {corr.get('correlation_coefficient', 'N/A')}")
                output.append(f"  • Strength: {corr.get('strength', 'N/A')}")
                output.append(f"  • R²: {corr.get('r_squared', 'N/A')}")
                if "insights" in corr:
                    output.append(f"  • Insights: {corr['insights']}")
        
        elif tool_name == "get_stock_summary":
            output.append("📈 STOCK SUMMARY")
            output.append("=" * 80)
            output.append(f"Symbol: {data.get('symbol', 'N/A')}")
            output.append(f"Price Change: {data.get('change_percent', 'N/A')}%")
            output.append(f"High: ${data.get('high', 'N/A')}")
            output.append(f"Low: ${data.get('low', 'N/A')}")
            output.append(f"Volatility: {data.get('volatility_percent', 'N/A')}%")
            output.append(f"Average Volume: {data.get('average_volume', 'N/A'):,}")
        
        elif tool_name == "get_news_sentiment":
            output.append("📰 NEWS SENTIMENT")
            output.append("=" * 80)
            for i, item in enumerate(data.get("news", [])[:5], 1):
                output.append(f"\n{i}. {item.get('title', 'N/A')}")
                output.append(f"   Date: {item.get('published_at', 'N/A')}")
                output.append(f"   Sentiment: {item.get('sentiment', 'N/A')} ({item.get('sentiment_score', 0):.2f})")
                output.append(f"   Source: {item.get('source', 'N/A')}")
        
        elif tool_name == "get_rag_evidence":
            output.append("🔍 RAG EVIDENCE")
            output.append("=" * 80)
            for i, item in enumerate(data[:5], 1):
                output.append(f"\n{i}. {item.get('title', 'N/A')}")
                output.append(f"   Date: {item.get('published_at', 'N/A')}")
                output.append(f"   Relevance: {item.get('match_quality', 'N/A')} ({item.get('relevance_score', 0):.2f})")
                output.append(f"   Sentiment: {item.get('sentiment_score', 0):.2f}")
                output.append(f"   URL: {item.get('url', 'N/A')}")
        
        else:
            output.append(json.dumps(data, indent=2))
        
        return "\n".join(output)
    
    def chat(self):
        """Main chat loop"""
        print("\n" + "="*80)
        print("MCP CHAT INTERFACE")
        print("="*80)
        print("\nℹ️  Ask questions about stocks using natural language.")
        print("\nExamples:")
        print("  • Why did AAPL drop in the last week?")
        print("  • What's the sentiment for TSLA in the last month?")
        print("  • Show me NVDA's performance over 2 weeks")
        print("  • Find news about GOOGL earnings")
        print("\nCommands:")
        print("  • 'quit' or 'exit' - Exit")
        print("  • 'help' - Show examples")
        print("  • 'history' - Show query history")
        print("="*80 + "\n")
        
        while True:
            try:
                # Get user input
                query = input("You: ").strip()
                
                if not query:
                    continue
                
                # Handle commands
                if query.lower() in ["quit", "exit"]:
                    print("Goodbye!")
                    break
                
                if query.lower() == "help":
                    print("\nExamples:")
                    print("  • Why did AAPL drop in the last week?")
                    print("  • What's the sentiment for TSLA in the last month?")
                    print("  • Show me NVDA's performance over 2 weeks")
                    print("  • Find news about GOOGL earnings")
                    continue
                
                if query.lower() == "history":
                    print("\nQuery History:")
                    for i, h in enumerate(self.history, 1):
                        print(f"{i}. {h}")
                    continue
                
                # Parse and execute query
                tool_call = self.parse_query(query)
                
                if not tool_call:
                    print("\n❌ I couldn't understand that query. Try:")
                    print("  • Include a stock symbol (e.g., AAPL, TSLA)")
                    print("  • Ask about price, sentiment, or news")
                    print("  • Type 'help' for examples\n")
                    continue
                
                # Add to history
                self.history.append(query)
                
                # Call tool
                print(f"\n🔧 Calling {tool_call['tool_name']}...\n")
                result = self.call_tool(tool_call["tool_name"], tool_call["parameters"])
                
                # Format and display response
                response = self.format_response(tool_call["tool_name"], result)
                print(f"\n{response}\n")
                print("="*80 + "\n")
                
            except KeyboardInterrupt:
                print("\n\nGoodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}\n")


def main():
    """Main entry point"""
    interface = MCPChatInterface()
    
    # Check server connection
    print("Checking MCP server connection...")
    if not interface.check_connection():
        print("❌ Cannot connect to MCP server at", MCP_BASE_URL)
        print("\nMake sure:")
        print("  1. MCP server is running (python server/main.py)")
        print("  2. Update API_KEY in this file")
        return
    
    print("✅ Connected to MCP server\n")
    
    # Start chat
    interface.chat()


if __name__ == "__main__":
    main()
