interface MarketIndexCardProps {
  name: string;
  ticker: string;
  value: string;
  change: number;
  priceData: number[];
}

export function MarketIndexCard({
  name,
  ticker,
  value,
  change,
  priceData,
}: MarketIndexCardProps) {
  const isPositive = change >= 0;
  
  // Safe price data processing
  const safePriceData = Array.isArray(priceData) && priceData.length > 0 ? priceData : [100, 105, 102, 108, 106];
  const maxPrice = Math.max(...safePriceData);
  const minPrice = Math.min(...safePriceData);
  const priceRange = maxPrice - minPrice;

  // Generate price path for chart
  const generatePricePath = () => {
    if (safePriceData.length === 0) return "M 0 20 L 100 20";
    
    const width = 100;
    const height = 40;
    
    const points = safePriceData.map((price, i) => {
      const x = (i / (safePriceData.length - 1)) * width;
      const y = priceRange === 0 ? height / 2 : height - ((price - minPrice) / priceRange) * height;
      return `${i === 0 ? 'M' : 'L'} ${x} ${y}`;
    }).join(' ');
    
    return points;
  };

  return (
    <div className="bg-[#1E293B] rounded-md p-2 border border-gray-700/50 hover:border-gray-600 transition-all duration-200 flex-1 h-24">
      {/* Header with name and percentage */}
      <div className="text-center mb-2">
        <h3 className="text-white text-sm font-bold truncate leading-tight">{name.split(' ')[0]}</h3>
        <div className={`text-sm font-medium ${isPositive ? "text-green-400" : "text-red-400"}`}>
          {isPositive ? "+" : ""}{change.toFixed(1)}%
        </div>
      </div>

      {/* Chart with proper fitting */}
      <div className="relative h-10 bg-gray-900/50 rounded mb-2">
        <svg className="w-full h-full" viewBox="0 0 100 40" preserveAspectRatio="none">
          <defs>
            <linearGradient id={`gradient-${ticker}`} x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor={isPositive ? "#10B981" : "#EF4444"} stopOpacity="0.3"/>
              <stop offset="100%" stopColor={isPositive ? "#10B981" : "#EF4444"} stopOpacity="0"/>
            </linearGradient>
          </defs>
          
          <path
            d={`${generatePricePath()} L 100 40 L 0 40 Z`}
            fill={`url(#gradient-${ticker})`}
          />
          
          <path
            d={generatePricePath()}
            fill="none"
            stroke={isPositive ? "#10B981" : "#EF4444"}
            strokeWidth="2"
            strokeLinecap="round"
          />
        </svg>
      </div>

      {/* Value */}
      <div className="text-center">
        <div className="text-white text-sm font-bold truncate">{Math.round(parseFloat(value.replace(/[₹$,]/g, '')) / 1000)}K</div>
      </div>
    </div>
  );
}
