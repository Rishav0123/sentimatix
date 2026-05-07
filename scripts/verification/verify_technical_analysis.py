
import asyncio
import sys
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from server.tools.technical_analysis import get_technical_analysis

async def main():
    print("Verifying Technical Analysis Tools...")
    
    symbol = "HDFCBANK"
    print(f"\n1. Fetching Technical Analysis for {symbol}...")
    
    try:
        result = await get_technical_analysis(symbol=symbol, period_days=60)
        
        if "error" in result:
            print(f"Error: {result['error']}")
        else:
            print(f"Success! Analyzed {result['symbol']} as of {result['date']}")
            print(f"Latest Price: {result['price']}")
            
            indicators = result["indicators"]
            
            print("\n--- RSI ---")
            rsi = indicators["rsi"]
            print(f"RSI: {rsi['value']} ({rsi['condition']})")
            
            print("\n--- MACD ---")
            macd = indicators["macd"]
            print(f"MACD Line: {macd['line']}")
            print(f"Signal: {macd['signal']}")
            print(f"Histogram: {macd['histogram']} ({macd['trend']})")
            
            print("\n--- Bollinger Bands ---")
            bb = indicators["bollinger_bands"]
            print(f"Upper: {bb['upper']}")
            print(f"Middle: {bb['middle']}")
            print(f"Lower: {bb['lower']}")
            print(f"Width: {bb['width_pct']}%")
            
            print("\n--- Moving Averages ---")
            ma = indicators["moving_averages"]
            print(f"SMA 50: {ma['sma_50']}")
            print(f"EMA 20: {ma['ema_20']}")
            print(f"Price vs SMA50: {ma['price_vs_sma50']}")
            
            print("\n--- Volatility ---")
            vol = indicators["volatility"]
            print(f"ATR: {vol['atr']}")

            # Basic validation
            if rsi['value'] is not None and not (0 <= rsi['value'] <= 100):
                print("WARNING: RSI out of range [0, 100]")
            
    except Exception as e:
        print(f"Exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
