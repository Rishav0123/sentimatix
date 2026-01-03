import { useState, useEffect } from "react";
import { MarketIndexCard } from "./MarketIndexCard";

interface MarketIndex {
  symbol: string;
  name: string;
  value: number;
  change: number;
  change_percent: number;
  exchange: string;
  country: string;
  sector_coverage: string;
  currency: string;
}

interface PricePoint {
  date: string;
  close: number;
  volume: number;
}

export function MarketIndices() {
  const [indices, setIndices] = useState<MarketIndex[]>([]);
  const [priceData, setPriceData] = useState<Record<string, PricePoint[]>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch price history for a specific symbol
  const fetchPriceHistory = async (symbol: string): Promise<PricePoint[]> => {
    try {
      console.log(`📈 Generating mock price data for index ${symbol}...`);
      
      // For market indices, we'll use mock data since they're not in the stocks table
      // The stocks API is designed for individual stocks with UUID IDs, not market indices
      return generateMockPriceData();
      
    } catch (err) {
      console.warn(`Error generating price data for ${symbol}:`, err);
      return generateMockPriceData();
    }
  };

  // Generate mock price data as fallback
  const generateMockPriceData = (basePrice?: number): PricePoint[] => {
    const data: PricePoint[] = [];
    const startPrice = basePrice || (1000 + Math.random() * 500);
    
    for (let i = 29; i >= 0; i--) {
      const date = new Date();
      date.setDate(date.getDate() - i);
      
      const variation = (Math.random() - 0.5) * 0.03; // ±1.5% daily variation
      const trendFactor = Math.sin((30 - i) / 30 * Math.PI) * 0.1; // Overall upward trend
      const price = startPrice * (1 + variation + trendFactor);
      
      data.push({
        date: date.toISOString().split('T')[0],
        close: price,
        volume: Math.floor(Math.random() * 1000000) + 500000
      });
    }
    
    return data;
  };

  useEffect(() => {
    const fetchIndicesAndPrices = async () => {
      try {
        setLoading(true);
        console.log('📊 Fetching market indices from API...');
        
        const API_BASE_URL = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/+$/, '').replace(/\/api$/, '');
        const response = await fetch(`${API_BASE_URL}/api/indices`);
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('✅ Market indices data received:', data);
        
        // Show only top 4 indices
        const topIndices = data.slice(0, 4);
        setIndices(topIndices);
        
        // Fetch price history for each index
        const pricePromises = topIndices.map(async (index: MarketIndex) => {
          const prices = await fetchPriceHistory(index.symbol);
          return { symbol: index.symbol, prices };
        });
        
        const priceResults = await Promise.all(pricePromises);
        const priceMap: Record<string, PricePoint[]> = {};
        
        priceResults.forEach(({ symbol, prices }) => {
          priceMap[symbol] = prices;
        });
        
        setPriceData(priceMap);
        setError(null);
        
      } catch (err) {
        console.error('❌ Error fetching market indices:', err);
        setError('Failed to load market indices');
        
        // Fallback to mock data - top 4 indices
        const mockIndices = [
          {
            symbol: "NIFTY50",
            name: "NIFTY 50",
            value: 24500.75,
            change: 125.30,
            change_percent: 0.51,
            exchange: "NSE",
            country: "India",
            sector_coverage: "Large Cap",
            currency: "INR"
          },
          {
            symbol: "SENSEX",
            name: "BSE SENSEX",
            value: 80250.40,
            change: -85.20,
            change_percent: -0.11,
            exchange: "BSE",
            country: "India",
            sector_coverage: "Large Cap",
            currency: "INR"
          },
          {
            symbol: "CNXIT",
            name: "NIFTY IT",
            value: 42150.25,
            change: 125.5,
            change_percent: 0.3,
            exchange: "NSE",
            country: "India",
            sector_coverage: "Information Technology",
            currency: "INR"
          },
          {
            symbol: "NIFTYBANK",
            name: "NIFTY BANK",
            value: 52340.80,
            change: -245.60,
            change_percent: -0.47,
            exchange: "NSE",
            country: "India",
            sector_coverage: "Banking",
            currency: "INR"
          }
        ];
        
        setIndices(mockIndices);
        
        // Generate mock price data for fallback indices
        const mockPriceMap: Record<string, PricePoint[]> = {};
        mockIndices.forEach(index => {
          mockPriceMap[index.symbol] = generateMockPriceData();
        });
        setPriceData(mockPriceMap);
        
      } finally {
        setLoading(false);
      }
    };

    fetchIndicesAndPrices();
  }, []);

  if (loading) {
    return (
      <div className="space-y-4 py-6">
        <div className="flex items-center justify-between px-4">
          <h3 className="text-white text-xl font-semibold">Market Indices</h3>
        </div>
        <div className="flex gap-2 w-full px-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="bg-[#1E293B] rounded-md p-1.5 animate-pulse flex-1 h-20">
              <div className="flex justify-between mb-1">
                <div className="h-2 bg-gray-600 rounded w-8"></div>
                <div className="h-2 bg-gray-700 rounded w-6"></div>
              </div>
              <div className="h-8 bg-gray-700/50 rounded mb-1"></div>
              <div className="text-center">
                <div className="h-2 bg-gray-600 rounded w-12 mx-auto"></div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4 py-6">
      <div className="flex items-center justify-between px-4">
        <h3 className="text-white text-xl font-semibold">Market Indices</h3>
        {error && (
          <span className="text-amber-400 text-sm">Using fallback data</span>
        )}
      </div>

      <div className="flex gap-2 w-full px-4">
        {indices.map((index) => {
          const indexPriceData = priceData[index.symbol] || [];
          const pricePoints = indexPriceData.map(p => p.close);
          
          return (
            <MarketIndexCard
              key={index.symbol}
              name={index.name}
              ticker={index.symbol}
              value={`${index.currency === 'INR' ? '₹' : '$'}${index.value.toLocaleString()}`}
              change={index.change_percent}
              priceData={pricePoints}
            />
          );
        })}
      </div>
    </div>
  );
}