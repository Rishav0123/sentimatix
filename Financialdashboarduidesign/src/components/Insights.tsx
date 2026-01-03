import { useState, useEffect } from "react";
import { TrendingUp, TrendingDown, BarChart3, PieChart, Activity, RefreshCw } from "lucide-react";

interface InsightData {
  title: string;
  value: string;
  change: number;
  trend: 'up' | 'down' | 'neutral';
  description: string;
}

interface SectorPerf {
  sector: string;
  performance: number;
  color: string;
}

interface MarketComposition {
  category: string;
  percentage: number;
  color: string;
}

interface AISignal {
  type: string;
  color: string;
  content: string;
}

interface PremiumInsightsResponse {
  insights: InsightData[];
  sector_performance: SectorPerf[];
  market_composition: MarketComposition[];
  ai_analysis: {
    signals: AISignal[];
  };
}

export function Insights() {
  const [data, setData] = useState<PremiumInsightsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchInsights = async () => {
    try {
      setLoading(true);
      setError(null);
      const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const response = await fetch(`${API_BASE_URL}/api/market/insights`);
      if (!response.ok) throw new Error("Failed to fetch market insights");
      const result = await response.json();
      setData(result);
    } catch (err) {
      console.error("Error fetching insights:", err);
      setError("Unable to load real-time market insights. Please try again later.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInsights();
  }, []);

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'up':
        return <TrendingUp className="w-5 h-5 text-green-400" style={{ color: '#4ade80' }} />;
      case 'down':
        return <TrendingDown className="w-5 h-5 text-red-400" style={{ color: '#f87171' }} />;
      default:
        return <Activity className="w-5 h-5 text-white" style={{ color: 'white' }} />;
    }
  };

  const getTrendColor = (trend: string) => {
    switch (trend) {
      case 'up':
        return 'text-green-400';
      case 'down':
        return 'text-red-400';
      default:
        return 'text-white';
    }
  };

  if (loading) {
    return (
      <div className="p-6 max-w-[1800px] mx-auto h-full overflow-y-auto">
        <div className="mb-6 flex justify-between items-center">
          <div>
            <h1 className="text-white text-2xl font-bold mb-2">Market Insights</h1>
            <p className="text-gray-300">Loading AI-powered market analysis...</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="bg-[#1E293B] rounded-lg p-6 animate-pulse border border-gray-700/50">
              <div className="h-4 bg-gray-700 rounded w-3/4 mb-4"></div>
              <div className="h-8 bg-gray-700 rounded w-1/2 mb-2"></div>
              <div className="h-3 bg-gray-700 rounded w-full"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="p-6 max-w-[1800px] mx-auto h-full flex flex-col items-center justify-center text-center">
        <div className="bg-red-900/20 border border-red-800 p-8 rounded-xl max-w-md">
          <Activity className="w-12 h-12 text-red-400 mx-auto mb-4" />
          <h2 className="text-white text-xl font-bold mb-2">Service Unavailable</h2>
          <p className="text-gray-300 mb-6">{error || "Something went wrong"}</p>
          <button
            onClick={fetchInsights}
            className="px-6 py-2 bg-red-600 hover:bg-red-500 text-white rounded-lg transition-colors flex items-center gap-2 mx-auto"
          >
            <RefreshCw className="w-4 h-4" />
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-[1800px] mx-auto h-full overflow-y-auto">
      <div className="mb-6 flex justify-between items-center">
        <div>
          <h1 className="text-white text-2xl font-bold mb-2">Market Insights</h1>
          <p className="text-white">Real-time database analysis and AI trends</p>
        </div>
        <button
          onClick={fetchInsights}
          className="p-2 text-gray-400 hover:text-white transition-colors rounded-lg border border-gray-800 hover:border-gray-700"
          title="Refresh Data"
        >
          <RefreshCw className="w-5 h-5" />
        </button>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {data.insights.map((insight, index) => (
          <div key={index} className="bg-[#1E293B] rounded-lg p-6 border border-gray-700/50 hover:border-gray-600 transition-colors group">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-white text-sm font-medium">{insight.title}</h3>
              {getTrendIcon(insight.trend)}
            </div>

            <div className="mb-2">
              <div className="text-white text-2xl font-bold" style={{ color: 'white' }}>{insight.value}</div>
              <div className={`text-sm font-semibold ${getTrendColor(insight.trend)}`} style={{ color: insight.trend === 'up' ? '#4ade80' : insight.trend === 'down' ? '#f87171' : 'white' }}>
                {insight.change > 0 ? '+' : ''}{insight.change}%
              </div>
            </div>

            <p className="text-white text-xs leading-relaxed">{insight.description}</p>
          </div>
        ))}
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <div className="bg-[#1E293B] rounded-lg p-6 border border-gray-700/50">
          <div className="flex items-center gap-2 mb-4 text-blue-400">
            <BarChart3 className="w-5 h-5" />
            <h3 className="text-white text-lg font-semibold">Sector Performance</h3>
          </div>

          <div className="space-y-4">
            {data.sector_performance.map((item, index) => (
              <div key={index} className="flex items-center justify-between group">
                <div className="flex items-center gap-3">
                  <div className={`w-3 h-3 rounded ${item.color}`}></div>
                  <span className="text-white">{item.sector}</span>
                </div>
                <span className={`text-sm font-bold ${item.performance >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                  {item.performance > 0 ? '+' : ''}{item.performance}%
                </span>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-[#1E293B] rounded-lg p-6 border border-gray-700/50">
          <div className="flex items-center gap-2 mb-4 text-green-400">
            <PieChart className="w-5 h-5" />
            <h3 className="text-white text-lg font-semibold">Market Composition</h3>
          </div>

          <div className="space-y-4">
            {data.market_composition.map((item, index) => (
              <div key={index} className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-white">{item.category}</span>
                  <span className="text-white font-medium" style={{ color: 'white' }}>{item.percentage}%</span>
                </div>
                <div className="w-full bg-gray-700/50 rounded-full h-1.5 overflow-hidden">
                  <div
                    className={`h-full transition-all duration-1000 ${item.color}`}
                    style={{ width: `${item.percentage}%` }}
                  ></div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* AI Insights */}
      <div className="bg-[#1E293B] rounded-lg p-6 border border-gray-700/50">
        <div className="flex items-center gap-2 mb-4">
          <Activity className="w-5 h-5 text-purple-400" />
          <h3 className="text-white text-lg font-semibold">AI Market Analysis</h3>
        </div>

        <div className="space-y-4">
          {data.ai_analysis.signals.map((signal, index) => (
            <div key={index} className="bg-[#0F172A] rounded-lg p-4 border border-gray-800 hover:border-gray-700 transition-colors">
              <h4 className={`${signal.color} font-medium mb-1 text-sm uppercase tracking-wider`}>{signal.type}</h4>
              <p className="text-white text-sm leading-relaxed">
                {signal.content}
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
