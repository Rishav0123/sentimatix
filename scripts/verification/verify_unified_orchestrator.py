
import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from server.tools.orchestrator import explain_price_change

async def main():
    print("Verifying Orchestrator with Technical Analysis...")
    
    # Needs backend connection
    import os
    if not os.getenv("BACKEND_API_URL"):
         print("Warning: BACKEND_API_URL not set, default might fail if not localhost")

    try:
        # Mocking the args typically passed to explain_price_change
        # Note: explain_price_change is an async function in the file I viewed, but in the import list it was simple. 
        # Let's check if it is async. The file says `async def explain_price_change`.
        
        from datetime import datetime
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = "2025-12-01" # Arbitrary start

        result = await explain_price_change("HDFCBANK", start_date, end_date)
        
        if "technical_analysis" in result and result["technical_analysis"]:
            ta = result["technical_analysis"]
            print("\n✅ Orchestrator returned Technical Analysis!")
            if "indicators" in ta:
                inds = ta["indicators"]
                print(f"RSI: {inds.get('rsi', {}).get('value')}")
            else:
                print("❌ Indicators missing inside TA data")
        else:
            print("\n❌ Orchestrator FAILED to return Technical Analysis")
            print("Keys found:", list(result.keys()))
            
    except Exception as e:
        print(f"❌ Error during verification: {e}")

if __name__ == "__main__":
    asyncio.run(main())
