import { TrendingUp, TrendingDown } from "lucide-react";

const topMovers = [
  { ticker: "INFY", name: "Infosys", change: 12.5, sentiment: 85 },
  { ticker: "TCS", name: "Tata Consultancy", change: 8.3, sentiment: 78 },
  { ticker: "WIPRO", name: "Wipro Limited", change: 6.7, sentiment: 72 },
  { ticker: "HCLTECH", name: "HCL Technologies", change: -4.2, sentiment: 55 },
  { ticker: "TECHM", name: "Tech Mahindra", change: -2.8, sentiment: 58 },
];

export function TopMovers() {
  return (
    <div className="bg-[#111827] rounded-xl p-6 border border-gray-800">
      <h3 className="text-[#E5E7EB] text-xl mb-4">Top Movers by Sentiment</h3>
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        {topMovers.map((stock) => {
          const isPositive = stock.change > 0;
          return (
            <div
              key={stock.ticker}
              className="bg-[#0B1120] rounded-lg p-4 border border-gray-800 hover:border-gray-700 transition-all cursor-pointer group"
            >
              <div className="flex items-start justify-between mb-2">
                <div>
                  <p className="text-[#E5E7EB]">{stock.ticker}</p>
                  <p className="text-[#9CA3AF] text-xs">{stock.name}</p>
                </div>
                {isPositive ? (
                  <TrendingUp className="w-5 h-5 text-[#10B981]" />
                ) : (
                  <TrendingDown className="w-5 h-5 text-red-500" />
                )}
              </div>
              <div className="flex items-center justify-between">
                <div
                  className={`px-2 py-1 rounded text-sm ${
                    isPositive
                      ? "bg-[#10B981]/10 text-[#10B981]"
                      : "bg-red-500/10 text-red-500"
                  }`}
                >
                  {isPositive ? "+" : ""}
                  {stock.change.toFixed(1)}%
                </div>
                <div className="text-[#9CA3AF] text-xs">
                  Sentiment: <span className="text-[#E5E7EB]">{stock.sentiment}</span>
                </div>
              </div>
              <div className="mt-3 h-1 bg-gray-800 rounded-full overflow-hidden">
                <div
                  className="h-full bg-[#3B82F6] rounded-full transition-all group-hover:bg-[#10B981]"
                  style={{ width: `${stock.sentiment}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
