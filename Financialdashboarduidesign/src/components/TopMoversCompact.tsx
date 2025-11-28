import { TrendingUp, TrendingDown } from "lucide-react";

const topMovers = [
  { ticker: "INFY", name: "Infosys", change: 12.5, sentiment: 85 },
  { ticker: "TCS", name: "Tata Consultancy", change: 8.3, sentiment: 78 },
  { ticker: "WIPRO", name: "Wipro Limited", change: 6.7, sentiment: 72 },
];

interface TopMoversCompactProps {
  onStockClick?: (ticker: string) => void;
}

export function TopMoversCompact({ onStockClick }: TopMoversCompactProps) {
  return (
    <div className="bg-[#111827] rounded-xl p-5 border border-gray-800">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-[#E5E7EB]">Top Movers</h3>
        <p className="text-xs text-[#9CA3AF]">By Sentiment</p>
      </div>
      <div className="space-y-2">
        {topMovers.map((stock) => {
          const isPositive = stock.change > 0;
          return (
            <div
              key={stock.ticker}
              onClick={() => onStockClick?.(stock.ticker)}
              className="bg-[#0B1120] rounded-lg p-3 border border-gray-800 hover:border-gray-700 transition-all cursor-pointer group"
            >
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  {isPositive ? (
                    <TrendingUp className="w-4 h-4 text-[#10B981]" />
                  ) : (
                    <TrendingDown className="w-4 h-4 text-red-500" />
                  )}
                  <div>
                    <p className="text-[#E5E7EB] text-sm">{stock.ticker}</p>
                    <p className="text-[#9CA3AF] text-xs">{stock.name}</p>
                  </div>
                </div>
                <div
                  className={`px-2 py-0.5 rounded text-xs ${
                    isPositive
                      ? "bg-[#10B981]/10 text-[#10B981]"
                      : "bg-red-500/10 text-red-500"
                  }`}
                >
                  {isPositive ? "+" : ""}
                  {stock.change.toFixed(1)}%
                </div>
              </div>
              <div className="flex items-center gap-2">
                <div className="flex-1 h-1 bg-gray-800 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-[#3B82F6] rounded-full transition-all group-hover:bg-[#10B981]"
                    style={{ width: `${stock.sentiment}%` }}
                  />
                </div>
                <span className="text-[#9CA3AF] text-xs">{stock.sentiment}</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
