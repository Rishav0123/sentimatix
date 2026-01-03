import { useState } from "react";
import { Search, Plus, X, TrendingUp, TrendingDown } from "lucide-react";

interface Stock {
  symbol: string;
  name: string;
  price: number;
  change: number;
  changePercent: number;
  marketCap: string;
  pe: number;
  volume: string;
}

export function Compare() {
  const [selectedStocks, setSelectedStocks] = useState<Stock[]>([
    {
      symbol: "TCS",
      name: "Tata Consultancy Services",
      price: 3245.50,
      change: 45.20,
      changePercent: 1.41,
      marketCap: "₹11.8L Cr",
      pe: 28.5,
      volume: "1.2M"
    },
    {
      symbol: "INFY",
      name: "Infosys Limited",
      price: 1456.75,
      change: -12.30,
      changePercent: -0.84,
      marketCap: "₹6.1L Cr",
      pe: 24.2,
      volume: "2.1M"
    }
  ]);

  const [searchQuery, setSearchQuery] = useState("");
  const [showSearch, setShowSearch] = useState(false);

  const availableStocks = [
    { symbol: "RELIANCE", name: "Reliance Industries" },
    { symbol: "HDFCBANK", name: "HDFC Bank" },
    { symbol: "ICICIBANK", name: "ICICI Bank" },
    { symbol: "BHARTIARTL", name: "Bharti Airtel" },
    { symbol: "SBIN", name: "State Bank of India" },
    { symbol: "LICI", name: "Life Insurance Corporation" },
    { symbol: "ITC", name: "ITC Limited" },
    { symbol: "HINDUNILVR", name: "Hindustan Unilever" },
    { symbol: "LT", name: "Larsen & Toubro" },
    { symbol: "AXISBANK", name: "Axis Bank" }
  ];

  const filteredStocks = availableStocks.filter(stock =>
    stock.symbol.toLowerCase().includes(searchQuery.toLowerCase()) ||
    stock.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const addStock = (symbol: string, name: string) => {
    if (selectedStocks.length >= 4) return; // Limit to 4 stocks
    
    // Mock data for new stock
    const newStock: Stock = {
      symbol,
      name,
      price: Math.random() * 3000 + 500,
      change: (Math.random() - 0.5) * 100,
      changePercent: (Math.random() - 0.5) * 5,
      marketCap: `₹${(Math.random() * 10 + 1).toFixed(1)}L Cr`,
      pe: Math.random() * 30 + 10,
      volume: `${(Math.random() * 5 + 0.5).toFixed(1)}M`
    };
    
    setSelectedStocks([...selectedStocks, newStock]);
    setShowSearch(false);
    setSearchQuery("");
  };

  const removeStock = (symbol: string) => {
    setSelectedStocks(selectedStocks.filter(stock => stock.symbol !== symbol));
  };

  const metrics = [
    { label: "Current Price", key: "price" as keyof Stock, format: (val: number | string) => typeof val === 'number' ? `₹${val.toFixed(2)}` : val },
    { label: "Change", key: "change" as keyof Stock, format: (val: number | string) => typeof val === 'number' ? `₹${val.toFixed(2)}` : val },
    { label: "Change %", key: "changePercent" as keyof Stock, format: (val: number | string) => typeof val === 'number' ? `${val.toFixed(2)}%` : val },
    { label: "Market Cap", key: "marketCap" as keyof Stock, format: (val: number | string) => val.toString() },
    { label: "P/E Ratio", key: "pe" as keyof Stock, format: (val: number | string) => typeof val === 'number' ? val.toFixed(1) : val },
    { label: "Volume", key: "volume" as keyof Stock, format: (val: number | string) => val.toString() }
  ];

  return (
    <div className="p-6 max-w-[1800px] mx-auto h-full overflow-y-auto">
      <div className="mb-6">
        <h1 className="text-white text-2xl font-bold mb-2">Compare Stocks</h1>
        <p className="text-gray-400">Compare key metrics across multiple stocks</p>
      </div>

      {/* Add Stock Section */}
      <div className="mb-6">
        {!showSearch ? (
          <button
            onClick={() => setShowSearch(true)}
            className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors"
            disabled={selectedStocks.length >= 4}
          >
            <Plus className="w-4 h-4" />
            Add Stock to Compare {selectedStocks.length >= 4 && "(Max 4)"}
          </button>
        ) : (
          <div className="bg-[#1E293B] rounded-lg p-4 border border-gray-700/50">
            <div className="flex items-center gap-2 mb-4">
              <Search className="w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search stocks..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="flex-1 bg-transparent text-white placeholder-gray-400 outline-none"
                autoFocus
              />
              <button
                onClick={() => {
                  setShowSearch(false);
                  setSearchQuery("");
                }}
                className="text-gray-400 hover:text-white"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
            
            <div className="space-y-2 max-h-48 overflow-y-auto">
              {filteredStocks.map((stock) => (
                <button
                  key={stock.symbol}
                  onClick={() => addStock(stock.symbol, stock.name)}
                  className="w-full text-left p-2 hover:bg-[#0F172A] rounded transition-colors"
                  disabled={selectedStocks.some(s => s.symbol === stock.symbol)}
                >
                  <div className="text-white font-medium">{stock.symbol}</div>
                  <div className="text-white text-sm">{stock.name}</div>
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Comparison Table */}
      {selectedStocks.length > 0 && (
        <div className="bg-[#1E293B] rounded-lg border border-gray-700/50 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-700">
                  <th className="text-left p-4 text-gray-400 font-medium">Metric</th>
                  {selectedStocks.map((stock) => (
                    <th key={stock.symbol} className="text-left p-4 min-w-[200px]">
                      <div className="flex items-center justify-between">
                        <div>
                          <div className="text-white font-semibold">{stock.symbol}</div>
                          <div className="text-gray-400 text-sm truncate">{stock.name}</div>
                        </div>
                        <button
                          onClick={() => removeStock(stock.symbol)}
                          className="text-gray-400 hover:text-red-400 transition-colors"
                        >
                          <X className="w-4 h-4" />
                        </button>
                      </div>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {metrics.map((metric, index) => (
                  <tr key={metric.key} className={index % 2 === 0 ? "bg-[#0F172A]/50" : ""}>
                    <td className="p-4 text-white font-medium">{metric.label}</td>
                    {selectedStocks.map((stock) => {
                      const value = stock[metric.key as keyof Stock];
                      const isChange = metric.key === 'change' || metric.key === 'changePercent';
                      const isPositive = typeof value === 'number' ? value >= 0 : false;
                      
                      return (
                        <td key={stock.symbol} className="p-4">
                          <div className={`flex items-center gap-1 ${
                            isChange 
                              ? isPositive 
                                ? 'text-green-400' 
                                : 'text-red-400'
                              : 'text-white'
                          }`}>
                            {isChange && (
                              isPositive 
                                ? <TrendingUp className="w-4 h-4" />
                                : <TrendingDown className="w-4 h-4" />
                            )}
                            {typeof value === 'number' ? metric.format(value) : metric.format(value)}
                          </div>
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {selectedStocks.length === 0 && (
        <div className="text-center py-12">
          <div className="text-gray-400 mb-2">No stocks selected for comparison</div>
          <div className="text-sm text-gray-500">Add stocks to start comparing their metrics</div>
        </div>
      )}
    </div>
  );
}