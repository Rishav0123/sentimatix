import { NewsCard } from "./NewsCard";

const newsItems = [
  {
    headline: "Infosys announces Q4 earnings beat with strong digital revenue growth",
    sentiment: "Positive" as const,
    source: "Reuters",
    timestamp: "2 hours ago",
  },
  {
    headline: "Major cloud partnership expansion announced with Fortune 500 client",
    sentiment: "Positive" as const,
    source: "Bloomberg",
    timestamp: "5 hours ago",
  },
  {
    headline: "Tech sector faces headwinds as interest rates remain elevated",
    sentiment: "Negative" as const,
    source: "CNBC",
    timestamp: "8 hours ago",
  },
  {
    headline: "Analyst maintains neutral rating on IT services sector outlook",
    sentiment: "Neutral" as const,
    source: "Morgan Stanley",
    timestamp: "1 day ago",
  },
  {
    headline: "Infosys wins multi-year contract for AI transformation project",
    sentiment: "Positive" as const,
    source: "Financial Times",
    timestamp: "1 day ago",
  },
  {
    headline: "Quarterly revenue guidance meets market expectations",
    sentiment: "Neutral" as const,
    source: "Wall Street Journal",
    timestamp: "2 days ago",
  },
];

export function NewsFeed() {
  return (
    <div className="bg-[#111827] rounded-xl p-6 border border-gray-800">
      <h3 className="text-[#E5E7EB] text-xl mb-4">Recent News & Headlines</h3>
      <div className="space-y-3 max-h-[500px] overflow-y-auto pr-2 scrollbar-thin scrollbar-thumb-gray-700 scrollbar-track-transparent">
        {newsItems.map((item, index) => (
          <NewsCard
            key={index}
            {...item}
            onClick={() => console.log("Open news detail:", item.headline)}
          />
        ))}
      </div>
    </div>
  );
}
