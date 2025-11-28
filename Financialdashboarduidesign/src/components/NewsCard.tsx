import { ExternalLink } from "lucide-react";

interface NewsCardProps {
  headline: string;
  sentiment: "Positive" | "Neutral" | "Negative";
  source: string;
  timestamp: string;
  onClick?: () => void;
}

export function NewsCard({ headline, sentiment, source, timestamp, onClick }: NewsCardProps) {
  const sentimentColors = {
    Positive: "bg-[#10B981]/10 text-[#10B981] border-[#10B981]/20",
    Neutral: "bg-blue-500/10 text-blue-400 border-blue-500/20",
    Negative: "bg-red-500/10 text-red-500 border-red-500/20",
  };

  return (
    <div
      onClick={onClick}
      className="bg-[#111827] rounded-lg p-4 border border-gray-800 hover:border-gray-700 transition-all cursor-pointer group"
    >
      <div className="flex items-start justify-between gap-3 mb-2">
        <h3 className="text-[#E5E7EB] flex-1 group-hover:text-[#3B82F6] transition-colors">
          {headline}
        </h3>
        <ExternalLink className="w-4 h-4 text-[#9CA3AF] opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0" />
      </div>
      
      <div className="flex items-center gap-3">
        <span className={`px-2 py-1 rounded text-xs border ${sentimentColors[sentiment]}`}>
          {sentiment}
        </span>
        <span className="text-[#9CA3AF] text-xs">{source}</span>
        <span className="text-[#9CA3AF] text-xs">•</span>
        <span className="text-[#9CA3AF] text-xs">{timestamp}</span>
      </div>
    </div>
  );
}
