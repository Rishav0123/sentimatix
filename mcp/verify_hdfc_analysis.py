import asyncio
import os
import sys
import json
from datetime import datetime

# Add the project root and mcp directory to sys.path
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), '..'))

from mcp.server.tools.enhanced_analysis import analyze_stock_enhanced

async def test_hdfc_analysis():
    symbol = "HDFCBANK"
    print(f"Testing {symbol} Analysis for 6 months...")
    try:
        # Run enhanced analysis for HDFCBANK for 6 months
        result = await analyze_stock_enhanced(symbol=symbol, period="6m", analysis_type="detailed")
        
        if result.get("success"):
            data = result["data"]
            print(f"Success! Analyzed {data['stock_info']['symbol']}")
            
            insights = data.get('insights', {})
            print(f"\nRecommendation: {insights.get('recommendation')} (Confidence: {insights.get('confidence_level')})")
            
            print("\nMarket Themes:")
            themes = insights.get('market_themes', [])
            for i, theme in enumerate(themes, 1):
                print(f"{i}. {theme}")
                
            with open("hdfc_verification_result.json", "w") as f:
                json.dump(result, f, indent=2, default=lambda o: str(o))
            print("\nFull result saved to hdfc_verification_result.json")
        else:
            print(f"Analysis failed: {result.get('message')}")
            
    except Exception as e:
        print(f"Error during verification: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_hdfc_analysis())
