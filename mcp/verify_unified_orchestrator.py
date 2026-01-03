import asyncio
import os
import sys
import json
from datetime import datetime, timedelta

# Add the project root and mcp directory to sys.path
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), '..'))

from mcp.server.tools.orchestrator import explain_price_change
import mcp.server.tools.enhanced_analysis as ea
print(f"DEBUG: enhanced_analysis file: {ea.__file__}")
import server.tools.enhanced_analysis as sea
print(f"DEBUG: server.tools.enhanced_analysis file: {sea.__file__ if 'server.tools.enhanced_analysis' in sys.modules else 'NOT LOADED'}")

async def verify_unified_orchestrator():
    symbol = "HDFCBANK"
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=180)).strftime("%Y-%m-%d")
    
    print(f"Testing unified explain_price_change for {symbol} ({start_date} to {end_date})...")
    try:
        result = await explain_price_change(symbol, start_date, end_date)
        
        print("\nTool Status:")
        print(json.dumps(result.get("tool_status"), indent=2))
        
        print("\nInsights Found:")
        insights = result.get("insights")
        if insights:
            print(f"Recommendation: {insights.get('recommendation')}")
            print("Market Themes:")
            for theme in insights.get("market_themes", []):
                print(f"- {theme}")
        else:
            print("❌ No insights found in unified output!")
            
        with open("unified_orchestrator_verify.json", "w") as f:
            json.dump(result, f, indent=2, default=lambda o: str(o))
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(verify_unified_orchestrator())
