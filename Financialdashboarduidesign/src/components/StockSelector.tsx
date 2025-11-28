import { Search, X } from "lucide-react";
import { useState } from "react";

interface Stock {
  ticker: string;
  name: string;
  logo: string;
}

interface StockSelectorProps {
  selectedStocks: string[];
  onStockAdd: (ticker: string) => void;
  onStockRemove: (ticker: string) => void;
  maxStocks?: number;
}

const availableStocks: Stock[] = [
  { ticker: "INFY", name: "Infosys Limited", logo: "🏢" },
  { ticker: "TCS", name: "Tata Consultancy Services", logo: "💼" },
  { ticker: "HDFCBANK", name: "HDFC Bank", logo: "🏦" },
  { ticker: "RELIANCE", name: "Reliance Industries", logo: "⚡" },
  { ticker: "WIPRO", name: "Wipro Limited", logo: "💻" },
  { ticker: "ICICIBANK", name: "ICICI Bank", logo: "🏛️" },
  { ticker: "DRREDDY", name: "Dr. Reddy's Laboratories", logo: "💊" },
  { ticker: "M&M", name: "Mahindra & Mahindra", logo: "🚗" },
  { ticker: "HCLTECH", name: "HCL Technologies", logo: "🖥️" },
  { ticker: "ASIANPAINT", name: "Asian Paints", logo: "🎨" },
];

export function StockSelector({
  selectedStocks,
  onStockAdd,
  onStockRemove,
  maxStocks = 4,
}: StockSelectorProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [showDropdown, setShowDropdown] = useState(false);

  const filteredStocks = availableStocks.filter(
    (stock) =>
      !selectedStocks.includes(stock.ticker) &&
      (stock.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        stock.ticker.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  const handleAddStock = (ticker: string) => {
    if (selectedStocks.length < maxStocks) {
      onStockAdd(ticker);
      setSearchQuery("");
      setShowDropdown(false);
    }
  };

  return (
    <div className="bg-[#111827] rounded-xl p-6 border border-gray-800">
      <h3 className="text-[#E5E7EB] mb-4">Select Stocks to Compare</h3>

      {/* Selected Stocks */}
      <div className="flex flex-wrap gap-2 mb-4">
        {selectedStocks.map((ticker) => {
          const stock = availableStocks.find((s) => s.ticker === ticker);
          return (
            <div
              key={ticker}
              className="flex items-center gap-2 bg-[#3B82F6]/10 border border-[#3B82F6]/20 rounded-lg px-3 py-2"
            >
              <span className="text-lg">{stock?.logo}</span>
              <span className="text-[#E5E7EB] text-sm">{ticker}</span>
              <button
                onClick={() => onStockRemove(ticker)}
                className="text-[#9CA3AF] hover:text-red-500 transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          );
        })}
        {selectedStocks.length === 0 && (
          <p className="text-[#9CA3AF] text-sm">No stocks selected</p>
        )}
      </div>

      {/* Search Input */}
      {selectedStocks.length < maxStocks && (
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#9CA3AF]" />
          <input
            type="text"
            placeholder={`Add stock (${selectedStocks.length}/${maxStocks})...`}
            value={searchQuery}
            onChange={(e) => {
              setSearchQuery(e.target.value);
              setShowDropdown(true);
            }}
            onFocus={() => setShowDropdown(true)}
            className="w-full bg-[#0B1120] border border-gray-800 rounded-lg pl-10 pr-4 py-2.5 text-[#E5E7EB] placeholder:text-[#9CA3AF] focus:outline-none focus:border-[#3B82F6] transition-colors text-sm"
          />

          {/* Dropdown */}
          {showDropdown && searchQuery && filteredStocks.length > 0 && (
            <div className="absolute top-full left-0 right-0 mt-2 bg-[#111827] border border-gray-800 rounded-lg shadow-lg z-10 max-h-60 overflow-y-auto">
              {filteredStocks.map((stock) => (
                <button
                  key={stock.ticker}
                  onClick={() => handleAddStock(stock.ticker)}
                  className="w-full flex items-center gap-3 px-4 py-3 hover:bg-[#0B1120] transition-colors text-left"
                >
                  <span className="text-lg">{stock.logo}</span>
                  <div className="flex-1">
                    <p className="text-[#E5E7EB] text-sm">{stock.ticker}</p>
                    <p className="text-[#9CA3AF] text-xs">{stock.name}</p>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
