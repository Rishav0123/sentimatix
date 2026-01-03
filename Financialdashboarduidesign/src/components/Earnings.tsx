import { useState, useEffect } from "react";
import { Calendar, TrendingUp, TrendingDown, Clock, Building } from "lucide-react";

interface EarningsEvent {
  id: string;
  company: string;
  symbol: string;
  date: string;
  time: string;
  quarter: string;
  expectedEPS: number;
  actualEPS?: number;
  revenue?: string;
  status: 'upcoming' | 'reported' | 'today';
  surprise?: number;
}

export function Earnings() {
  const [earnings, setEarnings] = useState<EarningsEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedTab, setSelectedTab] = useState<'today' | 'upcoming' | 'past'>('today');

  useEffect(() => {
    // Simulate loading earnings data
    setTimeout(() => {
      const mockEarnings: EarningsEvent[] = [
        {
          id: "1",
          company: "Tata Consultancy Services",
          symbol: "TCS",
          date: "2026-01-01",
          time: "Post Market",
          quarter: "Q3 FY26",
          expectedEPS: 45.20,
          actualEPS: 47.80,
          revenue: "₹62,441 Cr",
          status: 'today',
          surprise: 5.75
        },
        {
          id: "2",
          company: "Infosys Limited",
          symbol: "INFY",
          date: "2026-01-01",
          time: "Pre Market",
          quarter: "Q3 FY26",
          expectedEPS: 18.50,
          status: 'today'
        },
        {
          id: "3",
          company: "Reliance Industries",
          symbol: "RELIANCE",
          date: "2026-01-02",
          time: "Post Market",
          quarter: "Q3 FY26",
          expectedEPS: 85.30,
          status: 'upcoming'
        },
        {
          id: "4",
          company: "HDFC Bank",
          symbol: "HDFCBANK",
          date: "2026-01-03",
          time: "Pre Market",
          quarter: "Q3 FY26",
          expectedEPS: 42.10,
          status: 'upcoming'
        },
        {
          id: "5",
          company: "ICICI Bank",
          symbol: "ICICIBANK",
          date: "2025-12-30",
          time: "Post Market",
          quarter: "Q3 FY26",
          expectedEPS: 38.20,
          actualEPS: 40.15,
          revenue: "₹45,230 Cr",
          status: 'reported',
          surprise: 5.11
        }
      ];
      
      setEarnings(mockEarnings);
      setLoading(false);
    }, 1000);
  }, []);

  const getFilteredEarnings = () => {
    switch (selectedTab) {
      case 'today':
        return earnings.filter(e => e.status === 'today');
      case 'upcoming':
        return earnings.filter(e => e.status === 'upcoming');
      case 'past':
        return earnings.filter(e => e.status === 'reported');
      default:
        return earnings;
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-IN', { 
      weekday: 'short', 
      month: 'short', 
      day: 'numeric' 
    });
  };

  const getSurpriseColor = (surprise?: number) => {
    if (!surprise) return 'text-gray-400';
    return surprise > 0 ? 'text-green-400' : 'text-red-400';
  };

  const getSurpriseIcon = (surprise?: number) => {
    if (!surprise) return null;
    return surprise > 0 ? 
      <TrendingUp className="w-4 h-4" /> : 
      <TrendingDown className="w-4 h-4" />;
  };

  if (loading) {
    return (
      <div className="p-6 max-w-[1800px] mx-auto h-full overflow-y-auto">
        <div className="mb-6">
          <h1 className="text-white text-2xl font-bold mb-2">Earnings Calendar</h1>
          <p className="text-gray-400">Track upcoming and recent earnings announcements</p>
        </div>
        
        <div className="space-y-4">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="bg-[#1E293B] rounded-lg p-6 animate-pulse">
              <div className="flex items-center justify-between mb-4">
                <div className="h-6 bg-gray-700 rounded w-1/3"></div>
                <div className="h-4 bg-gray-700 rounded w-20"></div>
              </div>
              <div className="grid grid-cols-4 gap-4">
                <div className="h-4 bg-gray-700 rounded"></div>
                <div className="h-4 bg-gray-700 rounded"></div>
                <div className="h-4 bg-gray-700 rounded"></div>
                <div className="h-4 bg-gray-700 rounded"></div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-[1800px] mx-auto h-full overflow-y-auto">
      <div className="mb-6">
        <h1 className="text-white text-2xl font-bold mb-2">Earnings Calendar</h1>
        <p className="text-gray-400">Track upcoming and recent earnings announcements</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 mb-6 bg-[#0F172A] p-1 rounded-lg w-fit">
        {[
          { key: 'today', label: 'Today', count: earnings.filter(e => e.status === 'today').length },
          { key: 'upcoming', label: 'Upcoming', count: earnings.filter(e => e.status === 'upcoming').length },
          { key: 'past', label: 'Past Results', count: earnings.filter(e => e.status === 'reported').length }
        ].map((tab) => (
          <button
            key={tab.key}
            onClick={() => setSelectedTab(tab.key as any)}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              selectedTab === tab.key
                ? 'bg-blue-600 text-white'
                : 'text-gray-400 hover:text-white hover:bg-[#1E293B]'
            }`}
          >
            {tab.label} ({tab.count})
          </button>
        ))}
      </div>

      {/* Earnings List */}
      <div className="space-y-4">
        {getFilteredEarnings().map((earning) => (
          <div key={earning.id} className="bg-[#1E293B] rounded-lg p-6 border border-gray-700/50 hover:border-gray-600 transition-all">
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-start gap-4">
                <div className="w-12 h-12 bg-blue-600 rounded-lg flex items-center justify-center">
                  <Building className="w-6 h-6 text-white" />
                </div>
                
                <div>
                  <h3 className="text-white text-lg font-semibold">{earning.company}</h3>
                  <div className="flex items-center gap-2 text-sm text-gray-400">
                    <span className="bg-blue-500/20 text-blue-400 px-2 py-1 rounded">
                      {earning.symbol}
                    </span>
                    <span>{earning.quarter}</span>
                  </div>
                </div>
              </div>

              <div className="text-right">
                <div className="flex items-center gap-1 text-gray-400 text-sm mb-1">
                  <Calendar className="w-4 h-4" />
                  {formatDate(earning.date)}
                </div>
                <div className="flex items-center gap-1 text-gray-400 text-sm">
                  <Clock className="w-4 h-4" />
                  {earning.time}
                </div>
              </div>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
              <div>
                <div className="text-gray-400 text-sm mb-1">Expected EPS</div>
                <div className="text-white font-semibold">₹{earning.expectedEPS.toFixed(2)}</div>
              </div>

              {earning.actualEPS && (
                <div>
                  <div className="text-gray-400 text-sm mb-1">Actual EPS</div>
                  <div className="text-white font-semibold">₹{earning.actualEPS.toFixed(2)}</div>
                </div>
              )}

              {earning.revenue && (
                <div>
                  <div className="text-gray-400 text-sm mb-1">Revenue</div>
                  <div className="text-white font-semibold">{earning.revenue}</div>
                </div>
              )}

              {earning.surprise && (
                <div>
                  <div className="text-gray-400 text-sm mb-1">Surprise</div>
                  <div className={`font-semibold flex items-center gap-1 ${getSurpriseColor(earning.surprise)}`}>
                    {getSurpriseIcon(earning.surprise)}
                    {earning.surprise > 0 ? '+' : ''}{earning.surprise.toFixed(2)}%
                  </div>
                </div>
              )}
            </div>

            {earning.status === 'today' && (
              <div className="mt-4 p-3 bg-yellow-500/10 border border-yellow-500/20 rounded-lg">
                <div className="text-yellow-400 text-sm font-medium">
                  📊 Earnings announcement scheduled for today
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {getFilteredEarnings().length === 0 && (
        <div className="text-center py-12">
          <div className="text-gray-400 mb-2">No earnings data for {selectedTab}</div>
          <div className="text-sm text-gray-500">Check other tabs for more information</div>
        </div>
      )}
    </div>
  );
}