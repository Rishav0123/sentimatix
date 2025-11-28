import { useState } from "react";
import { TopNav } from "./components/TopNav";
import { Sidebar } from "./components/Sidebar";
import { MarketOverview } from "./components/MarketOverview";
import { StockDetail } from "./components/StockDetail";
import { AIChatPanel } from "./components/AIChatPanel";
import { InsightsDashboard } from "./components/InsightsDashboard";
import { NewsFeedPage } from "./components/NewsFeedPage";
import { ComparePage } from "./components/ComparePage";
import { APIAccessPage } from "./components/APIAccessPage";
import StockifyPerplexity from "./components/StockifyPerplexity";

export default function App() {
  const [isChatOpen, setIsChatOpen] = useState(false);
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

  // If AI view is selected, render Perplexity UI fullscreen
  if (activeView === "ai") {
    return <StockifyPerplexity />;
  }

  return (
    <div className="h-screen w-full bg-[#0B1120] flex flex-col dark">
      {/* Top Navigation */}
      <TopNav
        onAskStockify={() => setIsChatOpen(true)}
        selectedMarket={selectedMarket}
        onMarketChange={setSelectedMarket}
        showMarketSelector={!selectedStock}
      />

      {/* Main Layout */}
      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        <Sidebar activeView={activeView} onViewChange={handleViewChange} />

        {/* Main Content */}
        <main className="flex-1 overflow-y-auto">
          <div className="p-6 max-w-[1800px] mx-auto">
            {activeView === "stock-detail" && selectedStock ? (
              <StockDetail ticker={selectedStock} onBack={handleBackToOverview} />
            ) : activeView === "insights" ? (
              <InsightsDashboard onStockSelect={handleStockSelect} />
            ) : activeView === "news" ? (
              <NewsFeedPage onStockSelect={handleStockSelect} />
            ) : activeView === "compare" ? (
              <ComparePage onStockSelect={handleStockSelect} />
            ) : activeView === "api" ? (
              <APIAccessPage />
            ) : activeView === "dashboard" ? (
              <MarketOverview onStockSelect={handleStockSelect} />
            ) : (
              <div className="bg-[#111827] rounded-xl p-12 border border-gray-800 text-center">
                <h2 className="text-[#E5E7EB] text-2xl mb-2">Coming Soon</h2>
                <p className="text-[#9CA3AF]">
                  The {activeView} section is under development
                </p>
              </div>
            )}
          </div>
        </main>

        {/* AI Chat Panel */}
        <AIChatPanel isOpen={isChatOpen} onClose={() => setIsChatOpen(false)} />
      </div>
    </div>
  );
}
