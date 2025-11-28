import { ArrowLeft } from "lucide-react";
import { CompanyOverview } from "./CompanyOverview";
import { SentimentChart } from "./SentimentChart";
import { NewsFeed } from "./NewsFeed";
import { SentimentHeatmap } from "./SentimentHeatmap";
import { TopMovers } from "./TopMovers";
import { FileText } from "lucide-react";

interface StockDetailProps {
  ticker: string;
  onBack: () => void;
}

export function StockDetail({ ticker, onBack }: StockDetailProps) {
  return (
    <div className="space-y-6">
      {/* Back Button */}
      <button
        onClick={onBack}
        className="flex items-center gap-2 text-[#9CA3AF] hover:text-[#E5E7EB] transition-colors"
      >
        <ArrowLeft className="w-5 h-5" />
        <span>Back to Market Overview</span>
      </button>

      {/* Company Overview Section */}
      <CompanyOverview />

      {/* Sentiment & Price Section */}
      <SentimentChart />

      {/* News Feed Section */}
      <NewsFeed />

      {/* Analytics Section */}
      <div className="space-y-6">
        {/* Sentiment Heatmap */}
        <SentimentHeatmap />

        {/* Top Movers */}
        <TopMovers />

        {/* Generate Report CTA */}
        <div className="bg-gradient-to-r from-[#3B82F6]/10 to-[#10B981]/10 rounded-xl p-8 border border-[#3B82F6]/20">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-[#E5E7EB] text-xl mb-2">
                AI-Powered Insights Report
              </h3>
              <p className="text-[#9CA3AF]">
                Get a comprehensive sentiment analysis report with actionable insights
                and market predictions powered by Stockify AI.
              </p>
            </div>
            <button className="flex items-center gap-2 bg-[#3B82F6] hover:bg-[#3B82F6]/90 text-white px-6 py-3 rounded-lg transition-all hover:scale-105">
              <FileText className="w-5 h-5" />
              Generate Report
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
