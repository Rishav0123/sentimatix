import { useState, useEffect } from "react";

interface MarketSummaryItem {
  title: string;
  description: string;
  category: string;
  sentiment: string;
  impact_score: number;
  source: string;
  published_at: string;
  related_stock: string;
}

interface MarketSummaryData {
  summary_items: MarketSummaryItem[];
  market_sentiment: string;
  insights: string[];
  last_updated: string;
  total_news_analyzed: number;
}

export function MarketSummary() {
  const [summaryData, setSummaryData] = useState<MarketSummaryData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // API configuration
  const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

  const fetchMarketSummary = async () => {
    try {
      setLoading(true);
      setError(null);

      console.log('📊 Fetching market summary from API...');

      const response = await fetch(`${API_BASE_URL}/api/market-summary`);

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data: MarketSummaryData = await response.json();
      setSummaryData(data);

      console.log(`✅ Successfully fetched market summary with ${data.summary_items.length} items`);

    } catch (err) {
      console.error('❌ Error fetching market summary:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch market summary');

      // Fallback to mock data
      setSummaryData({
        summary_items: [
          {
            title: "Market Update",
            description: "Markets showing mixed signals today with technology stocks leading gains while banking sector faces pressure.",
            category: "Market Update",
            sentiment: "neutral",
            impact_score: 50,
            source: "Market Analysis",
            published_at: new Date().toISOString(),
            related_stock: "NIFTY"
          }
        ],
        market_sentiment: "neutral",
        insights: ["Mixed trading session"],
        last_updated: new Date().toISOString(),
        total_news_analyzed: 1
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMarketSummary();
  }, []);

  if (loading) {
    return (
      <div className="bg-[#111827] rounded-xl p-6 border border-gray-800">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-[#E5E7EB] text-xl">Market Summary</h3>
          <div className="h-3 bg-gray-700 rounded w-24 animate-pulse"></div>
        </div>
        <div className="space-y-4">
          <div className="pb-4 border-b border-gray-800 animate-pulse">
            <div className="h-4 bg-gray-700 rounded w-3/4 mb-2"></div>
            <div className="h-3 bg-gray-800 rounded w-full mb-1"></div>
            <div className="h-3 bg-gray-800 rounded w-2/3"></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-[#111827] rounded-xl p-6 border border-gray-800">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <h3 className="text-[#E5E7EB] text-xl">Market Summary</h3>
          {summaryData && (
            <span className="text-sm px-2 py-1 rounded text-blue-400 bg-blue-400/10">
              {summaryData.market_sentiment.charAt(0).toUpperCase() + summaryData.market_sentiment.slice(1)}
            </span>
          )}
        </div>
        <p className="text-gray-300 text-xs">
          {summaryData ? 'Recently updated' : 'Loading...'}
        </p>
      </div>

      {error && (
        <div className="bg-yellow-500/10 border border-yellow-500/20 rounded-lg p-3 mb-4">
          <p className="text-yellow-400 text-sm">⚠️ {error}</p>
        </div>
      )}

      <div className="space-y-4">
        {summaryData?.summary_items.map((item, index) => (
          <div key={index} className="pb-4 border-b border-gray-800 last:border-0 last:pb-0">
            <div className="flex items-start justify-between gap-2 mb-2">
              <h4 className="text-[#E5E7EB] flex-1">{item.title}</h4>
              <div className="flex items-center gap-2">
                <span className="text-gray-300 text-xs">{item.category}</span>
              </div>
            </div>
            <p className="text-gray-300 text-sm leading-relaxed">{item.description}</p>
            <div className="flex items-center justify-between mt-2">
              <span className="text-gray-300 text-xs">{item.source}</span>
              {item.related_stock && (
                <span className="text-[#3B82F6] text-xs">{item.related_stock}</span>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
