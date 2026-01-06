
import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from server.tools.enhanced_analysis import analyze_stock_enhanced

async def main():
    print("Verifying Enhanced Analysis with Technical Data...")
    
    # Needs backend connection
    import os
    if not os.getenv("BACKEND_API_URL"):
         print("Warning: BACKEND_API_URL not set, default might fail if not localhost")

    try:
        result = await analyze_stock_enhanced("HDFCBANK", period="1m")
        
        if not result["success"]:
            print(f"❌ Analysis failed: {result.get('message')}")
            return

        data = result["data"]
        print(f"\nAnalysis for: {data['stock_info']['symbol']}")
        print(f"Price: {data['stock_info']['formatted_price']}")
        
        # Check Technical Analysis
        if "technical_analysis" in data and data["technical_analysis"]:
            ta = data["technical_analysis"]
            print("\n✅ Technical Analysis Data Found!")
            if "indicators" in ta:
                inds = ta["indicators"]
                print(f"RSI: {inds.get('rsi', {}).get('value')} ({inds.get('rsi', {}).get('condition')})")
                print(f"MACD: {inds.get('macd', {}).get('trend')}")
                print(f"Bollinger Width: {inds.get('bollinger_bands', {}).get('width_pct')}%")
            else:
                print("❌ 'indicators' key missing in technical_analysis")
        else:
            print("\n❌ Technical Analysis Data MISSING in response")
            
    except Exception as e:
        print(f"❌ Error during verification: {e}")

if __name__ == "__main__":
    asyncio.run(main())
