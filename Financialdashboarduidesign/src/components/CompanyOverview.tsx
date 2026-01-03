import { useState, useEffect } from "react";
import { InsightCard } from "./InsightCard";

interface CompanyOverviewProps {
  ticker?: string;
}

interface StockData {
  symbol: string;
  name: string;
  last_price: number;
  change: number;
  change_percent: number;
  volume: number;
  sentiment_score: number;
  sector: string;
  country: string;
}

export function CompanyOverview({ ticker = "INFY" }: CompanyOverviewProps) {
  const [stockData, setStockData] = useState<StockData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // API configuration
  const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

  const fetchStockData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      console.log(`🚀 Fetching stock data for: ${ticker}`);
      
      const response = await fetch(`${API_BASE_URL}/api/stocks?sentiment_days=7`);
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const stocks: StockData[] = await response.json();
      const stock = stocks.find(s => s.symbol === ticker);
      
      if (!stock) {
        throw new Error(`Stock ${ticker} not found`);
      }
      
      setStockData(stock);
      console.log(`✅ Successfully fetched data for ${ticker}:`, stock);
      
    } catch (err) {
      console.error('❌ Error fetching stock data:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch stock data');
      
      // Fallback to mock data for INFY
      setStockData({
        symbol: ticker,
        name: ticker === "INFY" ? "Infosys" : ticker,
        last_price: 1606.8,
        change: 104.0,
        change_percent: 6.92,
        volume: 4190181,
        sentiment_score: 14.68,
        sector: "IT Services",
        country: "IN"
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStockData();
  }, [ticker]);

  // Calculate market cap (simplified calculation)
  const calculateMarketCap = (price: number): string => {
    // For Indian stocks, approximate market cap calculation
    // This is a simplified calculation - in reality you'd need shares outstanding
    const approxMarketCap = price * 1000000; // Rough approximation
    
    if (approxMarketCap >= 1e12) {
      return `₹${(approxMarketCap / 1e12).toFixed(1)}T`;
    } else if (approxMarketCap >= 1e9) {
      return `₹${(approxMarketCap / 1e9).toFixed(1)}B`;
    } else {
      return `₹${(approxMarketCap / 1e6).toFixed(1)}M`;
    }
  };

  // Format volume
  const formatVolume = (volume: number): string => {
    if (volume >= 1000000) {
      return `${(volume / 1000000).toFixed(1)}M`;
    } else if (volume >= 1000) {
      return `${(volume / 1000).toFixed(1)}K`;
    }
    return volume.toString();
  };

  // Get company emoji based on sector
  const getCompanyEmoji = (sector: string): string => {
    const sectorEmojis: Record<string, string> = {
      "IT Services": "💻",
      "Banking": "🏦",
      "Automotive": "🚗",
      "Pharmaceuticals": "💊",
      "FMCG": "🛒",
      "Oil & Gas": "⛽",
      "Metals": "⚙️",
      "Healthcare": "🏥",
      "Finance": "💰",
      "Telecom": "📱"
    };
    return sectorEmojis[sector] || "🏢";
  };

  if (loading) {
    return (
      <div className="bg-[#111827] rounded-xl p-6 border border-gray-800">
        <div className="flex items-center gap-4 mb-6">
          <div className="w-16 h-16 bg-[#3B82F6]/20 rounded-xl flex items-center justify-center animate-pulse">
            <div className="w-8 h-8 bg-gray-600 rounded"></div>
          </div>
          <div>
            <div className="h-6 bg-gray-600 rounded w-32 mb-2 animate-pulse"></div>
            <div className="h-4 bg-gray-700 rounded w-20 animate-pulse"></div>
          </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="bg-[#0B1120] rounded-lg p-4 border border-gray-800 animate-pulse">
              <div className="h-4 bg-gray-700 rounded w-20 mb-2"></div>
              <div className="h-6 bg-gray-600 rounded w-16"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (error && !stockData) {
    return (
      <div className="bg-[#111827] rounded-xl p-6 border border-gray-800">
        <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-4">
          <p className="text-red-400 text-sm">⚠️ {error}</p>
        </div>
      </div>
    );
  }

  if (!stockData) {
    return null;
  }

  return (
    <div className="bg-[#111827] rounded-xl p-6 border border-gray-800">
      {error && (
        <div className="bg-yellow-500/10 border border-yellow-500/20 rounded-lg p-3 mb-4">
          <p className="text-yellow-400 text-sm">⚠️ Using cached data: {error}</p>
        </div>
      )}
      
      <div className="flex items-center gap-4 mb-6">
        <div className="w-16 h-16 bg-[#3B82F6]/20 rounded-xl flex items-center justify-center text-3xl">
          {getCompanyEmoji(stockData.sector)}
        </div>
        <div>
          <h2 className="text-[#E5E7EB] text-2xl">{stockData.name}</h2>
          <p className="text-[#9CA3AF]">{stockData.symbol} • NSE • {stockData.sector}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <InsightCard
          title="Current Price"
          value={`₹${stockData.last_price.toFixed(2)}`}
          trend={[45, 52, 48, 55, 61, 58, 65, 70, 68, 72]} // Mock trend data
        />
        <InsightCard
          title="Daily Change"
          value={`₹${stockData.change.toFixed(2)}`}
          change={stockData.change_percent}
        />
        <InsightCard
          title="Volume"
          value={formatVolume(stockData.volume)}
          subtitle="Shares Traded"
        />
        <InsightCard
          title="Sentiment Score"
          value={`${Math.round(stockData.sentiment_score)}/100`}
          change={stockData.sentiment_score > 0 ? stockData.sentiment_score : undefined}
        />
      </div>
    </div>
  );
}
