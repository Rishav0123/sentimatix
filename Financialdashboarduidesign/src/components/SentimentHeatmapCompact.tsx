const sectors = [
  { name: "Technology", sentiment: 82, color: "bg-[#10B981]" },
  { name: "Finance", sentiment: 65, color: "bg-[#3B82F6]" },
  { name: "Healthcare", sentiment: 58, color: "bg-blue-400" },
  { name: "Energy", sentiment: 45, color: "bg-yellow-500" },
  { name: "Consumer", sentiment: 72, color: "bg-[#10B981]" },
  { name: "Industrial", sentiment: 55, color: "bg-blue-400" },
];

export function SentimentHeatmapCompact() {
  const getSentimentColor = (sentiment: number) => {
    if (sentiment >= 70) return "bg-[#10B981]";
    if (sentiment >= 60) return "bg-[#3B82F6]";
    if (sentiment >= 50) return "bg-blue-400";
    if (sentiment >= 40) return "bg-yellow-500";
    return "bg-red-500";
  };

  const getSentimentOpacity = (sentiment: number) => {
    return `${Math.max(30, sentiment)}%`;
  };

  return (
    <div className="bg-[#111827] rounded-xl p-5 border border-gray-800">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-[#E5E7EB]">Sentiment by Sector</h3>
        <p className="text-xs text-[#9CA3AF]">Live</p>
      </div>
      <div className="grid grid-cols-3 gap-2">
        {sectors.map((sector) => (
          <div
            key={sector.name}
            className={`${getSentimentColor(sector.sentiment)} rounded-lg p-3 relative overflow-hidden group cursor-pointer transition-transform hover:scale-105`}
            style={{ opacity: getSentimentOpacity(sector.sentiment) }}
          >
            <div className="relative z-10">
              <p className="text-white text-xs mb-0.5">{sector.name}</p>
              <p className="text-white text-sm opacity-90">{sector.sentiment}</p>
            </div>
            <div className="absolute inset-0 bg-gradient-to-br from-white/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
          </div>
        ))}
      </div>
    </div>
  );
}
