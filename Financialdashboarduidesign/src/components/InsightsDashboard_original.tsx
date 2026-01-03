import { useState, useEffect } from "react";
import { FilterBar, FilterState } from "./FilterBar";
import { StockTable, Stock } from "./StockTable";
import { Download, RefreshCw } from "lucide-react";

interface InsightsDashboardProps {
  onStockSelect: (ticker: string) => void;
}

// API Response interface from your backend
interface APIStockResponse {
  symbol: string;
  name: string;
  last_price: number;
  change: number;
  change_percent: number;
  volume: number;
  sentiment_score: number | string; // Can be number or "None"
}

// Helper functions to map symbols to display data
const getStockName = (symbol: string): string => {
  const nameMap: Record<string, string> = {
    'INFY': 'Infosys Limited',
    'TCS': 'Tata Consultancy Services',
    'DRREDDY': "Dr. Reddy's Laboratories",
    'SUNPHARMA': 'Sun Pharmaceutical',
    'HCLTECH': 'HCL Technologies',
    'RELIANCE': 'Reliance Industries',
    'HDFCBANK': 'HDFC Bank',
    'WIPRO': 'Wipro Limited',
    'ICICIBANK': 'ICICI Bank',
    'M&M': 'Mahindra & Mahindra',
    'ASIANPAINT': 'Asian Paints',
    'BHARTIARTL': 'Bharti Airtel',
  };
  return nameMap[symbol] || symbol;
};

const getStockSector = (symbol: string): string => {
  const sectorMap: Record<string, string> = {
    'INFY': 'Technology',
    'TCS': 'Technology',
    'DRREDDY': 'Healthcare',
    'SUNPHARMA': 'Healthcare',
    'HCLTECH': 'Technology',
    'RELIANCE': 'Energy',
    'HDFCBANK': 'Finance',
    'WIPRO': 'Technology',
    'ICICIBANK': 'Finance',
    'M&M': 'Industrial',
    'ASIANPAINT': 'Consumer',
    'BHARTIARTL': 'Telecom',
  };
  return sectorMap[symbol] || 'Unknown';
};

const getStockIndex = (symbol: string): string => {
  const indexMap: Record<string, string> = {
    'INFY': 'NIFTY 50',
    'TCS': 'NIFTY 50',
    'DRREDDY': 'NIFTY Pharma',
    'SUNPHARMA': 'NIFTY Pharma',
    'HCLTECH': 'NIFTY IT',
    'RELIANCE': 'NIFTY 50',
    'HDFCBANK': 'NIFTY 50',
    'WIPRO': 'NIFTY 100',
    'ICICIBANK': 'NIFTY 50',
    'M&M': 'NIFTY 50',
    'ASIANPAINT': 'NIFTY 50',
    'BHARTIARTL': 'NIFTY 50',
  };
  return indexMap[symbol] || 'NSE';
};

const getMarketCap = (symbol: string): string => {
  const marketCapMap: Record<string, string> = {
    'INFY': '₹6.2T',
    'TCS': '₹14.1T',
    'DRREDDY': '₹945B',
    'SUNPHARMA': '₹4.0T',
    'HCLTECH': '₹4.8T',
    'RELIANCE': '₹16.6T',
    'HDFCBANK': '₹12.5T',
    'WIPRO': '₹2.3T',
    'ICICIBANK': '₹7.9T',
    'M&M': '₹3.5T',
    'ASIANPAINT': '₹2.8T',
    'BHARTIARTL': '₹8.5T',
  };
  return marketCapMap[symbol] || '₹0';
};

const getStockLogo = (symbol: string): string => {
  const logoMap: Record<string, string> = {
    'INFY': '🏢',
    'TCS': '💼',
    'DRREDDY': '💊',
    'SUNPHARMA': '☀️',
    'HCLTECH': '🖥️',
    'RELIANCE': '⚡',
    'HDFCBANK': '🏦',
    'WIPRO': '💻',
    'ICICIBANK': '🏛️',
    'M&M': '🚗',
    'ASIANPAINT': '🎨',
    'BHARTIARTL': '📱',
  };
  return logoMap[symbol] || '📈';
};

const formatVolume = (volume: number): string => {
  if (volume >= 1000000) {
    return `${(volume / 1000000).toFixed(1)}M`;
  } else if (volume >= 1000) {
    return `${(volume / 1000).toFixed(1)}K`;
  }
  return volume.toString();
};

const mockStocks: Stock[] = [
  {
    name: "Infosys Limited",
    ticker: "INFY",
    sector: "Technology",
    index: "NIFTY 50",
    country: "India",
    price: "₹1,482.30",
    change: 3.45,
    volume: "8.2M",
    marketCap: "₹6.2T",
    sentiment: 78,
    logo: "🏢",
  },
  {
    name: "Tata Consultancy Services",
    ticker: "TCS",
    sector: "Technology",
    index: "NIFTY 50",
    country: "India",
    price: "₹3,850.60",
    change: 2.15,
    volume: "2.4M",
    marketCap: "₹14.1T",
    sentiment: 82,
    logo: "💼",
  },
  {
    name: "HDFC Bank",
    ticker: "HDFCBANK",
    sector: "Finance",
    index: "NIFTY 50",
    country: "India",
    price: "₹1,645.20",
    change: -1.23,
    volume: "12.5M",
    marketCap: "₹12.5T",
    sentiment: 65,
    logo: "🏦",
  },
  {
    name: "Reliance Industries",
    ticker: "RELIANCE",
    sector: "Energy",
    index: "NIFTY 50",
    country: "India",
    price: "₹2,456.75",
    change: 1.87,
    volume: "9.8M",
    marketCap: "₹16.6T",
    sentiment: 72,
    logo: "⚡",
  },
  {
    name: "Wipro Limited",
    ticker: "WIPRO",
    sector: "Technology",
    index: "NIFTY 100",
    country: "India",
    price: "₹425.80",
    change: -0.56,
    volume: "5.3M",
    marketCap: "₹2.3T",
    sentiment: 58,
    logo: "💻",
  },
  {
    name: "ICICI Bank",
    ticker: "ICICIBANK",
    sector: "Finance",
    index: "NIFTY 50",
    country: "India",
    price: "₹1,125.40",
    change: 2.34,
    volume: "14.2M",
    marketCap: "₹7.9T",
    sentiment: 70,
    logo: "🏛️",
  },
  {
    name: "Dr. Reddy's Laboratories",
    ticker: "DRREDDY",
    sector: "Healthcare",
    index: "NIFTY Pharma",
    country: "India",
    price: "₹5,680.90",
    change: 4.21,
    volume: "1.2M",
    marketCap: "₹945B",
    sentiment: 85,
    logo: "💊",
  },
  {
    name: "Mahindra & Mahindra",
    ticker: "M&M",
    sector: "Industrial",
    index: "NIFTY 50",
    country: "India",
    price: "₹2,845.60",
    change: -2.15,
    volume: "3.8M",
    marketCap: "₹3.5T",
    sentiment: 62,
    logo: "🚗",
  },
  {
    name: "HCL Technologies",
    ticker: "HCLTECH",
    sector: "Technology",
    index: "NIFTY IT",
    country: "India",
    price: "₹1,756.30",
    change: 1.92,
    volume: "4.6M",
    marketCap: "₹4.8T",
    sentiment: 75,
    logo: "🖥️",
  },
  {
    name: "Asian Paints",
    ticker: "ASIANPAINT",
    sector: "Consumer",
    index: "NIFTY 50",
    country: "India",
    price: "₹2,924.50",
    change: -0.78,
    volume: "1.9M",
    marketCap: "₹2.8T",
    sentiment: 55,
    logo: "🎨",
  },
  {
    name: "Bharti Airtel",
    ticker: "BHARTIARTL",
    sector: "Telecom",
    index: "NIFTY 50",
    country: "India",
    price: "₹1,456.80",
    change: 3.12,
    volume: "7.4M",
    marketCap: "₹8.5T",
    sentiment: 68,
    logo: "📱",
  },
  {
    name: "Sun Pharmaceutical",
    ticker: "SUNPHARMA",
    sector: "Healthcare",
    index: "NIFTY Pharma",
    country: "India",
    price: "₹1,678.40",
    change: 2.89,
    volume: "3.2M",
    marketCap: "₹4.0T",
    sentiment: 80,
    logo: "☀️",
  },
];

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
  const API_BASE_URL = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/+$/, '').replace(/\/api$/, '');

  // Function to fetch stocks from your FastAPI backend
  const fetchStocksFromAPI = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await fetch(`${API_BASE_URL}/api/stocks`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const apiStocks: APIStockResponse[] = await response.json();
      
      // Transform API response to match your Stock interface
      const transformedStocks: Stock[] = apiStocks.map((apiStock) => ({
        name: getStockName(apiStock.symbol), // Map symbol to company name
        ticker: apiStock.symbol,
        sector: getStockSector(apiStock.symbol), // Map symbol to sector
        index: getStockIndex(apiStock.symbol), // Map symbol to index
        country: "India", // Default to India for NSE stocks
        price: `₹${apiStock.last_price.toLocaleString('en-IN', { minimumFractionDigits: 2 })}`,
        change: apiStock.change_percent,
        volume: formatVolume(apiStock.volume),
        marketCap: getMarketCap(apiStock.symbol), // You might want to add this to your API
        sentiment: typeof apiStock.sentiment_score === 'number' ? apiStock.sentiment_score : 50,
        logo: getStockLogo(apiStock.symbol), // Map symbol to emoji
      }));

      setStocks(transformedStocks);
      console.log(`Successfully fetched ${transformedStocks.length} stocks from API`);
    } catch (err) {
      console.error('Error fetching stocks from API:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch stock data');
      
      // Fallback to mock data if API fails
      setStocks(mockStocks);
    } finally {
      setLoading(false);
    }
  };

  // Fetch data on component mount
  useEffect(() => {
    fetchStocksFromAPI();
  }, []);

  // Helper function to refresh data
  const handleRefresh = () => {
    fetchStocksFromAPI();
  };
    if (filters.search && !stock.name.toLowerCase().includes(filters.search.toLowerCase()) && !stock.ticker.toLowerCase().includes(filters.search.toLowerCase())) {
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
    if (filters.sentiment !== "All") {
      if (filters.sentiment === "Positive" && stock.sentiment < 70) return false;
      if (filters.sentiment === "Neutral" && (stock.sentiment < 50 || stock.sentiment >= 70)) return false;
      if (filters.sentiment === "Negative" && stock.sentiment >= 50) return false;
    }
    return true;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-[#E5E7EB] text-2xl mb-1">Stock Insights</h2>
          <p className="text-[#9CA3AF] text-sm">
            Analyze and filter stocks based on sentiment, sector, and performance metrics
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button className="flex items-center gap-2 px-4 py-2 bg-[#0B1120] border border-gray-800 rounded-lg text-[#9CA3AF] hover:text-[#E5E7EB] hover:border-gray-700 transition-colors">
            <RefreshCw className="w-4 h-4" />
            Refresh
          </button>
          <button className="flex items-center gap-2 px-4 py-2 bg-[#3B82F6] hover:bg-[#3B82F6]/90 text-white rounded-lg transition-colors">
            <Download className="w-4 h-4" />
            Export
          </button>
        </div>
      </div>

      {/* Filter Bar */}
      <FilterBar onFilterChange={setFilters} />

      {/* Results Summary */}
      <div className="flex items-center justify-between">
        <p className="text-[#9CA3AF] text-sm">
          Showing <span className="text-[#E5E7EB]">{filteredStocks.length}</span> of{" "}
          <span className="text-[#E5E7EB]">{mockStocks.length}</span> stocks
        </p>
        <div className="flex items-center gap-2">
          <span className="text-[#9CA3AF] text-xs">Average Sentiment:</span>
          <span className="text-[#10B981]">
            {filteredStocks.length > 0
              ? Math.round(
                  filteredStocks.reduce((acc, stock) => acc + stock.sentiment, 0) /
                    filteredStocks.length
                )
              : 0}
          </span>
        </div>
      </div>

      {/* Stock Table */}
      <StockTable stocks={filteredStocks} onStockClick={onStockSelect} />
    </div>
  );
}
