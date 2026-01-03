import { useState } from "react";
// Import components one by one to identify issues
import { TopNav } from "./components/TopNav";
import { Sidebar } from "./components/Sidebar";
import { MarketOverview } from "./components/MarketOverview";
import AISearchPage from "./components/AISearchPage";
import { NewsFeed } from "./components/NewsFeed";
import { Insights } from "./components/Insights";
import { Compare } from "./components/Compare";
import { Earnings } from "./components/Earnings";
import { Screener } from "./components/Screener";
import { APIAccess } from "./components/APIAccess";
import { Settings } from "./components/Settings";

export default function App() {
  const [selectedMarket, setSelectedMarket] = useState("India Markets");
  const [selectedStock, setSelectedStock] = useState<string | null>(null);
  const [activeView, setActiveView] = useState("dashboard");

  const handleStockSelect = (ticker: string) => {
    setSelectedStock(ticker);
    setActiveView("stock-detail");
  };

  const handleBackToOverview = () => {
    setSelectedStock(null);
    setActiveView("dashboard");
  };

  const handleViewChange = (view: string) => {
    setActiveView(view);
    setSelectedStock(null);
  };

  return (
    <div className="h-screen w-full bg-[#0B1120] flex flex-col dark">
      {/* Top Navigation */}
      <TopNav
        onAskStockify={() => setActiveView("ai")}
        selectedMarket={selectedMarket}
        onMarketChange={setSelectedMarket}
        showMarketSelector={true}
      />

      {/* Main Layout */}
      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        <Sidebar activeView={activeView} onViewChange={handleViewChange} />

        {/* Main Content */}
        <main className="flex-1 overflow-hidden">
          {activeView === "dashboard" ? (
            <div className="p-6 max-w-[1800px] mx-auto h-full overflow-y-auto">
              <MarketOverview onStockSelect={handleStockSelect} />
            </div>
          ) : activeView === "ai" ? (
            <AISearchPage />
          ) : activeView === "news" ? (
            <NewsFeed />
          ) : activeView === "insights" ? (
            <Insights />
          ) : activeView === "compare" ? (
            <Compare />
          ) : activeView === "earnings" ? (
            <Earnings />
          ) : activeView === "screener" ? (
            <Screener />
          ) : activeView === "api" ? (
            <APIAccess />
          ) : activeView === "settings" ? (
            <Settings />
          ) : (
            <div className="p-6 max-w-[1800px] mx-auto h-full overflow-y-auto">
              <div className="bg-[#111827] rounded-xl p-12 border border-gray-800 text-center">
                <h2 className="text-[#E5E7EB] text-2xl mb-2">Coming Soon</h2>
                <p className="text-[#9CA3AF]">
                  {activeView} feature is under development
                </p>
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
