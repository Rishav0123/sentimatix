import { useState, useEffect } from "react";
import { TrendingUp, TrendingDown, RefreshCw } from "lucide-react";

interface TopMover {
  ticker: string;
  name: string;
  change: number;
  sentiment: number;
  sector: string;
  country: string;
}

interface TopMoversAPIResponse {
  data: TopMover[];
  meta: {
    period_days: number;
    limit: number;
    sentiment_column: string;
    price_date: string;
  };
}

export function TopMovers() {
  const [topMovers, setTopMovers] = useState<TopMover[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<string>("");
  const [sentimentPeriod, setSentimentPeriod] = useState<7 | 30>(7);

  // API configuration
  const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

  const fetchTopMovers = async () => {
    try {
      setLoading(true);
      setError(null);
      
      console.log('📈 Fetching top movers by sentiment...');
      
      const response = await fetch(`${API_BASE_URL}/api/top-movers-sentiment?days=${sentimentPeriod}&limit=5`);
      
      if (!response.ok) {
        throw new Error(`API Error: ${response.status} ${response.statusText}`);
      }
      
      const apiData: TopMoversAPIResponse = await response.json();
      
      console.log('✅ Top movers API response:', apiData);
      
      setTopMovers(apiData.data);
      setLastUpdated(new Date().toLocaleTimeString());
      
      console.log(`📊 Loaded ${apiData.data.length} top movers from ${apiData.meta.sentiment_column}`);
      
    } catch (err) {
      console.error('❌ Error fetching top movers:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch top movers data');
      
      // Fallback to mock data on error
      const mockData: TopMover[] = [
        { ticker: "INFY", name: "Infosys", change: 12.5, sentiment: 85, sector: "IT Services", country: "IN" },
        { ticker: "TCS", name: "Tata Consultancy", change: 8.3, sentiment: 78, sector: "IT Services", country: "IN" },
        { ticker: "WIPRO", name: "Wipro Limited", change: 6.7, sentiment: 72, sector: "IT Services", country: "IN" },
        { ticker: "HCLTECH", name: "HCL Technologies", change: -4.2, sentiment: 55, sector: "IT Services", country: "IN" },
        { ticker: "TECHM", name: "Tech Mahindra", change: -2.8, sentiment: 58, sector: "IT Services", country: "IN" },
      ];
      setTopMovers(mockData);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTopMovers();
    
    // Refresh every 5 minutes
    const interval = setInterval(fetchTopMovers, 5 * 60 * 1000);
    
    return () => clearInterval(interval);
  }, [sentimentPeriod]);

  return (
    <div className="bg-[#111827] rounded-xl p-6 border border-gray-800">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-[#E5E7EB] text-xl">Top Movers by Sentiment</h3>
        <div className="flex items-center gap-2">
          {/* Period Toggle */}
          <div className="flex bg-[#0B1120] rounded-lg border border-gray-800">
            <button
              onClick={() => setSentimentPeriod(7)}
              className={`px-3 py-1 text-xs rounded-l-lg transition-colors ${
                sentimentPeriod === 7
                  ? "bg-[#3B82F6] text-white"
                  : "text-[#9CA3AF] hover:text-[#E5E7EB]"
              }`}
            >
              7D
            </button>
            <button
              onClick={() => setSentimentPeriod(30)}
              className={`px-3 py-1 text-xs rounded-r-lg transition-colors ${
                sentimentPeriod === 30
                  ? "bg-[#3B82F6] text-white"
                  : "text-[#9CA3AF] hover:text-[#E5E7EB]"
              }`}
            >
              30D
            </button>
          </div>
          
          {/* Refresh Button */}
          <button
            onClick={fetchTopMovers}
            disabled={loading}
            className="text-xs text-[#9CA3AF] hover:text-[#E5E7EB] transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-3 mb-4">
          <p className="text-red-400 text-sm">⚠️ {error}</p>
          <p className="text-red-300/70 text-xs mt-1">Showing fallback data.</p>
        </div>
      )}

      {loading && topMovers.length === 0 ? (
        <div className="flex items-center justify-center h-32">
          <div className="flex items-center gap-3">
            <RefreshCw className="w-5 h-5 animate-spin text-[#3B82F6]" />
            <p className="text-[#9CA3AF]">Loading top movers...</p>
          </div>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
            {topMovers.map((stock) => {
              const isPositive = stock.change > 0;
              return (
                <div
                  key={stock.ticker}
                  className="bg-[#0B1120] rounded-lg p-4 border border-gray-800 hover:border-gray-700 transition-all cursor-pointer group"
                  title={`${stock.name} (${stock.sector}) - ${sentimentPeriod}D Sentiment: ${stock.sentiment}%`}
                >
                  <div className="flex items-start justify-between mb-2">
                    <div>
                      <p className="text-[#E5E7EB] font-medium">{stock.ticker}</p>
                      <p className="text-[#9CA3AF] text-xs truncate">{stock.name}</p>
                    </div>
                    {isPositive ? (
                      <TrendingUp className="w-5 h-5 text-[#10B981]" />
                    ) : (
                      <TrendingDown className="w-5 h-5 text-red-500" />
                    )}
                  </div>
                  <div className="flex items-center justify-between mb-2">
                    <div
                      className={`px-2 py-1 rounded text-sm font-medium ${
                        isPositive
                          ? "bg-[#10B981]/10 text-[#10B981]"
                          : "bg-red-500/10 text-red-500"
                      }`}
                    >
                      {isPositive ? "+" : ""}
                      {stock.change.toFixed(1)}%
                    </div>
                    <div className="text-[#9CA3AF] text-xs">
                      <span className="text-[#E5E7EB] font-medium">{stock.sentiment}</span>
                    </div>
                  </div>
                  <div className="mt-3 h-1 bg-gray-800 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-[#3B82F6] rounded-full transition-all group-hover:bg-[#10B981]"
                      style={{ width: `${stock.sentiment}%` }}
                    />
                  </div>
                  <div className="mt-2">
                    <p className="text-[#9CA3AF] text-xs truncate">{stock.sector}</p>
                  </div>
                </div>
              );
            })}
          </div>

          {topMovers.length === 0 && !loading && (
            <div className="text-center py-8">
              <p className="text-[#9CA3AF]">No top movers data available</p>
            </div>
          )}
        </>
      )}

      <div className="flex items-center justify-between mt-4 pt-4 border-t border-gray-800">
        <div className="text-xs text-[#9CA3AF]">
          Showing top 5 stocks by {sentimentPeriod}-day sentiment
        </div>
        <p className="text-xs text-[#9CA3AF]">
          {lastUpdated ? `Updated ${lastUpdated}` : "Loading..."}
        </p>
      </div>
    </div>
  );
}
