import { TrendingUp, TrendingDown } from "lucide-react";

interface InsightCardProps {
  title: string;
  value: string;
  change?: number;
  trend?: number[];
  subtitle?: string;
}

export function InsightCard({ title, value, change, trend, subtitle }: InsightCardProps) {
  const isPositive = change && change > 0;
  
  return (
    <div className="bg-[#111827] rounded-xl p-5 border border-gray-800 hover:border-gray-700 transition-colors">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-[#9CA3AF] text-sm mb-1">{title}</p>
          <p className="text-[#E5E7EB] text-2xl mb-1">{value}</p>
          {subtitle && <p className="text-[#9CA3AF] text-xs">{subtitle}</p>}
        </div>
        
        {change !== undefined && (
          <div className={`flex items-center gap-1 px-2 py-1 rounded-lg ${isPositive ? 'bg-green-500/10 text-[#10B981]' : 'bg-red-500/10 text-red-500'}`}>
            {isPositive ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
            <span className="text-sm">{Math.abs(change).toFixed(2)}%</span>
          </div>
        )}
      </div>
      
      {trend && trend.length > 0 && (
        <div className="mt-3 flex items-end gap-1 h-8">
          {trend.map((value, i) => (
            <div
              key={i}
              className="flex-1 bg-[#3B82F6]/30 rounded-sm"
              style={{ height: `${(value / Math.max(...trend)) * 100}%` }}
            />
          ))}
        </div>
      )}
    </div>
  );
}
