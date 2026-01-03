import { useState, useEffect } from "react";

interface SectorData {
  sector: string;
  sentiment_score: number;
  news_count: number;
  positive_count: number;
  negative_count: number;
  neutral_count: number;
}

interface SectorAPIResponse {
  data: SectorData[];
  meta: {
    period_days: number;
    start_date: string;
    end_date: string;
    total_sectors: number;
    total_news_items: number;
  };
}

export function SentimentHeatmap() {
  const [sectorData, setSectorData] = useState<SectorData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<string>("");

  // API configuration
  const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

  const fetchSectorSentiment = async () => {
    try {
      setLoading(true);
      setError(null);
      
      console.log('📊 Fetching sector sentiment data from new endpoint...');
      
      // Use the new sector sentiment endpoint with longer period to get more data
      const response = await fetch(`${API_BASE_URL}/api/sector-sentiment?days=365`);
      
      if (!response.ok) {
        throw new Error(`API Error: ${response.status} ${response.statusText}`);
      }
      
      const apiData: SectorAPIResponse = await response.json();
      
      console.log('✅ Sector sentiment API response:', apiData);
      
      // Transform the data to match our component interface
      const transformedData: SectorData[] = apiData.data.map(item => ({
        sector: item.sector,
        sentiment_score: item.sentiment_score,
        news_count: item.news_count,
        positive_count: item.positive_count,
        negative_count: item.negative_count,
        neutral_count: item.neutral_count
      }));
      
      setSectorData(transformedData);
      setLastUpdated(new Date().toLocaleTimeString());
      
      console.log(`📊 Processed ${transformedData.length} sectors from ${apiData.meta.total_news_items} news items`);
      
    } catch (err) {
      console.error('❌ Error fetching sector sentiment:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch sector data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSectorSentiment();
    
    // Refresh every 5 minutes
    const interval = setInterval(fetchSectorSentiment, 5 * 60 * 1000);
    
    return () => clearInterval(interval);
  }, []);
  const getSentimentColor = (sentiment: number) => {
    if (sentiment >= 30) return "bg-[#10B981]";      // Strong positive: >= 30
    if (sentiment >= 15) return "bg-[#3B82F6]";      // Moderate positive: 15-29
    if (sentiment >= 5) return "bg-blue-400";        // Mild positive: 5-14
    if (sentiment >= -5) return "bg-gray-500";       // Neutral: -5 to 4
    if (sentiment >= -15) return "bg-yellow-500";    // Mild negative: -15 to -6
    if (sentiment >= -30) return "bg-orange-500";    // Moderate negative: -30 to -16
    return "bg-red-500";                             // Strong negative: < -30
  };

  const getSentimentOpacity = (sentiment: number) => {
    // Convert -50 to 50 scale to opacity percentage (40% to 90%)
    const normalizedSentiment = Math.max(-50, Math.min(50, sentiment)); // Clamp to -50 to 50
    const opacity = ((normalizedSentiment + 50) / 100) * 50 + 40; // Map to 40-90%
    return `${Math.round(opacity)}%`;
  };

  return (
    <div className="bg-[#111827] rounded-xl p-6 border border-gray-800">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-[#E5E7EB] text-xl">Top Sector Sentiments (Last Year)</h3>
        <button
          onClick={fetchSectorSentiment}
          disabled={loading}
          className="text-xs text-[#9CA3AF] hover:text-[#E5E7EB] transition-colors disabled:opacity-50"
        >
          {loading ? "Updating..." : "Refresh"}
        </button>
      </div>

      {error && (
        <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-3 mb-4">
          <p className="text-red-400 text-sm">⚠️ {error}</p>
        </div>
      )}

      {loading && sectorData.length === 0 ? (
        <div className="flex items-center justify-center h-32">
          <p className="text-[#9CA3AF]">Loading sector data...</p>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-5 gap-3">
            {sectorData.slice(0, 10).map((sector) => (
              <div
                key={sector.sector}
                className={`${getSentimentColor(sector.sentiment_score)} rounded-lg p-4 relative overflow-hidden group cursor-pointer transition-transform hover:scale-105`}
                style={{ opacity: getSentimentOpacity(sector.sentiment_score) }}
                title={`${sector.sector}: ${sector.sentiment_score}/100 (${sector.news_count} news items from last year)`}
              >
                <div className="relative z-10">
                  <p className="text-white text-sm mb-1 truncate">{sector.sector}</p>
                  <p className="text-white opacity-90 text-lg font-semibold">{sector.sentiment_score}</p>
                  <p className="text-white opacity-70 text-xs">{sector.news_count} items</p>
                </div>
                <div className="absolute inset-0 bg-gradient-to-br from-white/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
              </div>
            ))}
          </div>

          {sectorData.length === 0 && !loading && (
            <div className="text-center py-8">
              <p className="text-[#9CA3AF]">No sector data available</p>
            </div>
          )}
        </>
      )}

      <div className="flex items-center justify-between mt-4 pt-4 border-t border-gray-800">
        <div className="flex items-center gap-2 text-xs text-[#9CA3AF]">
          <div className="w-3 h-3 bg-red-500 rounded-sm" />
          <span>Strong Negative</span>
          <div className="w-3 h-3 bg-orange-500 rounded-sm ml-2" />
          <span>Negative</span>
          <div className="w-3 h-3 bg-gray-500 rounded-sm ml-2" />
          <span>Neutral</span>
          <div className="w-3 h-3 bg-blue-400 rounded-sm ml-2" />
          <span>Positive</span>
          <div className="w-3 h-3 bg-[#10B981] rounded-sm ml-2" />
          <span>Strong Positive</span>
        </div>
        <p className="text-xs text-[#9CA3AF]">
          {lastUpdated ? `Updated ${lastUpdated}` : "Loading..."}
        </p>
      </div>
    </div>
  );
}
