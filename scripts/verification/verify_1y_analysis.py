import asyncio
import os
import sys
import json
from datetime import datetime, timedelta

# Add the project root and mcp directory to sys.path
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), '..'))

from mcp.server.tools.orchestrator import explain_price_change

async def verify_1y_analysis():
    all_results = {}
    for symbol in ["HDFCBANK", "TCS"]:
        print(f"\n--- Analysis for {symbol} (1 Year) ---")
        try:
            # Calculate dates for 1 year
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
            
            result = await explain_price_change(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date
            )
            all_results[symbol] = result
            
            if "error" not in result:
                insights = result.get("insights")
                if insights:
                    print(f"Recommendation: {insights.get('recommendation')}")
                    print("Market Themes:")
                    for theme in insights.get("market_themes", []):
                        print(f"- {theme}")
                else:
                    print("❌ No insights in orchestrator output!")
            else:
                print(f"Error: {result.get('error')}")
                
        except Exception as e:
            print(f"Exception: {e}")
            all_results[symbol] = {"error": str(e)}

    with open("verify_1y_output.json", "w") as f:
        json.dump(all_results, f, indent=2, default=lambda o: str(o))

if __name__ == "__main__":
    asyncio.run(verify_1y_analysis())
