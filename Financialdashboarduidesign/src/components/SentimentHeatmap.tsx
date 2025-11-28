import { useState, useEffect } from "react";

interface SectorData {
  name: string;
  sentiment: number;
  count: number;
}

interface NewsItem {
  id: string;
  sector?: string;
  impact_score: number;
  sentiment: string;
  published_at?: string;
}

interface APIResponse {
  data: NewsItem[];
  meta: {
    found: number;
    returned: number;
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
      
      // Calculate date range for last 1 month
      const endDate = new Date();
      const startDate = new Date();
      startDate.setMonth(startDate.getMonth() - 1);
      
      const endDateStr = endDate.toISOString().split('T')[0];
      const startDateStr = startDate.toISOString().split('T')[0];
      
      console.log(`📅 Fetching news from ${startDateStr} to ${endDateStr}`);
      
      // Fetch data with smaller limit to avoid API 422 errors
      const response = await fetch(`${API_BASE_URL}/api/news?limit=100`);
      
      if (!response.ok) {
        throw new Error(`API Error: ${response.status}`);
      }
      
      const apiData: APIResponse = await response.json();
      
      // Filter for last 1 month based on published_at
      const oneMonthData = apiData.data.filter(item => {
        if (!item.published_at) return false;
        const itemDate = new Date(item.published_at);
        return itemDate >= startDate && itemDate <= endDate;
      });
      
      console.log(`📊 Filtered ${oneMonthData.length} news items from last month (from ${apiData.data.length} total)`);
      
      // Group news by sector and calculate average sentiment
      const sectorMap = new Map<string, { scores: number[], count: number }>();
      
      oneMonthData.forEach(item => {
        const sector = item.sector || 'Other';
        const score = item.impact_score || 0;
        
        if (!sectorMap.has(sector)) {
          sectorMap.set(sector, { scores: [], count: 0 });
        }
        
        const sectorInfo = sectorMap.get(sector)!;
        sectorInfo.scores.push(score);
        sectorInfo.count++;
      });
      
      // Calculate average sentiment score for each sector and convert to -100 to +100 scale
      const allSectors: SectorData[] = Array.from(sectorMap.entries())
        .map(([name, data]) => {
          const avgScore = data.scores.reduce((sum, score) => sum + score, 0) / data.scores.length;
          // Convert impact score (-1 to 1) to sentiment scale (-100 to +100)
          const sentiment = Math.round(avgScore * 100);
          
          return {
            name,
            sentiment,
            count: data.count
          };
        })
        .filter(sector => sector.count >= 2); // Only show sectors with at least 2 news items
      
      // Get top 5 positive and top 5 negative sectors
      const positiveSectors = allSectors
        .filter(sector => sector.sentiment > 0)
        .sort((a, b) => b.sentiment - a.sentiment)
        .slice(0, 5);
      
      const negativeSectors = allSectors
        .filter(sector => sector.sentiment < 0)
        .sort((a, b) => a.sentiment - b.sentiment)
        .slice(0, 5);
      
      // Combine top positive and negative sectors
      const sectors = [...positiveSectors, ...negativeSectors];
      
      setSectorData(sectors);
      setLastUpdated(new Date().toLocaleTimeString());
      
      console.log('📊 Last month sector sentiment data:', sectors);
      console.log(`📅 Date range: ${startDateStr} to ${endDateStr}`);
      
    } catch (err) {
      console.error('❌ Error fetching sector sentiment:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch data');
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
    if (sentiment >= 50) return "bg-[#10B981]";    // Positive: >= 50
    if (sentiment >= 20) return "bg-[#3B82F6]";    // Moderate positive: 20-49
    if (sentiment >= -20) return "bg-blue-400";    // Neutral: -20 to 19
    if (sentiment >= -50) return "bg-yellow-500";  // Moderate negative: -50 to -21
    return "bg-red-500";                           // Negative: < -50
  };

  const getSentimentOpacity = (sentiment: number) => {
    // Convert -100 to 100 scale to opacity percentage (30% to 90%)
    const normalizedSentiment = (sentiment + 100) / 200; // Convert to 0-1 scale
    const opacity = Math.max(30, Math.min(90, normalizedSentiment * 60 + 30));
    return `${Math.round(opacity)}%`;
  };

  return (
    <div className="bg-[#111827] rounded-xl p-6 border border-gray-800">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-[#E5E7EB] text-xl">Top Sector Sentiments (Last Month)</h3>
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
                key={sector.name}
                className={`${getSentimentColor(sector.sentiment)} rounded-lg p-4 relative overflow-hidden group cursor-pointer transition-transform hover:scale-105`}
                style={{ opacity: getSentimentOpacity(sector.sentiment) }}
                title={`${sector.name}: ${sector.sentiment}/100 (${sector.count} news items from last month)`}
              >
                <div className="relative z-10">
                  <p className="text-white text-sm mb-1 truncate">{sector.name}</p>
                  <p className="text-white opacity-90 text-lg font-semibold">{sector.sentiment}</p>
                  <p className="text-white opacity-70 text-xs">{sector.count} items</p>
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
          <span>Negative</span>
          <div className="w-3 h-3 bg-yellow-500 rounded-sm ml-2" />
          <span>Neutral</span>
          <div className="w-3 h-3 bg-[#10B981] rounded-sm ml-2" />
          <span>Positive</span>
        </div>
        <p className="text-xs text-[#9CA3AF]">
          {lastUpdated ? `Updated ${lastUpdated}` : "Loading..."}
        </p>
      </div>
    </div>
  );
}
