import { Search, User, Sparkles, Bell, Share2, ChevronDown } from "lucide-react";

interface TopNavProps {
  onAskStockify: () => void;
  selectedMarket: string;
  onMarketChange: (market: string) => void;
  showMarketSelector?: boolean;
}

export function TopNav({ onAskStockify, selectedMarket, onMarketChange, showMarketSelector = true }: TopNavProps) {
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
          <button className="flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-[#0B1120] transition-colors text-[#9CA3AF] hover:text-[#E5E7EB]">
            <Bell className="w-4 h-4" />
            <span className="text-sm">Price Alert</span>
          </button>
          <button className="flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-[#0B1120] transition-colors text-[#9CA3AF] hover:text-[#E5E7EB]">
            <Share2 className="w-4 h-4" />
            <span className="text-sm">Share</span>
          </button>
          <button
            onClick={onAskStockify}
            className="flex items-center gap-2 bg-[#3B82F6] hover:bg-[#3B82F6]/90 text-white px-4 py-2 rounded-lg transition-colors"
          >
            <Sparkles className="w-4 h-4" />
            Ask Stockify
          </button>
          <button className="w-10 h-10 bg-[#0B1120] border border-gray-800 rounded-lg flex items-center justify-center hover:border-gray-700 transition-colors">
            <User className="w-5 h-5 text-[#9CA3AF]" />
          </button>
        </div>
      </div>

      {/* Market Selector & Status Bar */}
      {showMarketSelector && (
        <div className="px-6 py-3 flex items-center justify-between border-t border-gray-800">
          <div className="flex items-center gap-4">
            {/* Market Dropdown */}
            <button
              onClick={() => onMarketChange("India Markets")}
              className="flex items-center gap-2 px-3 py-1.5 bg-[#10B981]/10 border border-[#10B981]/20 rounded-lg text-[#10B981] hover:bg-[#10B981]/20 transition-colors"
            >
              <span className="text-sm">🇮🇳</span>
              <span className="text-sm">India Markets</span>
              <ChevronDown className="w-3 h-3" />
            </button>

            {/* Quick Access Tabs */}
            <div className="flex items-center gap-2">
              <button className="px-3 py-1.5 rounded-lg text-[#9CA3AF] hover:text-[#E5E7EB] hover:bg-[#0B1120] transition-colors text-sm">
                Crypto
              </button>
              <button className="px-3 py-1.5 rounded-lg text-[#9CA3AF] hover:text-[#E5E7EB] hover:bg-[#0B1120] transition-colors text-sm">
                Earnings
              </button>
              <button className="px-3 py-1.5 rounded-lg text-[#9CA3AF] hover:text-[#E5E7EB] hover:bg-[#0B1120] transition-colors text-sm">
                Screener
              </button>
            </div>
          </div>

          {/* Market Status */}
          <div className="flex items-center gap-4 text-sm">
            <span className="text-[#9CA3AF]">1 Nov 2025, IST • Market Closed</span>
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
