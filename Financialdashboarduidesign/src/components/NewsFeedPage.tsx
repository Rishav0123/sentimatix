import { useState, useEffect } from "react";
import { Search, TrendingUp, TrendingDown, Filter, Calendar, RefreshCw, ChevronLeft, ChevronRight } from "lucide-react";
import { SentimentHeatmap } from "./SentimentHeatmap";
import { TopMovers } from "./TopMovers";

interface NewsItem {
  id: string;
  title: string;
  summary: string;
  source: string;
  time: string;
  ticker: string;
  stockName: string;
  sentiment: number;
  category: string;
  image?: string;
}

// API Response interface for your FastAPI backend
interface APINewsResponse {
  id: string;
  title: string;
  content?: string | null;
  url?: string | null;
  source: string;
  stock_symbol?: string;  // Some items have this
  yfin_symbol?: string;   // Some items have this instead
  published_at: string;
  sentiment: string;
  impact_score?: number;  // Main sentiment score field
  sentiment_score?: number;  // Alternative sentiment score field
  stock_name?: string;  // Stock company name
  tags?: string[];  // News categories/tags
  scraped_at?: string;
  published_date?: string;
  summary?: string | null;
  entities?: any;
  country?: string;
  sector?: string;
  type?: string;
}

// API Meta interface for pagination
interface APIMetaResponse {
  found: number;
  returned: number;
  limit: number;
  page: number;
}

// Full API Response with pagination
interface APIPaginatedResponse {
  data: APINewsResponse[];
  meta: APIMetaResponse;
}

const newsData: NewsItem[] = [
  {
    id: "1",
    title: "Infosys Announces Major AI Partnership with Global Tech Giant",
    summary:
      "Infosys has entered into a strategic partnership to develop next-generation AI solutions for enterprise customers, expected to boost revenue by 15% in Q4.",
    source: "Economic Times",
    time: "2 hours ago",
    ticker: "INFY",
    stockName: "Infosys Limited",
    sentiment: 85,
    category: "Partnership",
  },
  {
    id: "2",
    title: "TCS Reports Record Quarterly Earnings, Beats Estimates",
    summary:
      "Tata Consultancy Services posted impressive Q3 results with net profit rising 14.5% YoY, driven by strong demand in BFSI and retail sectors.",
    source: "Bloomberg",
    time: "3 hours ago",
    ticker: "TCS",
    stockName: "Tata Consultancy Services",
    sentiment: 92,
    category: "Earnings",
  },
  {
    id: "3",
    title: "HDFC Bank Faces Regulatory Scrutiny Over Lending Practices",
    summary:
      "India's banking regulator has launched an investigation into HDFC Bank's lending practices, causing concerns among investors about potential penalties.",
    source: "Reuters",
    time: "5 hours ago",
    ticker: "HDFCBANK",
    stockName: "HDFC Bank",
    sentiment: 35,
    category: "Regulatory",
  },
  {
    id: "4",
    title: "Reliance Industries Unveils Green Energy Roadmap",
    summary:
      "Mukesh Ambani announced ambitious plans to invest $80 billion in renewable energy over the next decade, positioning RIL as a clean energy leader.",
    source: "Mint",
    time: "6 hours ago",
    ticker: "RELIANCE",
    stockName: "Reliance Industries",
    sentiment: 78,
    category: "Initiative",
  },
  {
    id: "5",
    title: "Wipro Loses Major Client Contract to Competitor",
    summary:
      "Wipro's largest banking client has decided not to renew their $200M annual contract, citing concerns over project delivery timelines and quality.",
    source: "Business Standard",
    time: "8 hours ago",
    ticker: "WIPRO",
    stockName: "Wipro Limited",
    sentiment: 28,
    category: "Contract",
  },
  {
    id: "6",
    title: "Asian Paints Launches Eco-Friendly Product Line",
    summary:
      "Asian Paints introduced a new range of zero-VOC paints targeting environmentally conscious consumers, expecting 20% market share growth.",
    source: "Hindu Business Line",
    time: "10 hours ago",
    ticker: "ASIANPAINT",
    stockName: "Asian Paints",
    sentiment: 72,
    category: "Product Launch",
  },
  {
    id: "7",
    title: "Mahindra Electric Vehicle Sales Surge 45% in October",
    summary:
      "Mahindra & Mahindra reported exceptional EV sales growth, driven by strong demand for the XUV400 model and expanding charging infrastructure.",
    source: "ET Auto",
    time: "12 hours ago",
    ticker: "M&M",
    stockName: "Mahindra & Mahindra",
    sentiment: 88,
    category: "Sales",
  },
  {
    id: "8",
    title: "ICICI Bank Raises Interest Rates on Fixed Deposits",
    summary:
      "Following RBI's monetary policy stance, ICICI Bank increased FD rates by 25 basis points across all tenures, attracting more depositors.",
    source: "MoneyControl",
    time: "14 hours ago",
    ticker: "ICICIBANK",
    stockName: "ICICI Bank",
    sentiment: 65,
    category: "Policy",
  },
];

interface NewsFeedPageProps {
  onStockSelect: (ticker: string) => void;
}

export function NewsFeedPage({ onStockSelect }: NewsFeedPageProps) {
  const [newsItems, setNewsItems] = useState<NewsItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedCategory, setSelectedCategory] = useState("All");
  const [selectedSentiment, setSelectedSentiment] = useState("All");
  const [searchQuery, setSearchQuery] = useState("");
  
  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalItems, setTotalItems] = useState(0);
  const [itemsPerPage] = useState(20); // 20 items per page for 5 pages = 100 total news

  // API configuration - Vite uses import.meta.env instead of process.env
  const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

  // Helper function to map sentiment string to number
  const mapSentimentToNumber = (sentiment: string): number => {
    switch (sentiment.toLowerCase()) {
      case 'positive': return 1;    // Positive: > 0
      case 'negative': return -1;   // Negative: < 0
      case 'neutral': 
      default: return 0;            // Neutral: = 0
    }
  };

  // Helper function to get relative time
  const getRelativeTime = (publishedAt: string): string => {
    const now = new Date();
    const published = new Date(publishedAt);
    const diffMs = now.getTime() - published.getTime();
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    
    if (diffHours < 1) return 'Just now';
    if (diffHours === 1) return '1 hour ago';
    if (diffHours < 24) return `${diffHours} hours ago`;
    
    const diffDays = Math.floor(diffHours / 24);
    if (diffDays === 1) return '1 day ago';
    return `${diffDays} days ago`;
  };

  // Function to fetch news from your FastAPI backend with pagination
  const fetchNewsFromAPI = async (page: number = currentPage) => {
    try {
      setLoading(true);
      setError(null);
      
      const url = `${API_BASE_URL}/api/news?page=${page}&limit=${itemsPerPage}`;
      console.log(`🚀 Fetching news from: ${url}`);
      
      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      console.log(`📰 News API Response Status: ${response.status} ${response.statusText}`);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status} - ${response.statusText}`);
      }

      const apiResponse: APIPaginatedResponse = await response.json();
      console.log('✅ News API Response received:', apiResponse);
      
      // Extract data and meta from paginated response
      const apiNews = apiResponse.data || [];
      const meta = apiResponse.meta;
      
      if (!Array.isArray(apiNews)) {
        throw new Error('API response data is not an array');
      }

      // Update pagination info - Limit to maximum 5 pages (100 news total)
      if (meta) {
        setTotalItems(meta.found);
        const calculatedPages = Math.ceil(meta.found / meta.limit);
        const maxPages = 5; // Limit to 5 pages maximum
        setTotalPages(Math.min(calculatedPages, maxPages));
        setCurrentPage(meta.page);
        console.log(`📊 Pagination: Page ${meta.page} of ${Math.min(calculatedPages, maxPages)} (showing max 100 items from ${meta.found} total)`);
      }

      // Debug: Log the first item structure to understand the API response
      if (apiNews.length > 0) {
        console.log('🔍 First API news item structure:', JSON.stringify(apiNews[0], null, 2));
      }

      // Transform API response to match your NewsItem interface
      const transformedNews: NewsItem[] = apiNews.map((apiNews: APINewsResponse, index: number) => {
        // Debug: Log the sentiment data for each news item
        console.log(`📊 News item ${index + 1} sentiment data:`, {
          impact_score: apiNews.impact_score,
          sentiment_score: apiNews.sentiment_score,
          sentiment_string: apiNews.sentiment,
          stock_symbol: apiNews.stock_symbol,
          yfin_symbol: apiNews.yfin_symbol,
          stock_name: apiNews.stock_name,
          tags: apiNews.tags,
          sector: apiNews.sector,
          title: apiNews.title?.substring(0, 50) + '...'
        });

        // Determine final sentiment value with explicit priority:
        // 1. Use impact_score or sentiment_score if it exists (including 0)
        // 2. Map sentiment string to number
        // 3. Default to 60 only if nothing else is available
        let finalSentiment: number;
        
        const sentimentScore = apiNews.impact_score ?? apiNews.sentiment_score;
        
        if (typeof sentimentScore === 'number') {
          // Always use the actual impact_score from backend
          finalSentiment = sentimentScore;
          console.log(`✅ Using backend impact_score: ${finalSentiment}`);
        } else if (apiNews.sentiment) {
          // Fallback to sentiment string mapping only if no numeric score
          finalSentiment = mapSentimentToNumber(apiNews.sentiment);
          console.log(`📝 Mapped sentiment string '${apiNews.sentiment}' to: ${finalSentiment}`);
        } else {
          // Last resort default
          finalSentiment = 0;
          console.log(`⚠️ Using default sentiment: ${finalSentiment}`);
        }

        return {
          id: apiNews.id || index.toString(),
          title: apiNews.title,
          summary: apiNews.content || apiNews.summary || `News about ${apiNews.yfin_symbol || apiNews.stock_symbol}`,
          source: apiNews.source,
          time: getRelativeTime(apiNews.published_at),
          ticker: apiNews.yfin_symbol || apiNews.stock_symbol || 'N/A',
          stockName: apiNews.stock_name || getStockName(apiNews.yfin_symbol || apiNews.stock_symbol || ''),
          sentiment: finalSentiment,
          category: apiNews.tags?.join(', ') || apiNews.sector || getCategoryFromSentiment(apiNews.sentiment),
        };
      });

      setNewsItems(transformedNews);
      console.log(`✅ Successfully fetched ${transformedNews.length} news items from API`);
    } catch (err) {
      console.error('❌ Error fetching news from API:', err);
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch news data';
      setError(`News API Error: ${errorMessage}`);
      
      // Keep existing data on error instead of falling back to mock
      if (newsItems.length === 0) {
        console.log('🔄 Falling back to mock news data');
        setNewsItems(mockNewsData);
      }
    } finally {
      setLoading(false);
    }
  };

  // Fetch data on component mount and when page changes
  useEffect(() => {
    fetchNewsFromAPI(currentPage);
  }, [currentPage]);

  // Helper function to refresh current page data
  const handleRefresh = () => {
    fetchNewsFromAPI(currentPage);
  };

  // Pagination handlers
  const handlePageChange = (page: number) => {
    if (page >= 1 && page <= totalPages && page !== currentPage) {
      setCurrentPage(page);
      // Scroll to top when changing pages
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  };

  const handlePreviousPage = () => {
    if (currentPage > 1) {
      handlePageChange(currentPage - 1);
    }
  };

  const handleNextPage = () => {
    if (currentPage < totalPages) {
      handlePageChange(currentPage + 1);
    }
  };

  // Helper function to get stock name from ticker
  const getStockName = (ticker: string): string => {
    const nameMap: Record<string, string> = {
      'INFY': 'Infosys Limited',
      'TCS': 'Tata Consultancy Services',
      'HDFCBANK': 'HDFC Bank',
      'RELIANCE': 'Reliance Industries',
      'WIPRO': 'Wipro Limited',
      'ASIANPAINT': 'Asian Paints',
      'M&M': 'Mahindra & Mahindra',
      'ICICIBANK': 'ICICI Bank',
    };
    return nameMap[ticker] || ticker;
  };

  // Helper function to get category from sentiment
  const getCategoryFromSentiment = (sentiment: string): string => {
    switch (sentiment.toLowerCase()) {
      case 'positive': return 'Partnership';
      case 'negative': return 'Regulatory';
      default: return 'General';
    }
  };

  // Mock data as fallback
  const mockNewsData: NewsItem[] = [
    {
      id: "1",
      title: "Infosys Announces Major AI Partnership with Global Tech Giant",
      summary: "Infosys has entered into a strategic partnership to develop next-generation AI solutions for enterprise customers, expected to boost revenue by 15% in Q4.",
      source: "Economic Times",
      time: "2 hours ago",
      ticker: "INFY",
      stockName: "Infosys Limited",
      sentiment: 85,
      category: "Partnership",
    },
    // ... (keeping a few mock items for fallback)
  ];

  const categories = ["All", "Earnings", "Partnership", "Regulatory", "Product Launch", "Sales", "Policy", "Contract", "Initiative"];
  const sentiments = ["All", "Positive", "Neutral", "Negative"];

  const filteredNews = newsItems.filter((item: NewsItem) => {
    if (selectedCategory !== "All" && item.category !== selectedCategory) return false;
    if (selectedSentiment !== "All") {
      if (selectedSentiment === "Positive" && item.sentiment <= 0) return false;    // Positive: > 0
      if (selectedSentiment === "Neutral" && item.sentiment !== 0) return false;    // Neutral: = 0
      if (selectedSentiment === "Negative" && item.sentiment >= 0) return false;    // Negative: < 0
    }
    if (searchQuery && !item.title.toLowerCase().includes(searchQuery.toLowerCase()) && !item.ticker.toLowerCase().includes(searchQuery.toLowerCase())) {
      return false;
    }
    return true;
  });

  const getSentimentColor = (sentiment: number) => {
    if (sentiment > 0) return "text-[#10B981]";  // Positive: > 0
    if (sentiment === 0) return "text-blue-400"; // Neutral: = 0
    return "text-red-500";                       // Negative: < 0
  };

  const getSentimentBg = (sentiment: number) => {
    if (sentiment > 0) return "bg-[#10B981]/10 border-[#10B981]/20";  // Positive
    if (sentiment === 0) return "bg-blue-400/10 border-blue-400/20";  // Neutral
    return "bg-red-500/10 border-red-500/20";                        // Negative
  };

  const getSentimentLabel = (sentiment: number) => {
    if (sentiment > 0) return "Positive";   // Positive: > 0
    if (sentiment === 0) return "Neutral";  // Neutral: = 0  
    return "Negative";                      // Negative: < 0
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-[#E5E7EB] text-2xl mb-1">Market News & Sentiment</h2>
          <p className="text-[#9CA3AF] text-sm">
            Real-time news with AI-powered sentiment analysis
          </p>
        </div>
        <button
          onClick={handleRefresh}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2 bg-[#3B82F6] hover:bg-[#3B82F6]/80 disabled:bg-gray-600 text-white rounded-lg transition-colors text-sm"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-4">
          <p className="text-red-400 text-sm">⚠️ {error}</p>
          <p className="text-red-300/70 text-xs mt-1">
            {newsItems.length === 0 ? 'Showing mock data as fallback.' : 'Showing cached data.'}
          </p>
        </div>
      )}

      {/* Loading Indicator */}
      {loading && (
        <div className="bg-[#111827] rounded-xl p-8 border border-gray-800 text-center">
          <div className="flex items-center justify-center gap-3">
            <RefreshCw className="w-5 h-5 animate-spin text-[#3B82F6]" />
            <p className="text-[#9CA3AF]">Loading news data...</p>
          </div>
        </div>
      )}

      {/* Analytics Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <SentimentHeatmap />
        <TopMovers />
      </div>

      {/* Filters */}
      <div className="bg-[#111827] rounded-xl p-5 border border-gray-800">
        <div className="flex flex-col gap-4">
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#9CA3AF]" />
            <input
              type="text"
              placeholder="Search news by title or ticker..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-[#0B1120] border border-gray-800 rounded-lg pl-10 pr-4 py-2.5 text-[#E5E7EB] placeholder:text-[#9CA3AF] focus:outline-none focus:border-[#3B82F6] transition-colors text-sm"
            />
          </div>

          {/* Category & Sentiment Filters */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-[#9CA3AF] text-xs mb-2">Category</label>
              <div className="flex flex-wrap gap-2">
                {categories.map((cat) => (
                  <button
                    key={cat}
                    onClick={() => setSelectedCategory(cat)}
                    className={`px-3 py-1.5 rounded-lg text-xs transition-all ${
                      selectedCategory === cat
                        ? "bg-[#3B82F6] text-white"
                        : "bg-[#0B1120] text-[#9CA3AF] hover:text-[#E5E7EB] border border-gray-800"
                    }`}
                  >
                    {cat}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-[#9CA3AF] text-xs mb-2">Sentiment</label>
              <div className="flex gap-2">
                {sentiments.map((sent) => (
                  <button
                    key={sent}
                    onClick={() => setSelectedSentiment(sent)}
                    className={`px-4 py-1.5 rounded-lg text-xs transition-all ${
                      selectedSentiment === sent
                        ? "bg-[#3B82F6] text-white"
                        : "bg-[#0B1120] text-[#9CA3AF] hover:text-[#E5E7EB] border border-gray-800"
                    }`}
                  >
                    {sent}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Results Count */}
      <div className="flex items-center justify-between">
        <p className="text-[#9CA3AF] text-sm">
          Showing <span className="text-[#E5E7EB]">{filteredNews.length}</span> of{" "}
          <span className="text-[#E5E7EB]">{newsItems.length}</span> articles on this page
          {totalItems > 0 && (
            <span className="ml-2">
              (<span className="text-[#E5E7EB]">{totalItems.toLocaleString()}</span> total available)
            </span>
          )}
        </p>
      </div>

      {/* News Feed */}
      <div className="space-y-4">
        {filteredNews.map((item: NewsItem) => (
          <div
            key={item.id}
            className="bg-[#111827] rounded-xl p-5 border border-gray-800 hover:border-gray-700 transition-all group"
          >
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1">
                {/* Header */}
                <div className="flex items-start gap-3 mb-3">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <button
                        onClick={() => onStockSelect(item.ticker)}
                        className="text-[#3B82F6] hover:text-[#3B82F6]/80 transition-colors"
                      >
                        {item.ticker}
                      </button>
                      <span className="text-[#9CA3AF] text-xs">•</span>
                      <span className="text-[#9CA3AF] text-xs">{item.stockName}</span>
                      <span className="text-[#9CA3AF] text-xs">•</span>
                      <span className="text-[#9CA3AF] text-xs">{item.time}</span>
                    </div>
                    <h3 className="text-[#E5E7EB] text-lg mb-2 group-hover:text-[#3B82F6] transition-colors">
                      {item.title}
                    </h3>
                    <p className="text-[#9CA3AF] text-sm leading-relaxed mb-3">
                      {item.summary}
                    </p>
                  </div>
                </div>

                {/* Footer */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <span className="text-[#9CA3AF] text-xs">{item.source}</span>
                    <span className="px-2 py-1 bg-[#0B1120] border border-gray-800 rounded text-[#9CA3AF] text-xs">
                      {item.category}
                    </span>
                  </div>

                  {/* Sentiment Badge */}
                  <div
                    className={`flex items-center gap-2 px-3 py-1.5 rounded-lg border ${getSentimentBg(
                      item.sentiment
                    )}`}
                  >
                    {item.sentiment > 0 ? (
                      <TrendingUp className="w-4 h-4 text-[#10B981]" />
                    ) : item.sentiment === 0 ? (
                      <div className="w-4 h-4 flex items-center justify-center">
                        <div className="w-2 h-2 bg-blue-400 rounded-full" />
                      </div>
                    ) : (
                      <TrendingDown className="w-4 h-4 text-red-500" />
                    )}
                    <span className={`text-sm ${getSentimentColor(item.sentiment)}`}>
                      {getSentimentLabel(item.sentiment)}
                    </span>
                    <span className="text-[#9CA3AF] text-xs">•</span>
                    <span className={`${getSentimentColor(item.sentiment)}`}>
                      {item.sentiment}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {filteredNews.length === 0 && (
        <div className="bg-[#111827] rounded-xl p-12 border border-gray-800 text-center">
          <p className="text-[#9CA3AF]">No news articles match your filters</p>
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="bg-[#111827] rounded-xl p-6 border border-gray-800">
          <div className="flex items-center justify-between">
            {/* Pagination Info */}
            <div className="text-[#9CA3AF] text-sm">
              Showing page <span className="text-[#E5E7EB]">{currentPage}</span> of{" "}
              <span className="text-[#E5E7EB]">{totalPages}</span> (
              <span className="text-[#E5E7EB]">{Math.min(totalPages * itemsPerPage, totalItems)}</span> of <span className="text-[#E5E7EB]">{totalItems.toLocaleString()}</span> news items)
            </div>

            {/* Pagination Controls */}
            <div className="flex items-center gap-2">
              {/* Previous Button */}
              <button
                onClick={handlePreviousPage}
                disabled={currentPage === 1 || loading}
                className="flex items-center gap-2 px-3 py-2 bg-[#0B1120] border border-gray-800 rounded-lg text-[#9CA3AF] hover:text-[#E5E7EB] hover:border-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-sm"
              >
                <ChevronLeft className="w-4 h-4" />
                Previous
              </button>

              {/* Page Numbers */}
              <div className="flex items-center gap-1">
                {/* First page */}
                {currentPage > 3 && (
                  <>
                    <button
                      onClick={() => handlePageChange(1)}
                      className="px-3 py-2 bg-[#0B1120] border border-gray-800 rounded-lg text-[#9CA3AF] hover:text-[#E5E7EB] hover:border-gray-700 transition-colors text-sm"
                    >
                      1
                    </button>
                    {currentPage > 4 && (
                      <span className="text-[#9CA3AF] px-2">...</span>
                    )}
                  </>
                )}

                {/* Current page and neighbors */}
                {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                  let pageNum;
                  if (totalPages <= 5) {
                    pageNum = i + 1;
                  } else if (currentPage <= 3) {
                    pageNum = i + 1;
                  } else if (currentPage >= totalPages - 2) {
                    pageNum = totalPages - 4 + i;
                  } else {
                    pageNum = currentPage - 2 + i;
                  }

                  if (pageNum < 1 || pageNum > totalPages) return null;

                  return (
                    <button
                      key={pageNum}
                      onClick={() => handlePageChange(pageNum)}
                      disabled={loading}
                      className={`px-3 py-2 rounded-lg text-sm transition-colors ${
                        pageNum === currentPage
                          ? "bg-[#3B82F6] text-white"
                          : "bg-[#0B1120] border border-gray-800 text-[#9CA3AF] hover:text-[#E5E7EB] hover:border-gray-700"
                      } disabled:opacity-50 disabled:cursor-not-allowed`}
                    >
                      {pageNum}
                    </button>
                  );
                })}

                {/* Last page */}
                {currentPage < totalPages - 2 && totalPages > 5 && (
                  <>
                    {currentPage < totalPages - 3 && (
                      <span className="text-[#9CA3AF] px-2">...</span>
                    )}
                    <button
                      onClick={() => handlePageChange(totalPages)}
                      className="px-3 py-2 bg-[#0B1120] border border-gray-800 rounded-lg text-[#9CA3AF] hover:text-[#E5E7EB] hover:border-gray-700 transition-colors text-sm"
                    >
                      {totalPages}
                    </button>
                  </>
                )}
              </div>

              {/* Next Button */}
              <button
                onClick={handleNextPage}
                disabled={currentPage === totalPages || loading}
                className="flex items-center gap-2 px-3 py-2 bg-[#0B1120] border border-gray-800 rounded-lg text-[#9CA3AF] hover:text-[#E5E7EB] hover:border-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-sm"
              >
                Next
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
