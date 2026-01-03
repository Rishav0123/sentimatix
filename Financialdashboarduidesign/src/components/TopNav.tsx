import { Search, User, Sparkles, Bell, Share2, ChevronDown } from "lucide-react";
import { useState, useEffect, useRef } from "react";

interface TopNavProps {
  onAskStockify: () => void;
  selectedMarket: string;
  onMarketChange: (market: string) => void;
  showMarketSelector?: boolean;
}

export function TopNav({ onAskStockify, selectedMarket, onMarketChange, showMarketSelector = true }: TopNavProps) {
  const [showMarketDropdown, setShowMarketDropdown] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const markets = [
    { id: "india", name: "India Markets", flag: "🇮🇳", color: "#10B981" },
    { id: "usa", name: "USA Markets", flag: "🇺🇸", color: "#3B82F6" },
  ];

  const currentMarket = markets.find(m => m.name === selectedMarket) || markets[0];

  const handleMarketSelect = (market: typeof markets[0]) => {
    onMarketChange(market.name);
    setShowMarketDropdown(false);
  };

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setShowMarketDropdown(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  return (
    <div className="bg-[#111827] border-b border-gray-800">
      <div className="px-6 py-4 flex items-center justify-between gap-6">
        {/* Logo */}
        <div className="flex items-center gap-2">
          <span className="text-2xl">📈</span>
          <div>
            <h1 className="text-[#E5E7EB] text-xl">Stockify</h1>
          </div>
        </div>

        {/* Search Bar */}
        <div className="flex-1 max-w-2xl relative">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-[#9CA3AF]" />
          <input
            type="text"
            placeholder="Search for companies, tickers, or crypto"
            className="w-full bg-[#0B1120] border border-gray-800 rounded-lg pl-12 pr-4 py-2.5 text-[#E5E7EB] placeholder:text-[#9CA3AF] focus:outline-none focus:border-[#3B82F6] transition-colors text-sm"
          />
        </div>

        {/* Right Actions */}
        <div className="flex items-center gap-3">
          <button className="flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-[#0B1120] transition-colors text-[#9CA3AF] hover:text-[#E5E7EB] cursor-pointer">
            <Bell className="w-4 h-4" />
            <span className="text-sm">Price Alert</span>
          </button>
          <button className="flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-[#0B1120] transition-colors text-[#9CA3AF] hover:text-[#E5E7EB] cursor-pointer">
            <Share2 className="w-4 h-4" />
            <span className="text-sm">Share</span>
          </button>
          <button
            onClick={onAskStockify}
            className="flex items-center gap-2 bg-[#3B82F6] hover:bg-[#3B82F6]/90 text-white px-4 py-2 rounded-lg transition-colors cursor-pointer"
          >
            <Sparkles className="w-4 h-4" />
            Ask Stockify
          </button>
        </div>
      </div>

      {/* Market Selector & Status Bar */}
      {showMarketSelector && (
        <div className="px-6 py-3 flex items-center justify-between border-t border-gray-800">
          <div className="flex items-center gap-4">
            {/* Market Dropdown */}
            <div className="relative" ref={dropdownRef}>
              <button
                onClick={() => setShowMarketDropdown(!showMarketDropdown)}
                className="flex items-center gap-2 px-3 py-1.5 border rounded-lg transition-colors cursor-pointer"
                style={{ 
                  backgroundColor: `${currentMarket.color}10`, 
                  borderColor: `${currentMarket.color}33`,
                  color: currentMarket.color 
                }}
              >
                <span className="text-sm">{currentMarket.flag}</span>
                <span className="text-sm">{currentMarket.name}</span>
                <ChevronDown className={`w-3 h-3 transition-transform ${showMarketDropdown ? 'rotate-180' : ''}`} />
              </button>

              {/* Dropdown Menu */}
              {showMarketDropdown && (
                <div className="absolute top-full left-0 mt-1 bg-[#111827] border border-gray-800 rounded-lg shadow-lg z-50 min-w-[160px]">
                  {markets.map((market) => (
                    <button
                      key={market.id}
                      onClick={() => handleMarketSelect(market)}
                      className={`w-full flex items-center gap-2 px-3 py-2 text-left hover:bg-[#0B1120] transition-colors text-sm ${
                        market.name === selectedMarket ? 'bg-[#0B1120]' : ''
                      }`}
                      style={{ color: market.name === selectedMarket ? market.color : '#9CA3AF' }}
                    >
                      <span>{market.flag}</span>
                      <span>{market.name}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Quick Access Tabs - Only Crypto now */}
            <div className="flex items-center gap-2">
              <button className="px-3 py-1.5 rounded-lg text-[#9CA3AF] hover:text-[#E5E7EB] hover:bg-[#0B1120] transition-colors text-sm cursor-pointer">
                Crypto
              </button>
            </div>
          </div>

          {/* Market Status */}
          <div className="flex items-center gap-4 text-sm">
            <span className="text-[#9CA3AF]">
              {currentMarket.id === 'india' ? '1 Nov 2025, IST • Market Closed' : '1 Nov 2025, EST • Market Closed'}
            </span>
            <div className="flex items-center gap-1.5">
              <div className="flex items-center gap-1">
                <div className="w-1 h-1 bg-gray-500 rounded-full"></div>
                <div className="w-1 h-1 bg-gray-500 rounded-full"></div>
                <div className="w-1 h-1 bg-gray-500 rounded-full"></div>
              </div>
              <span className="text-[#9CA3AF]">Neutral Sentiment</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
