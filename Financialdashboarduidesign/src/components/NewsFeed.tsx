import { useState, useEffect } from "react";
import { Calendar, ExternalLink, TrendingUp, TrendingDown, ChevronLeft, ChevronRight, RefreshCw, Filter } from "lucide-react";

interface NewsArticle {
  id: string;
  title: string;
  content: string;
  published_at: string;
  source: string;
  url: string;
  stock_name: string;
  stock_symbol: string;
  sentiment: string;
  impact_score: number;
  country?: string;
  sector?: string;
  type?: string;
}

interface MetaData {
  found: number;
  returned: number;
  limit: number;
  page: number;
}

export function NewsFeed() {
  const [news, setNews] = useState<NewsArticle[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Pagination State
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalItems, setTotalItems] = useState(0);
  const ITEMS_PER_PAGE = 10;

  // Filter State
  const [sentimentFilter, setSentimentFilter] = useState<'all' | 'positive' | 'negative' | 'neutral'>('all');

  const fetchNews = async (page: number, sentiment: string) => {
    try {
      setLoading(true);

      const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      let url = `${API_BASE_URL}/api/news?page=${page}&limit=${ITEMS_PER_PAGE}`;
      if (sentiment !== 'all') {
        url += `&sentiment=${sentiment}`;
      }

n      console.log(`Fetching: ${url}`);
      const response = await fetch(url);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const responseData = await response.json();

      // Handle the API response format: {meta: {...}, data: [...]}
      let data: any[] = [];

      if (responseData && typeof responseData === 'object') {
        if (responseData.data && Array.isArray(responseData.data)) {
          // Standard Paginated Response
          data = responseData.data;

          // Update Pagination Meta
          if (responseData.meta) {
            const meta: MetaData = responseData.meta;
            setTotalItems(meta.found);
            const calcPages = Math.ceil(meta.found / meta.limit);
            setTotalPages(calcPages || 1);
          }
        } else if (Array.isArray(responseData)) {
          // Direct array format (fallback)
          data = responseData;
          setTotalItems(data.length);
          setTotalPages(1);
        }
      } else {
        throw new Error('Invalid API response format');
      }

      if (Array.isArray(data)) {
        const validNews = data.filter(article =>
          article && typeof article === 'object' && article.title
        ).map(article => ({
          ...article,
          title: article.title || 'No title available',
          content: article.content || 'No content available',
          source: article.source || 'Unknown',
          published_at: article.published_at || new Date().toISOString(),
          // Force existing sentiment or default to neutral
          sentiment: article.sentiment || 'neutral',
          // Force existing score or calculate default
          impact_score: typeof article.impact_score === 'number' ? article.impact_score : (article.sentiment_score ? article.sentiment_score * 100 : 50),
          stock_name: article.stock_name || article.stock_symbol || '',
          url: article.url || '#'
        }));

        setNews(validNews);
        setError(null);
      } else {
        throw new Error('Invalid data format received');
      }
    } catch (err) {
      console.error('Error fetching news:', err);
      setError('Failed to load news');
      setNews([]);
    } finally {
      setLoading(false);
    }
  };

  // Fetch when page or filter changes
  useEffect(() => {
    // Reset to page 1 if filter changes? 
    // Ideally yes, but here specific useEffect for filter change might be better. 
    // Combining them:
    fetchNews(currentPage, sentimentFilter);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }, [currentPage, sentimentFilter]);

  const handlePageChange = (newPage: number) => {
    if (newPage >= 1 && newPage <= totalPages) {
      setCurrentPage(newPage);
    }
  };

  const handleFilterChange = (filter: 'all' | 'positive' | 'negative' | 'neutral') => {
    setSentimentFilter(filter);
    setCurrentPage(1); // Reset to first page when filtering
  };

  const getSentimentIcon = (sentiment: string, score: number) => {
    // Convert impact_score (0-100) to sentiment_score (-1 to 1) for consistency
    const normalizedScore = (score - 50) / 50;

    if (sentiment?.toLowerCase() === 'positive' || normalizedScore > 0.1) {
      return <TrendingUp className="w-4 h-4 text-green-400" />;
    } else if (sentiment?.toLowerCase() === 'negative' || normalizedScore < -0.1) {
      return <TrendingDown className="w-4 h-4 text-red-400" />;
    }
    // Neutral icon
    return <div className="w-4 h-4 rounded-full border-2 border-[#D1D5DB] border-dashed"></div>;
  };

  const formatDate = (dateString: string) => {
    try {
      if (!dateString) return 'Unknown date';
      const date = new Date(dateString);
      if (isNaN(date.getTime())) return 'Invalid date';

      const now = new Date();
      const diffMs = now.getTime() - date.getTime();
      const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
      const diffDays = Math.floor(diffHours / 24);

      if (diffHours < 1) return 'Just now';
      if (diffHours < 24) return `${diffHours}h ago`;
      if (diffDays < 7) return `${diffDays}d ago`;
      return date.toLocaleDateString();
    } catch (error) {
      return 'Unknown date';
    }
  };

  return (
    <div className="p-6 max-w-[1800px] mx-auto h-full overflow-y-auto">
      <style>{`
        .filter-btn-white {
          color: white !important;
        }
      `}</style>
      <div className="mb-6">
        <div className="flex items-end justify-between mb-4">
          <div>
            <h1 className="text-white text-2xl font-bold mb-2">News Feed</h1>
            <p className="text-white">Latest market news and updates</p>
          </div>
          {!loading && !error && (
            <p className="text-white text-sm">
              Showing {news.length} articles (Page {currentPage} of {totalPages})
            </p>
          )}
        </div>

        {/* Filter Toolbar */}
        <div className="flex gap-2 mb-2">
          <button
            onClick={() => handleFilterChange('all')}
            className={`filter-btn-white px-3 py-1.5 rounded-lg text-sm transition-colors border ${sentimentFilter === 'all'
              ? 'bg-blue-600 border-blue-600'
              : 'bg-[#1E293B] border-gray-700 hover:border-gray-500'
              }`}
          >
            All
          </button>
          <button
            onClick={() => handleFilterChange('positive')}
            className={`filter-btn-white px-3 py-1.5 rounded-lg text-sm transition-colors border ${sentimentFilter === 'positive'
              ? 'bg-green-600/20 border-green-500 text-green-400'
              : 'bg-[#1E293B] border-gray-700 hover:border-green-500/50'
              }`}
          >
            Positive
          </button>
          <button
            onClick={() => handleFilterChange('negative')}
            className={`filter-btn-white px-3 py-1.5 rounded-lg text-sm transition-colors border ${sentimentFilter === 'negative'
              ? 'bg-red-600/20 border-red-500 text-red-400'
              : 'bg-[#1E293B] border-gray-700 hover:border-red-500/50'
              }`}
          >
            Negative
          </button>
          <button
            onClick={() => handleFilterChange('neutral')}
            className={`filter-btn-white px-3 py-1.5 rounded-lg text-sm transition-colors border ${sentimentFilter === 'neutral'
              ? 'bg-gray-600/20 border-gray-400'
              : 'bg-[#1E293B] border-gray-700 hover:border-gray-400/50'
              }`}
          >
            Neutral
          </button>
        </div>
      </div>

      {loading ? (
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="bg-[#1E293B] rounded-lg p-6 animate-pulse">
              <div className="h-4 bg-gray-700 rounded w-full mb-2"></div>
              <div className="h-4 bg-gray-700 rounded w-2/3"></div>
            </div>
          ))}
        </div>
      ) : error ? (
        <div className="text-center py-12">
          <p className="text-red-400 mb-2">{error}</p>
          <button
            onClick={() => fetchNews(currentPage, sentimentFilter)}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded transition-colors"
          >
            Retry
          </button>
        </div>
      ) : (
        <>
          <div className="space-y-4 mb-8">
            {news.map((article) => (
              <div key={article.id} className="bg-[#1E293B] rounded-lg p-6 border border-gray-700/50 hover:border-gray-600 transition-all">
                <div className="flex items-start justify-between mb-4">
                  <h3 className="text-white text-lg font-semibold leading-tight flex-1 mr-4">
                    {article.title || 'No title available'}
                  </h3>
                  <div className="flex items-center gap-2 text-sm text-white">
                    <Calendar className="w-4 h-4" />
                    <span className="text-white">{formatDate(article.published_at)}</span>
                  </div>
                </div>

                <p className="text-white mb-4 leading-relaxed line-clamp-3">
                  {article.content || 'No content available'}
                </p>

                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <span className="text-sm text-[#D1D5DB]">
                      <span className="text-[#9CA3AF]">Source:</span> <span className="text-white">{article.source || 'Unknown'}</span>
                    </span>
                    {article.stock_name && (
                      <span className="text-sm bg-blue-500/20 text-blue-400 px-2 py-1 rounded">
                        {article.stock_name}
                      </span>
                    )}
                  </div>

                  <div className="flex items-center gap-3">
                    {/* Always show sentiment badge */}
                    <div className="flex items-center gap-1 bg-[#0B1120] px-2 py-1 rounded border border-gray-800">
                      {getSentimentIcon(article.sentiment, article.impact_score || 50)}
                      <span className="text-sm text-white">
                        {article.impact_score ? `${Math.round(article.impact_score)}%` : (article.sentiment || 'Neutral')}
                      </span>
                    </div>

                    {article.url && article.url !== '#' && (
                      <a
                        href={article.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-400 hover:text-blue-300 transition-colors"
                      >
                        <ExternalLink className="w-4 h-4" />
                      </a>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Pagination Controls */}
          {totalPages > 1 && (
            <div className="flex justify-center items-center gap-4 py-4">
              <button
                onClick={() => handlePageChange(currentPage - 1)}
                disabled={currentPage === 1}
                className="p-2 bg-[#1E293B] border border-gray-700 rounded-lg text-white hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                <ChevronLeft className="w-5 h-5" />
              </button>

              <div className="flex items-center gap-2">
                {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                  let p = currentPage - 2 + i;
                  if (currentPage < 3) p = i + 1;
                  if (currentPage > totalPages - 2) p = totalPages - 4 + i;
                  if (p < 1 || p > totalPages) return null;

                  return (
                    <button
                      key={p}
                      onClick={() => handlePageChange(p)}
                      className={`w-8 h-8 rounded-lg flex items-center justify-center text-sm transition-colors ${p === currentPage
                        ? "bg-blue-600 text-white font-bold"
                        : "bg-[#1E293B] border border-gray-700 text-gray-300 hover:bg-gray-700"
                        }`}
                    >
                      {p}
                    </button>
                  );
                })}
              </div>

              <button
                onClick={() => handlePageChange(currentPage + 1)}
                disabled={currentPage === totalPages}
                className="p-2 bg-[#1E293B] border border-gray-700 rounded-lg text-white hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                <ChevronRight className="w-5 h-5" />
              </button>
            </div>
          )}
        </>
      )}

      {news.length === 0 && !loading && !error && (
        <div className="text-center py-12">
          <div className="text-[#D1D5DB] mb-2">No news items found</div>
          <p className="text-sm text-[#9CA3AF]">Try adjusting your filters</p>
        </div>
      )}
    </div>
  );
}