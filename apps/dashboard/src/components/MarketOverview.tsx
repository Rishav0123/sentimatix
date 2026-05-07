import { MarketSummary } from "./MarketSummary";
import { Standouts } from "./Standouts";
import { MarketIndices } from "./MarketIndices";
import { ExampleUsage } from "./ExampleUsage";

interface MarketOverviewProps {
  onStockSelect: (ticker: string) => void;
}

export function MarketOverview({ onStockSelect }: MarketOverviewProps) {
  return (
    <div className="space-y-6">
      <div className="bg-[#111827] rounded-xl p-6 border border-gray-800">
        <h2 className="text-[#E5E7EB] text-xl mb-4">Market Overview</h2>
        <p className="text-[#9CA3AF]">
          Real-time market data with news summary and standout stocks
        </p>
      </div>
      
      {/* Market Indices */}
      <MarketIndices />
      
      {/* Example Usage */}
      <ExampleUsage />
      
      {/* Market Summary */}
      <MarketSummary />
      
      {/* Standouts */}
      <Standouts onStockClick={onStockSelect} />
    </div>
  );
}
