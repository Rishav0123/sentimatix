
import sys
from pathlib import Path
import random

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from server.tools.technical_analysis import (
    calculate_rsi,
    calculate_macd,
    calculate_bollinger_bands,
    calculate_sma,
    calculate_ema,
    calculate_atr
)

def main():
    print("Verifying Technical Analysis Logic with Mock Data...")
    
    # Generate mock data: 100 days of prices trend upwards with some volatility
    prices = []
    base_price = 100.0
    for i in range(100):
        change = random.uniform(-2, 3) # Slight upward drift
        base_price += change
        prices.append(max(0.1, base_price))
        
    highs = [p + random.uniform(0.5, 2.0) for p in prices]
    lows = [p - random.uniform(0.5, 2.0) for p in prices]
    closes = prices # simplifying
    
    print(f"Generated {len(prices)} price points.")
    
    # Test SMA
    sma = calculate_sma(closes, 10)
    print(f"\nSMA(10) last value: {sma[-1]:.2f}")
    assert sma[-1] is not None
    
    # Test EMA
    ema = calculate_ema(closes, 10)
    print(f"EMA(10) last value: {ema[-1]:.2f}")
    assert ema[-1] is not None
    
    # Test RSI
    rsi = calculate_rsi(closes, 14)
    print(f"RSI(14) last value: {rsi[-1]:.2f}")
    if rsi[-1] is not None:
        assert 0 <= rsi[-1] <= 100
        
    # Test MACD
    macd = calculate_macd(closes)
    print(f"MACD Line: {macd['macd_line'][-1]:.2f}")
    print(f"Signal Line: {macd['signal_line'][-1]:.2f}")
    print(f"Histogram: {macd['histogram'][-1]:.2f}")
    
    # Test Bollinger Bands
    bb = calculate_bollinger_bands(closes, 20, 2.0)
    print(f"BB Upper: {bb['upper_band'][-1]:.2f}")
    print(f"BB Middle: {bb['middle_band'][-1]:.2f}")
    print(f"BB Lower: {bb['lower_band'][-1]:.2f}")
    
    if bb['upper_band'][-1] is not None:
        assert bb['upper_band'][-1] >= bb['middle_band'][-1] >= bb['lower_band'][-1]
        
    # Test ATR
    atr = calculate_atr(highs, lows, closes, 14)
    print(f"ATR(14) last value: {atr[-1]:.2f}")
    
    print("\n✅ Logic Verification Successful!")

if __name__ == "__main__":
    main()
