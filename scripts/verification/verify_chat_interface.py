
import sys
from pathlib import Path
from unittest.mock import MagicMock

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from client.chat_interface import MCPChatInterface

def main():
    print("Verifying Chat Interface Parsing Logic...")
    
    interface = MCPChatInterface()
    
    # Test queries
    queries = [
        "give me technical analysis for HDFC",
        "what is the RSI for TCS",
        "show me MACD and bollinger bands for RELIANCE",
        "technical indicators for INFY"
    ]
    
    for q in queries:
        print(f"\nQuery: '{q}'")
        parsed = interface.parse_query(q)
        if parsed and parsed['tool_name'] == 'get_technical_analysis':
            print(f"✅ Correctly parsed as 'get_technical_analysis' for symbol: {parsed['parameters']['symbol']}")
        else:
            print(f"❌ Failed to parse correctly. Result: {parsed}")

if __name__ == "__main__":
    main()
