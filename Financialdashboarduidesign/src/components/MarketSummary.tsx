import { Send } from "lucide-react";

const newsItems = [
  {
    title: "Sensex, Nifty 50 and Nifty Bank Slip as Expiry Volatility Hits",
    description:
      "India's benchmark indices fell, with Sensex down 0.56% by 0.60% and Nifty Bank lower by 0.44%. Expiry day volatility and weak global sentiment, despite a recent US Fed rate cut, drove broad-based profit-booking, especially in pharma, financials and IT.",
  },
  {
    title: "PSU Banks Outperform in Subdued Session",
    description:
      "Public sector banks bucked the downtrend, showing resilience as most indices slipped. Strong quarterly results from select lenders and hopes of policy support lifted sentiment in the sector.",
  },
  {
    title: "L&T Surges to Record on Robust Earnings",
    description:
      "Larsen & Toubro (L&T) rose 2% to all-time highs after reporting a strong Q2, driven by a healthy order book and positive broker commentary. Engineering and capital goods stocks rallied.",
  },
];

export function MarketSummary() {
  return (
    <div className="bg-[#111827] rounded-xl p-6 border border-gray-800">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-[#E5E7EB] text-xl">Market Summary</h3>
        <p className="text-[#9CA3AF] text-xs">Updated 44 minutes ago</p>
      </div>

      <div className="space-y-4">
        {newsItems.map((item, index) => (
          <div key={index} className="pb-4 border-b border-gray-800 last:border-0 last:pb-0">
            <h4 className="text-[#E5E7EB] mb-2">{item.title}</h4>
            <p className="text-[#9CA3AF] text-sm leading-relaxed">{item.description}</p>
          </div>
        ))}
      </div>

      {/* AI Chat Input */}
      <div className="mt-6 pt-6 border-t border-gray-800">
        <div className="relative">
          <input
            type="text"
            placeholder="Ask any question about finance"
            className="w-full bg-[#0B1120] border border-gray-800 rounded-lg pl-4 pr-24 py-3 text-[#E5E7EB] placeholder:text-[#9CA3AF] focus:outline-none focus:border-[#3B82F6] transition-colors"
          />
          <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-2">
            <button className="w-8 h-8 rounded hover:bg-gray-800 flex items-center justify-center transition-colors">
              <span className="text-[#9CA3AF] text-sm">🔍</span>
            </button>
            <button className="w-8 h-8 rounded hover:bg-gray-800 flex items-center justify-center transition-colors">
              <span className="text-[#9CA3AF] text-sm">📎</span>
            </button>
            <button className="w-8 h-8 rounded hover:bg-gray-800 flex items-center justify-center transition-colors">
              <span className="text-[#9CA3AF] text-sm">📍</span>
            </button>
            <button className="w-8 h-8 bg-[#3B82F6] hover:bg-[#3B82F6]/90 rounded flex items-center justify-center transition-colors">
              <Send className="w-4 h-4 text-white" />
            </button>
          </div>
        </div>

        {/* Additional insights */}
        <div className="mt-4 flex flex-wrap gap-2">
          <button className="px-3 py-1.5 bg-[#0B1120] border border-gray-800 rounded-lg text-[#9CA3AF] text-xs hover:border-gray-700 transition-colors">
            🇮🇳 Indian Markets
          </button>
          <button className="px-3 py-1.5 bg-[#0B1120] border border-gray-800 rounded-lg text-[#9CA3AF] text-xs hover:border-gray-700 transition-colors">
            Stocks -8%
          </button>
          <button className="px-3 py-1.5 bg-[#0B1120] border border-gray-800 rounded-lg text-[#9CA3AF] text-xs hover:border-gray-700 transition-colors">
            Breakdowns
          </button>
          <button className="px-3 py-1.5 bg-[#0B1120] border border-gray-800 rounded-lg text-[#9CA3AF] text-xs hover:border-gray-700 transition-colors">
            Outlook
          </button>
        </div>
      </div>
    </div>
  );
}
