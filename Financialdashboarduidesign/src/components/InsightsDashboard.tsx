import { useState, useEffect } from "react";
import { FilterBar, FilterState } from "./FilterBar";
import { StockTable, Stock } from "./StockTable";
import { Download, RefreshCw } from "lucide-react";

interface InsightsDashboardProps {
  onStockSelect: (ticker: string) => void;
}

// API Response interface from your FastAPI backend
interface APIStockResponse {
  symbol: string;
  name: string;
  sector: string;
  last_price: number;
  change: number;
  change_percent: number;
  volume: number;
  market_cap: number;
  sentiment_score: number | string; // Can be number or "None"
}

const formatVolume = (volume: number): string => {
  if (volume >= 1000000) {
    return `${(volume / 1000000).toFixed(1)}M`;
  } else if (volume >= 1000) {
    return `${(volume / 1000).toFixed(1)}K`;
  }
  return volume.toString();
};

export function InsightsDashboard({ onStockSelect }: InsightsDashboardProps) {
  const [stocks, setStocks] = useState<Stock[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState<FilterState>({
    search: "",
    sector: "All Sectors",
    index: "All Indices",
    country: "All Countries",
    marketCap: "All",
    sentiment: "All",
  });

  // API configuration - update this with your backend URL
  const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

  // Function to fetch stocks from your FastAPI backend
  const fetchStocksFromAPI = async () => {
    try {
      setLoading(true);
      setError(null);
      
      console.log(`🚀 Fetching stocks from: ${API_BASE_URL}/api/stocks?sentiment_days=7`);
      
      const response = await fetch(`${API_BASE_URL}/api/stocks?sentiment_days=7`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const apiStocks: APIStockResponse[] = await response.json();
      console.log(`✅ API returned ${apiStocks.length} stocks`);

      // Transform API response to match our Stock interface
      const transformedStocks: Stock[] = apiStocks.map((apiStock, index) => ({
        name: apiStock.name || apiStock.symbol, // Use API-provided name
        ticker: apiStock.symbol,
        sector: apiStock.sector || 'Unknown', // Use API-provided sector
        index: 'NSE', // Default to NSE since we don't have this in API
        country: "India",
        price: `₹${apiStock.last_price?.toFixed(2) || '0.00'}`,
        change: Number(apiStock.change_percent) || 0, // Use change_percent instead of change
        volume: formatVolume(apiStock.volume || 0),
        marketCap: `₹${((apiStock.market_cap || 0) / 1e12).toFixed(1)}T`,
        sentiment: typeof apiStock.sentiment_score === 'number' ? apiStock.sentiment_score : 0,
        logo: '📈', // Default logo
      }));

      setStocks(transformedStocks);
      console.log(`✅ Successfully processed ${transformedStocks.length} stocks`);
      
    } catch (err) {
      console.error('❌ Error fetching stocks from API:', err);
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch stock data';
      setError(`API Error: ${errorMessage}`);
      
      // Don't fall back to mock data - keep stocks array empty
    } finally {
      setLoading(false);
    }
  };

  // Refresh handler
  const handleRefresh = () => {
    console.log('🔄 Manual refresh triggered');
    fetchStocksFromAPI();
  };

  useEffect(() => {
    fetchStocksFromAPI();
  }, []);

  // Filter stocks based on current filters
  const filteredStocks = stocks.filter((stock) => {
    if (filters.search && !stock.name.toLowerCase().includes(filters.search.toLowerCase()) && 
        !stock.ticker.toLowerCase().includes(filters.search.toLowerCase())) {
      return false;
    }
    if (filters.sector !== "All Sectors" && stock.sector !== filters.sector) {
      return false;
    }
    if (filters.index !== "All Indices" && stock.index !== filters.index) {
      return false;
    }
    if (filters.country !== "All Countries" && stock.country !== filters.country) {
      return false;
    }
    // Add other filter logic as needed
    return true;
  });

  // Show loading state
  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-center py-20">
          <div className="flex items-center gap-3 text-[#9CA3AF]">
            <RefreshCw className="w-6 h-6 animate-spin" />
            <span>Loading stock data from API...</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-[#E5E7EB] text-2xl mb-1">Stock Insights</h2>
          <p className="text-[#9CA3AF] text-sm">
            Real-time analysis with sentiment data ({stocks.length} stocks loaded)
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button 
            onClick={handleRefresh}
            className="flex items-center gap-2 px-4 py-2 bg-[#0B1120] border border-gray-800 rounded-lg text-[#9CA3AF] hover:text-[#E5E7EB] hover:border-gray-700 transition-colors"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>
          
          <button className="flex items-center gap-2 px-4 py-2 bg-[#0B1120] border border-gray-800 rounded-lg text-[#9CA3AF] hover:text-[#E5E7EB] hover:border-gray-700 transition-colors">
            <Download className="w-4 h-4" />
            <span>Export</span>
          </button>
        </div>
      </div>

      {/* Show error if exists */}
      {error && (
        <div className="bg-red-900/20 border border-red-800 rounded-lg p-4">
          <div className="text-red-300 font-medium">Connection Error</div>
          <div className="text-red-400 text-sm mt-1">{error}</div>
          <button 
            onClick={handleRefresh}
            className="mt-3 px-4 py-2 bg-red-800 hover:bg-red-700 text-white rounded-lg text-sm transition-colors"
          >
            Try Again
          </button>
        </div>
      )}

      {/* Filters */}
      <FilterBar filters={filters} onFiltersChange={setFilters} />

      {/* Stock Table */}
      <StockTable 
        stocks={filteredStocks} 
        onStockSelect={onStockSelect}
      />

      {/* Show message if no stocks available */}
      {!loading && !error && stocks.length === 0 && (
        <div className="text-center py-12 text-[#9CA3AF]">
          <p>No stock data available. Please check your API connection.</p>
        </div>
      )}
    </div>
  );
}