import { useState, useEffect } from "react";
import { Filter, Search, TrendingUp, TrendingDown, RotateCcw } from "lucide-react";

interface Stock {
  symbol: string;
  name: string;
  price: number;
  change: number;
  changePercent: number;
  marketCap: number;
  pe: number;
  volume: number;
  sector: string;
}

interface FilterCriteria {
  minPrice: string;
  maxPrice: string;
  minMarketCap: string;
  maxMarketCap: string;
  minPE: string;
  maxPE: string;
  sector: string;
  minChange: string;
  maxChange: string;
}

export function Screener() {
  const [stocks, setStocks] = useState<Stock[]>([]);
  const [filteredStocks, setFilteredStocks] = useState<Stock[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [showFilters, setShowFilters] = useState(false);
  
  const [filters, setFilters] = useState<FilterCriteria>({
    minPrice: "",
    maxPrice: "",
    minMarketCap: "",
    maxMarketCap: "",
    minPE: "",
    maxPE: "",
    sector: "",
    minChange: "",
    maxChange: ""
  });

  const sectors = [
    "All Sectors",
    "Technology",
    "Banking",
    "Healthcare",
    "Energy",
    "Consumer Goods",
    "Telecommunications",
    "Automotive",
    "Real Estate",
    "Pharmaceuticals"
  ];

  useEffect(() => {
    // Simulate loading stock data
    setTimeout(() => {
      const mockStocks: Stock[] = [
        {
          symbol: "TCS",
          name: "Tata Consultancy Services",
          price: 3245.50,
          change: 45.20,
          changePercent: 1.41,
          marketCap: 1180000,
          pe: 28.5,
          volume: 1200000,
          sector: "Technology"
        },
        {
          symbol: "RELIANCE",
          name: "Reliance Industries",
          price: 2456.75,
          change: -32.10,
          changePercent: -1.29,
          marketCap: 1650000,
          pe: 24.2,
          volume: 2100000,
          sector: "Energy"
        },
        {
          symbol: "HDFCBANK",
          name: "HDFC Bank",
          price: 1534.20,
          change: 18.50,
          changePercent: 1.22,
          marketCap: 850000,
          pe: 19.8,
          volume: 1800000,
          sector: "Banking"
        },
        {
          symbol: "INFY",
          name: "Infosys Limited",
          price: 1456.75,
          change: -12.30,
          changePercent: -0.84,
          marketCap: 610000,
          pe: 24.2,
          volume: 2100000,
          sector: "Technology"
        },
        {
          symbol: "ICICIBANK",
          name: "ICICI Bank",
          price: 1089.40,
          change: 25.60,
          changePercent: 2.41,
          marketCap: 760000,
          pe: 16.5,
          volume: 1500000,
          sector: "Banking"
        }
      ];
      
      setStocks(mockStocks);
      setFilteredStocks(mockStocks);
      setLoading(false);
    }, 1000);
  }, []);

  useEffect(() => {
    applyFilters();
  }, [stocks, filters, searchQuery]);

  const applyFilters = () => {
    let filtered = stocks.filter(stock => {
      // Search filter
      if (searchQuery && !stock.symbol.toLowerCase().includes(searchQuery.toLowerCase()) && 
          !stock.name.toLowerCase().includes(searchQuery.toLowerCase())) {
        return false;
      }

      // Price filter
      if (filters.minPrice && stock.price < parseFloat(filters.minPrice)) return false;
      if (filters.maxPrice && stock.price > parseFloat(filters.maxPrice)) return false;

      // Market Cap filter (in crores)
      if (filters.minMarketCap && stock.marketCap < parseFloat(filters.minMarketCap)) return false;
      if (filters.maxMarketCap && stock.marketCap > parseFloat(filters.maxMarketCap)) return false;

      // P/E filter
      if (filters.minPE && stock.pe < parseFloat(filters.minPE)) return false;
      if (filters.maxPE && stock.pe > parseFloat(filters.maxPE)) return false;

      // Sector filter
      if (filters.sector && filters.sector !== "All Sectors" && stock.sector !== filters.sector) return false;

      // Change filter
      if (filters.minChange && stock.changePercent < parseFloat(filters.minChange)) return false;
      if (filters.maxChange && stock.changePercent > parseFloat(filters.maxChange)) return false;

      return true;
    });

    setFilteredStocks(filtered);
  };

  const resetFilters = () => {
    setFilters({
      minPrice: "",
      maxPrice: "",
      minMarketCap: "",
      maxMarketCap: "",
      minPE: "",
      maxPE: "",
      sector: "",
      minChange: "",
      maxChange: ""
    });
    setSearchQuery("");
  };

  const formatMarketCap = (value: number) => {
    if (value >= 100000) {
      return `₹${(value / 100000).toFixed(1)}L Cr`;
    } else {
      return `₹${(value / 1000).toFixed(0)}K Cr`;
    }
  };

  if (loading) {
    return (
      <div className="p-6 max-w-[1800px] mx-auto h-full overflow-y-auto">
        <div className="mb-6">
          <h1 className="text-white text-2xl font-bold mb-2">Stock Screener</h1>
          <p className="text-gray-400">Filter and discover stocks based on your criteria</p>
        </div>
        
        <div className="space-y-4">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="bg-[#1E293B] rounded-lg p-4 animate-pulse">
              <div className="grid grid-cols-6 gap-4">
                <div className="h-4 bg-gray-700 rounded"></div>
                <div className="h-4 bg-gray-700 rounded"></div>
                <div className="h-4 bg-gray-700 rounded"></div>
                <div className="h-4 bg-gray-700 rounded"></div>
                <div className="h-4 bg-gray-700 rounded"></div>
                <div className="h-4 bg-gray-700 rounded"></div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-[1800px] mx-auto h-full overflow-y-auto">
      <div className="mb-6">
        <h1 className="text-white text-2xl font-bold mb-2">Stock Screener</h1>
        <p className="text-gray-400">Filter and discover stocks based on your criteria</p>
      </div>

      {/* Search and Filter Controls */}
      <div className="mb-6 space-y-4">
        <div className="flex gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search stocks..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-[#1E293B] border border-gray-700 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-blue-500"
            />
          </div>
          
          <button
            onClick={() => setShowFilters(!showFilters)}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
          >
            <Filter className="w-4 h-4" />
            Filters
          </button>
          
          <button
            onClick={resetFilters}
            className="flex items-center gap-2 px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg transition-colors"
          >
            <RotateCcw className="w-4 h-4" />
            Reset
          </button>
        </div>

        {/* Filter Panel */}
        {showFilters && (
          <div className="bg-[#1E293B] rounded-lg p-6 border border-gray-700/50">
            <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-4">
              <div>
                <label className="block text-sm text-gray-400 mb-2">Min Price (₹)</label>
                <input
                  type="number"
                  value={filters.minPrice}
                  onChange={(e) => setFilters({...filters, minPrice: e.target.value})}
                  className="w-full px-3 py-2 bg-[#0F172A] border border-gray-700 rounded text-white focus:outline-none focus:border-blue-500"
                />
              </div>
              
              <div>
                <label className="block text-sm text-gray-400 mb-2">Max Price (₹)</label>
                <input
                  type="number"
                  value={filters.maxPrice}
                  onChange={(e) => setFilters({...filters, maxPrice: e.target.value})}
                  className="w-full px-3 py-2 bg-[#0F172A] border border-gray-700 rounded text-white focus:outline-none focus:border-blue-500"
                />
              </div>
              
              <div>
                <label className="block text-sm text-gray-400 mb-2">Min Market Cap (Cr)</label>
                <input
                  type="number"
                  value={filters.minMarketCap}
                  onChange={(e) => setFilters({...filters, minMarketCap: e.target.value})}
                  className="w-full px-3 py-2 bg-[#0F172A] border border-gray-700 rounded text-white focus:outline-none focus:border-blue-500"
                />
              </div>
              
              <div>
                <label className="block text-sm text-gray-400 mb-2">Sector</label>
                <select
                  value={filters.sector}
                  onChange={(e) => setFilters({...filters, sector: e.target.value})}
                  className="w-full px-3 py-2 bg-[#0F172A] border border-gray-700 rounded text-white focus:outline-none focus:border-blue-500"
                >
                  {sectors.map(sector => (
                    <option key={sector} value={sector === "All Sectors" ? "" : sector}>
                      {sector}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Results */}
      <div className="bg-[#1E293B] rounded-lg border border-gray-700/50 overflow-hidden">
        <div className="p-4 border-b border-gray-700">
          <div className="text-white font-semibold">
            {filteredStocks.length} stocks found
          </div>
        </div>
        
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-700 bg-[#0F172A]">
                <th className="text-left p-4 text-gray-400 font-medium">Symbol</th>
                <th className="text-left p-4 text-gray-400 font-medium">Company</th>
                <th className="text-right p-4 text-gray-400 font-medium">Price</th>
                <th className="text-right p-4 text-gray-400 font-medium">Change</th>
                <th className="text-right p-4 text-gray-400 font-medium">Market Cap</th>
                <th className="text-right p-4 text-gray-400 font-medium">P/E</th>
                <th className="text-left p-4 text-gray-400 font-medium">Sector</th>
              </tr>
            </thead>
            <tbody>
              {filteredStocks.map((stock, index) => (
                <tr key={stock.symbol} className={index % 2 === 0 ? "bg-[#0F172A]/50" : ""}>
                  <td className="p-4">
                    <div className="text-white font-semibold">{stock.symbol}</div>
                  </td>
                  <td className="p-4">
                    <div className="text-white">{stock.name}</div>
                  </td>
                  <td className="p-4 text-right">
                    <div className="text-white font-medium">₹{stock.price.toFixed(2)}</div>
                  </td>
                  <td className="p-4 text-right">
                    <div className={`flex items-center justify-end gap-1 ${
                      stock.changePercent >= 0 ? 'text-green-400' : 'text-red-400'
                    }`}>
                      {stock.changePercent >= 0 ? 
                        <TrendingUp className="w-4 h-4" /> : 
                        <TrendingDown className="w-4 h-4" />
                      }
                      {stock.changePercent.toFixed(2)}%
                    </div>
                  </td>
                  <td className="p-4 text-right">
                    <div className="text-white">{formatMarketCap(stock.marketCap)}</div>
                  </td>
                  <td className="p-4 text-right">
                    <div className="text-white">{stock.pe.toFixed(1)}</div>
                  </td>
                  <td className="p-4">
                    <span className="bg-blue-500/20 text-blue-400 px-2 py-1 rounded text-sm">
                      {stock.sector}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {filteredStocks.length === 0 && (
        <div className="text-center py-12">
          <div className="text-gray-400 mb-2">No stocks match your criteria</div>
          <div className="text-sm text-gray-500">Try adjusting your filters</div>
        </div>
      )}
    </div>
  );
}