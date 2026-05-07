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


  const [currentTime, setCurrentTime] = useState(new Date());
  const [marketStatus, setMarketStatus] = useState<string>("");
  const [sentiment, setSentiment] = useState<string>("Neutral Sentiment");

  // Update time every minute
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 60000);
    return () => clearInterval(timer);
  }, []);

  // Calculate Market Status based on timezone
  useEffect(() => {
    const calculateStatus = () => {
      const now = new Date();
      const isWeekend = now.getDay() === 0 || now.getDay() === 6;

      if (currentMarket.id === 'india') {
        // IST Time
        const istTime = new Date(now.toLocaleString("en-US", { timeZone: "Asia/Kolkata" }));
        const hours = istTime.getHours();
        const minutes = istTime.getMinutes();
        const totalMinutes = hours * 60 + minutes;

        // India Market Hours: 9:15 AM - 3:30 PM (15:30)
        const marketOpen = 9 * 60 + 15;
        const marketClose = 15 * 60 + 30;

        if (!isWeekend && totalMinutes >= marketOpen && totalMinutes < marketClose) {
          setMarketStatus("Market Open");
        } else {
          setMarketStatus("Market Closed");
        }
      } else {
        // USA Time (EST/EDT)
        const estTime = new Date(now.toLocaleString("en-US", { timeZone: "America/New_York" }));
        const hours = estTime.getHours();
        const minutes = estTime.getMinutes();
        const totalMinutes = hours * 60 + minutes;

        // NYSE Hours: 9:30 AM - 4:00 PM (16:00)
        const marketOpen = 9 * 60 + 30;
        const marketClose = 16 * 60;

        if (!isWeekend && totalMinutes >= marketOpen && totalMinutes < marketClose) {
          setMarketStatus("Market Open");
        } else {
          setMarketStatus("Market Closed");
        }
      }
    };

    calculateStatus();
  }, [currentMarket, currentTime]);

  // Fetch Sentiment
  useEffect(() => {
    const fetchSentiment = async () => {
      try {
        const API_BASE_URL = ((import.meta as any).env.VITE_API_URL || 'http://localhost:8000').replace(/\/+$/, '').replace(/\/api$/, '');
        const response = await fetch(`${API_BASE_URL}/api/market/insights`);
        if (response.ok) {
          const data = await response.json();
          // Assuming the first insight or a summary field represents overall sentiment
          // Or deriving from the "Bearish"/"Bullish" text usually present in data
          if (data && data.insights && data.insights.length > 0) {
            // Just use the first insight's trend or a summary if available. 
            // For now, let's look for keywords in the first insight title or description
            // Or better, check if there's a dedicated sentiment field. 
            // Based on Insights.tsx, there isn't a global 'sentiment' field in the root response shown, 
            // but visually the screenshot shows "Bearish -49.2%".
            // Let's default to "Neutral" if complex, but try to parse if possible.
            // Actually, simplest is to just keep "Neutral" dynamic if we can't easily derive it, 
            // BUT user asked for dynamic.
            // Let's use the first insight's trend.
            const mainTrend = data.insights[0]?.trend;
            if (mainTrend === 'up') setSentiment("Bullish Sentiment");
            else if (mainTrend === 'down') setSentiment("Bearish Sentiment");
            else setSentiment("Neutral Sentiment");
          }
        }
      } catch (e) {
        console.error("Failed to fetch sentiment for TopNav", e);
      }
    };
    fetchSentiment();
  }, []);

  const formatDate = (date: Date, marketId: string) => {
    const options: Intl.DateTimeFormatOptions = {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
      timeZone: marketId === 'india' ? 'Asia/Kolkata' : 'America/New_York'
    };
    return date.toLocaleDateString('en-GB', options);
  };

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
                      className={`w-full flex items-center gap-2 px-3 py-2 text-left hover:bg-[#0B1120] transition-colors text-sm ${market.name === selectedMarket ? 'bg-[#0B1120]' : ''
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
              {formatDate(currentTime, currentMarket.id)}, {currentMarket.id === 'india' ? 'IST' : 'EST'} • {marketStatus}
            </span>
            <div className="flex items-center gap-1.5">
              <div className="flex items-center gap-1">
                <div className={`w-1 h-1 rounded-full ${sentiment.includes('Bullish') ? 'bg-green-500' : sentiment.includes('Bearish') ? 'bg-red-500' : 'bg-gray-500'}`}></div>
                <div className={`w-1 h-1 rounded-full ${sentiment.includes('Bullish') ? 'bg-green-500' : sentiment.includes('Bearish') ? 'bg-red-500' : 'bg-gray-500'}`}></div>
                <div className={`w-1 h-1 rounded-full ${sentiment.includes('Bullish') ? 'bg-green-500' : sentiment.includes('Bearish') ? 'bg-red-500' : 'bg-gray-500'}`}></div>
              </div>
              <span className={`${sentiment.includes('Bullish') ? 'text-green-400' : sentiment.includes('Bearish') ? 'text-red-400' : 'text-[#9CA3AF]'}`}>
                {sentiment}
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
