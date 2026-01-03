interface StandoutCardProps {
  name: string;
  ticker: string;
  exchange: string;
  price: string;
  change: number;
  changeValue: string;
  logo: string;
  volume: string;
  marketCap: string;
  peRatio: string;
  dividendYield: string;
  chartData: number[];
  description: string;
  onClick?: () => void;
}

export function StandoutCard({
  name,
  ticker,
  exchange,
  price,
  change,
  changeValue,
  logo,
  volume,
  marketCap,
  peRatio,
  dividendYield,
  chartData,
  description,
  onClick,
}: StandoutCardProps) {
  const isPositive = change >= 0;
  
  // Safe chart data processing
  const safeChartData = Array.isArray(chartData) && chartData.length > 0 ? chartData : [100, 100];
  const maxValue = Math.max(...safeChartData);
  const minValue = Math.min(...safeChartData);
  const range = maxValue - minValue;
  
  // Prevent division by zero
  const normalizedData = range === 0 
    ? safeChartData.map(() => 64) // Middle of 128px height
    : safeChartData.map(value => 128 - ((value - minValue) / range) * 128);

  // Generate safe SVG path
  const generatePath = (data: number[], closePath = false) => {
    if (data.length === 0) return "M 0 64 L 100 64";
    
    const width = 100; // Use percentage width
    const points = data.map((y, i) => {
      const x = (i / (data.length - 1)) * width;
      return `${i === 0 ? 'M' : 'L'} ${x} ${y}`;
    }).join(' ');
    
    return closePath ? `${points} L ${width} 128 L 0 128 Z` : points;
  };

  return (
    <div
      onClick={onClick}
      className="bg-[#111827] rounded-xl p-6 border border-gray-800 hover:border-gray-700 transition-all cursor-pointer group"
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-[#0B1120] rounded border border-gray-800 flex items-center justify-center text-lg">
            {logo}
          </div>
          <div>
            <h4 className="text-[#E5E7EB]">{name}</h4>
            <p className="text-[#9CA3AF] text-xs">
              {ticker} · {exchange}
            </p>
          </div>
        </div>
        <div className="text-right">
          <p className="text-[#E5E7EB] text-xl">{price}</p>
          <p
            className={`text-sm ${
              isPositive ? "text-[#10B981]" : "text-red-500"
            }`}
          >
            {isPositive ? "+" : ""}
            {changeValue}
          </p>
        </div>
      </div>

      {/* Chart */}
      <div className="relative h-32 mb-4">
        <svg className="w-full h-full" viewBox="0 0 100 128" preserveAspectRatio="none">
          <defs>
            <linearGradient id={`gradient-${ticker}`} x1="0%" y1="0%" x2="0%" y2="100%">
              <stop
                offset="0%"
                style={{
                  stopColor: isPositive ? "#10B981" : "#EF4444",
                  stopOpacity: 0.3,
                }}
              />
              <stop
                offset="100%"
                style={{
                  stopColor: isPositive ? "#10B981" : "#EF4444",
                  stopOpacity: 0,
                }}
              />
            </linearGradient>
          </defs>
          
          {/* Area */}
          <path
            d={generatePath(normalizedData, true)}
            fill={`url(#gradient-${ticker})`}
          />
          
          {/* Line */}
          <path
            d={generatePath(normalizedData, false)}
            fill="none"
            stroke={isPositive ? "#10B981" : "#EF4444"}
            strokeWidth="0.5"
          />
        </svg>
        
        <p className="absolute bottom-0 right-0 text-[#9CA3AF] text-xs">
          Prev: {safeChartData[0]?.toFixed(2) || 'N/A'}
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 gap-3 mb-4 pb-4 border-b border-gray-800">
        <div>
          <p className="text-[#9CA3AF] text-xs mb-1">Volume</p>
          <p className="text-[#E5E7EB] text-sm">{volume}</p>
        </div>
        <div>
          <p className="text-[#9CA3AF] text-xs mb-1">Market Cap</p>
          <p className="text-[#E5E7EB] text-sm">{marketCap}</p>
        </div>
        <div>
          <p className="text-[#9CA3AF] text-xs mb-1">P/E Ratio</p>
          <p className="text-[#E5E7EB] text-sm">{peRatio}</p>
        </div>
        <div>
          <p className="text-[#9CA3AF] text-xs mb-1">Dividend Yield</p>
          <p className="text-[#E5E7EB] text-sm">{dividendYield}</p>
        </div>
      </div>

      {/* Description */}
      <p className="text-[#9CA3AF] text-sm leading-relaxed">{description}</p>
    </div>
  );
}
