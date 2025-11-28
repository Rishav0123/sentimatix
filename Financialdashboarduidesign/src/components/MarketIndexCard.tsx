import { TrendingDown, TrendingUp } from "lucide-react";

interface MarketIndexCardProps {
  name: string;
  ticker: string;
  exchange: string;
  value: string;
  change: number;
  changeValue: string;
  chartData: number[];
  onClick?: () => void;
}

export function MarketIndexCard({
  name,
  ticker,
  exchange,
  value,
  change,
  changeValue,
  chartData,
  onClick,
}: MarketIndexCardProps) {
  const isPositive = change >= 0;
  const maxValue = Math.max(...chartData);
  const minValue = Math.min(...chartData);

  return (
    <div
      onClick={onClick}
      className="bg-[#111827] rounded-xl p-4 border border-gray-800 hover:border-gray-700 transition-all cursor-pointer group"
    >
      <div className="mb-3">
        <h3 className="text-[#E5E7EB] mb-1">{name}</h3>
        <p className="text-[#9CA3AF] text-xs">
          {ticker} · {exchange}
        </p>
      </div>

      <div className="flex items-center gap-2 mb-3">
        <span
          className={`text-xs px-2 py-0.5 rounded ${
            isPositive
              ? "bg-[#10B981]/10 text-[#10B981]"
              : "bg-red-500/10 text-red-500"
          }`}
        >
          {isPositive ? "+" : ""}
          {change.toFixed(2)}%
        </span>
        <span
          className={`text-xs ${
            isPositive ? "text-[#10B981]" : "text-red-500"
          }`}
        >
          {isPositive ? "+" : ""}
          {changeValue}
        </span>
      </div>

      {/* Mini Chart */}
      <div className="h-16 flex items-end gap-0.5 mb-3">
        {chartData.map((value, i) => {
          const height = ((value - minValue) / (maxValue - minValue)) * 100;
          return (
            <div
              key={i}
              className={`flex-1 rounded-sm transition-all ${
                isPositive ? "bg-[#10B981]/30" : "bg-red-500/30"
              }`}
              style={{ height: `${Math.max(height, 10)}%` }}
            />
          );
        })}
      </div>

      <div className="text-[#E5E7EB] text-xl">{value}</div>
    </div>
  );
}
