import { useState } from "react";
import { StockSelector } from "./StockSelector";
import { ComparisonMetric } from "./ComparisonMetric";
import { TrendingUp, TrendingDown, BarChart3, Activity } from "lucide-react";

interface ComparePageProps {
  onStockSelect: (ticker: string) => void;
}

// Mock data for comparison
const stockData: Record<string, any> = {
  INFY: {
    logo: "🏢",
    name: "Infosys Limited",
    price: "₹1,482.30",
    priceNum: 1482.30,
    change: 3.45,
    volume: "8.2M",
    marketCap: "₹6.2T",
    sentiment: 78,
    sector: "Technology",
    pe: 28.5,
    eps: 52.0,
    dividendYield: 2.1,
    roe: 24.5,
    debtToEquity: 0.05,
    currentRatio: 2.8,
    rsi: 58,
    macd: "Bullish",
    sma50: "Above",
    sma200: "Above",
    recentDev: "Announced major AI partnership with global tech giant",
    earnings: "+14.5% YoY",
    revenue: "₹38,821 Cr",
  },
  TCS: {
    logo: "💼",
    name: "Tata Consultancy Services",
    price: "₹3,850.60",
    priceNum: 3850.60,
    change: 2.15,
    volume: "2.4M",
    marketCap: "₹14.1T",
    sentiment: 82,
    sector: "Technology",
    pe: 30.2,
    eps: 127.5,
    dividendYield: 1.8,
    roe: 42.3,
    debtToEquity: 0.02,
    currentRatio: 3.2,
    rsi: 62,
    macd: "Bullish",
    sma50: "Above",
    sma200: "Above",
    recentDev: "Record quarterly earnings beat estimates significantly",
    earnings: "+18.2% YoY",
    revenue: "₹60,583 Cr",
  },
  HDFCBANK: {
    logo: "🏦",
    name: "HDFC Bank",
    price: "₹1,645.20",
    priceNum: 1645.20,
    change: -1.23,
    volume: "12.5M",
    marketCap: "₹12.5T",
    sentiment: 65,
    sector: "Finance",
    pe: 18.4,
    eps: 89.4,
    dividendYield: 1.2,
    roe: 16.8,
    debtToEquity: 8.5,
    currentRatio: 0.9,
    rsi: 45,
    macd: "Bearish",
    sma50: "Below",
    sma200: "Above",
    recentDev: "Facing regulatory scrutiny over lending practices",
    earnings: "+8.4% YoY",
    revenue: "₹86,473 Cr",
  },
  RELIANCE: {
    logo: "⚡",
    name: "Reliance Industries",
    price: "₹2,456.75",
    priceNum: 2456.75,
    change: 1.87,
    volume: "9.8M",
    marketCap: "₹16.6T",
    sentiment: 72,
    sector: "Energy",
    pe: 24.8,
    eps: 99.1,
    dividendYield: 0.5,
    roe: 9.2,
    debtToEquity: 0.52,
    currentRatio: 1.1,
    rsi: 55,
    macd: "Neutral",
    sma50: "Above",
    sma200: "Above",
    recentDev: "Unveiled $80B green energy roadmap for next decade",
    earnings: "+12.1% YoY",
    revenue: "₹2,30,893 Cr",
  },
};

export function ComparePage({ onStockSelect }: ComparePageProps) {
  const [selectedStocks, setSelectedStocks] = useState<string[]>(["INFY", "TCS"]);

  const handleStockAdd = (ticker: string) => {
    if (selectedStocks.length < 4) {
      setSelectedStocks([...selectedStocks, ticker]);
    }
  };

  const handleStockRemove = (ticker: string) => {
    setSelectedStocks(selectedStocks.filter((t) => t !== ticker));
  };

  const comparedData = selectedStocks.map((ticker) => stockData[ticker] || {});
  const logos = comparedData.map((d) => d.logo || "📊");
  const tickers = selectedStocks;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-[#E5E7EB] text-2xl mb-1">Compare Stocks</h2>
        <p className="text-[#9CA3AF] text-sm">
          Side-by-side comparison of stock performance, fundamentals, and sentiment
        </p>
      </div>

      {/* Stock Selector */}
      <StockSelector
        selectedStocks={selectedStocks}
        onStockAdd={handleStockAdd}
        onStockRemove={handleStockRemove}
        maxStocks={4}
      />

      {selectedStocks.length === 0 && (
        <div className="bg-[#111827] rounded-xl p-12 border border-gray-800 text-center">
          <BarChart3 className="w-12 h-12 text-[#9CA3AF] mx-auto mb-4" />
          <h3 className="text-[#E5E7EB] text-xl mb-2">No Stocks Selected</h3>
          <p className="text-[#9CA3AF]">
            Add stocks above to start comparing metrics
          </p>
        </div>
      )}

      {selectedStocks.length > 0 && (
        <>
          {/* Stock Headers */}
          <div className="grid gap-4" style={{ gridTemplateColumns: `repeat(${selectedStocks.length}, 1fr)` }}>
            {comparedData.map((data, index) => (
              <div
                key={tickers[index]}
                onClick={() => onStockSelect(tickers[index])}
                className="bg-[#111827] rounded-xl p-5 border border-gray-800 hover:border-gray-700 transition-all cursor-pointer"
              >
                <div className="flex items-center gap-3 mb-3">
                  <span className="text-2xl">{data.logo}</span>
                  <div className="flex-1">
                    <h3 className="text-[#E5E7EB]">{tickers[index]}</h3>
                    <p className="text-[#9CA3AF] text-xs">{data.name}</p>
                  </div>
                </div>
                <div className="flex items-end justify-between mb-2">
                  <span className="text-[#E5E7EB] text-2xl">{data.price}</span>
                  <div
                    className={`flex items-center gap-1 px-2 py-1 rounded ${
                      data.change >= 0
                        ? "bg-[#10B981]/10 text-[#10B981]"
                        : "bg-red-500/10 text-red-500"
                    }`}
                  >
                    {data.change >= 0 ? (
                      <TrendingUp className="w-3 h-3" />
                    ) : (
                      <TrendingDown className="w-3 h-3" />
                    )}
                    <span className="text-sm">
                      {data.change >= 0 ? "+" : ""}
                      {data.change}%
                    </span>
                  </div>
                </div>
                <div className="flex items-center justify-between text-xs">
                  <span className="text-[#9CA3AF]">Vol: {data.volume}</span>
                  <span className="text-[#9CA3AF]">MCap: {data.marketCap}</span>
                </div>
              </div>
            ))}
          </div>

          {/* Price & Movement */}
          <div className="bg-[#111827] rounded-xl p-6 border border-gray-800">
            <h3 className="text-[#E5E7EB] mb-4 flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-[#3B82F6]" />
              Price & Movement
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <ComparisonMetric
                label="Current Price"
                values={comparedData.map((d) => d.price)}
                logos={logos}
                tickers={tickers}
              />
              <ComparisonMetric
                label="Change %"
                values={comparedData.map((d) => d.change)}
                logos={logos}
                tickers={tickers}
                type="change"
              />
              <ComparisonMetric
                label="Volume"
                values={comparedData.map((d) => d.volume)}
                logos={logos}
                tickers={tickers}
              />
              <ComparisonMetric
                label="Market Cap"
                values={comparedData.map((d) => d.marketCap)}
                logos={logos}
                tickers={tickers}
              />
            </div>
          </div>

          {/* Sentiment Summary */}
          <div className="bg-[#111827] rounded-xl p-6 border border-gray-800">
            <h3 className="text-[#E5E7EB] mb-4 flex items-center gap-2">
              <Activity className="w-5 h-5 text-[#10B981]" />
              Sentiment Summary
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <ComparisonMetric
                label="AI Sentiment Score"
                values={comparedData.map((d) => d.sentiment)}
                logos={logos}
                tickers={tickers}
                type="sentiment"
              />
              <ComparisonMetric
                label="Sentiment Strength"
                values={comparedData.map((d) => d.sentiment)}
                logos={logos}
                tickers={tickers}
                type="bar"
              />
            </div>
          </div>

          {/* Recent Developments */}
          <div className="bg-[#111827] rounded-xl p-6 border border-gray-800">
            <h3 className="text-[#E5E7EB] mb-4">Recent Developments</h3>
            <div className="grid gap-3">
              {comparedData.map((data, index) => (
                <div
                  key={tickers[index]}
                  className="bg-[#0B1120] rounded-lg p-4 border border-gray-800"
                >
                  <div className="flex items-start gap-3">
                    <span className="text-xl">{data.logo}</span>
                    <div className="flex-1">
                      <p className="text-[#3B82F6] text-sm mb-1">{tickers[index]}</p>
                      <p className="text-[#E5E7EB] text-sm">{data.recentDev}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Earnings */}
          <div className="bg-[#111827] rounded-xl p-6 border border-gray-800">
            <h3 className="text-[#E5E7EB] mb-4">Earnings Performance</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <ComparisonMetric
                label="Earnings Growth"
                values={comparedData.map((d) => d.earnings)}
                logos={logos}
                tickers={tickers}
              />
              <ComparisonMetric
                label="Revenue (Quarterly)"
                values={comparedData.map((d) => d.revenue)}
                logos={logos}
                tickers={tickers}
              />
            </div>
          </div>

          {/* Fundamental Indicators */}
          <div className="bg-[#111827] rounded-xl p-6 border border-gray-800">
            <h3 className="text-[#E5E7EB] mb-4">Fundamental Indicators</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <ComparisonMetric
                label="P/E Ratio"
                values={comparedData.map((d) => d.pe)}
                logos={logos}
                tickers={tickers}
              />
              <ComparisonMetric
                label="EPS"
                values={comparedData.map((d) => d.eps)}
                logos={logos}
                tickers={tickers}
              />
              <ComparisonMetric
                label="Dividend Yield %"
                values={comparedData.map((d) => d.dividendYield)}
                logos={logos}
                tickers={tickers}
              />
              <ComparisonMetric
                label="ROE %"
                values={comparedData.map((d) => d.roe)}
                logos={logos}
                tickers={tickers}
              />
              <ComparisonMetric
                label="Debt to Equity"
                values={comparedData.map((d) => d.debtToEquity)}
                logos={logos}
                tickers={tickers}
              />
              <ComparisonMetric
                label="Current Ratio"
                values={comparedData.map((d) => d.currentRatio)}
                logos={logos}
                tickers={tickers}
              />
            </div>
          </div>

          {/* Technical Indicators */}
          <div className="bg-[#111827] rounded-xl p-6 border border-gray-800">
            <h3 className="text-[#E5E7EB] mb-4">Technical Indicators</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <ComparisonMetric
                label="RSI"
                values={comparedData.map((d) => d.rsi)}
                logos={logos}
                tickers={tickers}
              />
              <ComparisonMetric
                label="MACD Signal"
                values={comparedData.map((d) => d.macd)}
                logos={logos}
                tickers={tickers}
              />
              <ComparisonMetric
                label="SMA 50"
                values={comparedData.map((d) => d.sma50)}
                logos={logos}
                tickers={tickers}
              />
              <ComparisonMetric
                label="SMA 200"
                values={comparedData.map((d) => d.sma200)}
                logos={logos}
                tickers={tickers}
              />
            </div>
          </div>
        </>
      )}
    </div>
  );
}
