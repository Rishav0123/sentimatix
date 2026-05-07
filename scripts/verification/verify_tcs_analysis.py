import asyncio
import os
import sys
import json
from datetime import datetime

# Add the project root and mcp directory to sys.path
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), '..'))

from mcp.server.tools.enhanced_analysis import analyze_stock_enhanced

async def test_tcs_analysis():
    print("Testing TCS Analysis for 1 year...")
    try:
        # Run enhanced analysis for TCS for 1 year
        result = await analyze_stock_enhanced(symbol="TCS", period="1y", analysis_type="detailed")
        
        if result.get("success"):
            data = result["data"]
            print(f"Success! Analyzed {data['stock_info']['symbol']}")
            print(f"Current Price: {data['stock_info']['current_price']}")
            print(f"Performance: {data['performance']['change_percent']}% ({data['performance']['direction']})")
            
            sentiment = data['sentiment_summary']
            print(f"Sentiment: {sentiment['interpretation']} ({sentiment['overall_score']}) based on {sentiment['article_count']} articles")
            
            print("\nKey Events/Evidence (Top 10):")
            key_events = data.get('key_events', [])
            if not key_events:
                print("No key events found.")
            else:
                for i, event in enumerate(key_events[:10], 1):
                    print(f"{i}. [{event['date']}] {event['title']} (Source: {event['source']}, Relevance: {event['relevance_score']})")
            
            print("\nBottom Line:")
            print(data['insights']['bottom_line'])
            
            # Print news article count before filtering
            # We need to check the sentiment_summary article_count
            print(f"\nTotal articles in sentiment aggregate: {data['sentiment_summary']['article_count']}")
            
            # Try to save, but handle errors
            try:
                def default_dump(obj):
                    if hasattr(obj, '__dict__'):
                        return obj.__dict__
                    return str(obj)
                with open("tcs_verification_result.json", "w") as f:
                    json.dump(result, f, indent=2, default=default_dump)
                print("\nFull result saved to tcs_verification_result.json")
            except Exception as se:
                print(f"\nCould not save full JSON: {se}")
        else:
            print(f"Analysis failed: {result.get('message')}")
            
    except Exception as e:
        print(f"Error during verification: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_tcs_analysis())
