import React, { useEffect, useState } from 'react';
import { TrendingUp, TrendingDown, Minus, Calendar, Tag } from 'lucide-react';

interface Development {
  id: number;
  symbol: string;
  title: string;
  summary: string;
  category: string;
  sentiment: 'positive' | 'negative' | 'neutral';
  impact_score: number;
  development_date: string;
  created_at: string;
  source_article_count: number;
}

interface RecentDevelopmentsProps {
  symbol?: string;
  days?: number;
  limit?: number;
}

export function RecentDevelopments({ symbol, days = 7, limit = 6 }: RecentDevelopmentsProps = {}) {
  const [developments, setDevelopments] = useState<Development[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<string>('');

  useEffect(() => {
    fetchDevelopments();
  }, [symbol, days, limit]);

  const fetchDevelopments = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams({
        days: days.toString(),
        limit: limit.toString(),
      });
      
      if (symbol) {
        params.append('stock_symbol', symbol);
      }

      const response = await fetch(`http://localhost:8000/api/developments?${params}`);
      const data = await response.json();
      
      if (response.ok) {
        setDevelopments(data.data || []);
        setLastUpdate(formatDate(new Date().toISOString()));
      } else {
        setError(data.error || 'Failed to fetch developments');
      }
    } catch (err) {
      setError('Network error');
      console.error('Error fetching developments:', err);
    } finally {
      setLoading(false);
    }
  };

  const getCategoryColor = (category: string) => {
    const colors: Record<string, string> = {
      earnings: 'bg-emerald-500/10 text-emerald-400',
      merger: 'bg-purple-500/10 text-purple-400',
      regulatory: 'bg-blue-500/10 text-blue-400',
      product: 'bg-amber-500/10 text-amber-400',
      financial: 'bg-cyan-500/10 text-cyan-400',
      management: 'bg-pink-500/10 text-pink-400',
      partnership: 'bg-indigo-500/10 text-indigo-400',
      expansion: 'bg-orange-500/10 text-orange-400',
      general: 'bg-slate-500/10 text-slate-400'
    };
    return colors[category] || colors.general;
  };

  const getCategoryEmoji = (category: string) => {
    const emojis: Record<string, string> = {
      earnings: '📊',
      merger: '🤝',
      regulatory: '⚖️',
      product: '🚀',
      financial: '💰',
      management: '👔',
      partnership: '🤝',
      expansion: '📈',
      general: '📰'
    };
    return emojis[category] || emojis.general;
  };

  const getSentimentEmoji = (sentiment: string) => {
    switch (sentiment) {
      case 'positive':
        return '✅';
      case 'negative':
        return '⚠️';
      default:
        return '➖';
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffHours = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60));
    
    if (diffHours < 1) return 'Just now';
    if (diffHours < 24) return `${diffHours} hours ago`;
    const diffDays = Math.floor(diffHours / 24);
    if (diffDays === 1) return '1 day ago';
    if (diffDays < 7) return `${diffDays} days ago`;
    return date.toLocaleDateString();
  };

  if (loading) {
    return (
      <div className="bg-[#111827] rounded-xl p-6 border border-gray-800">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-[#E5E7EB]">Recent Developments</h3>
          <p className="text-[#9CA3AF] text-xs">Loading...</p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="bg-[#0B1120] rounded-lg p-4 border border-gray-800 animate-pulse">
              <div className="h-4 bg-gray-700 rounded w-3/4 mb-3"></div>
              <div className="h-3 bg-gray-700 rounded w-full mb-2"></div>
              <div className="h-3 bg-gray-700 rounded w-2/3"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-[#111827] rounded-xl p-6 border border-gray-800">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-[#E5E7EB]">Recent Developments</h3>
          <p className="text-rose-400 text-xs">{error}</p>
        </div>
      </div>
    );
  }

  if (developments.length === 0) {
    return (
      <div className="bg-[#111827] rounded-xl p-6 border border-gray-800">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-[#E5E7EB]">Recent Developments</h3>
          <p className="text-[#9CA3AF] text-xs">No recent developments</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-[#111827] rounded-xl p-6 border border-gray-800">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-[#E5E7EB]">Recent Developments</h3>
        <p className="text-[#9CA3AF] text-xs">Updated {lastUpdate}</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {developments.slice(0, 3).map((dev) => (
          <div
            key={dev.id}
            className="bg-[#0B1120] rounded-lg p-4 border border-gray-800 hover:border-gray-700 transition-all cursor-pointer group"
          >
            <div className="flex items-start justify-between gap-2 mb-2">
              <div className="flex items-center gap-2">
                <span className="text-lg">{getCategoryEmoji(dev.category)}</span>
                <span className={`text-xs px-2 py-0.5 rounded ${getCategoryColor(dev.category)}`}>
                  {dev.category}
                </span>
              </div>
              <span className="text-[#9CA3AF] text-xs">{formatDate(dev.development_date)}</span>
            </div>
            <h4 className="text-[#E5E7EB] mb-2 group-hover:text-[#3B82F6] transition-colors font-medium">
              {dev.title}
            </h4>
            <p className="text-[#9CA3AF] text-sm leading-relaxed line-clamp-3">
              {dev.summary}
            </p>
            <div className="flex items-center gap-2 mt-3 text-xs">
              <span className="text-slate-500">
                {getSentimentEmoji(dev.sentiment)} {dev.sentiment}
              </span>
              <span className="text-slate-600">•</span>
              <span className="text-slate-500">
                Impact: {(dev.impact_score * 100).toFixed(0)}%
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
