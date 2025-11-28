import { MarketIndexCard } from "./MarketIndexCard";
import { MarketSummary } from "./MarketSummary";
import { Watchlist } from "./Watchlist";
import { RecentDevelopments } from "./RecentDevelopments";
import { Standouts } from "./Standouts";
import { SentimentHeatmapCompact } from "./SentimentHeatmapCompact";
import { TopMoversCompact } from "./TopMoversCompact";

interface MarketOverviewProps {
  onStockSelect: (ticker: string) => void;
}

const marketIndices = [
  {
    name: "NIFTY 50",
    ticker: "NSEI",
    exchange: "INDEX",
    value: "25,722.1",
    change: -0.6,
    changeValue: "-155.75",
    chartData: [95, 92, 88, 85, 82, 78, 75, 72, 70, 68, 65, 62, 60, 58, 55],
  },
  {
    name: "S&P BSE Sensex",
    ticker: "BSESN",
    exchange: "INDEX",
    value: "83,938.71",
    change: -0.55,
    changeValue: "-465.75",
    chartData: [92, 89, 85, 82, 78, 75, 72, 69, 66, 63, 60, 58, 55, 53, 50],
  },
  {
    name: "Nifty Bank Index",
    ticker: "NSEBANK",
    exchange: "INDEX",
    value: "57,776.35",
    change: -0.44,
    changeValue: "-254.35",
    chartData: [88, 85, 82, 79, 76, 73, 70, 67, 64, 61, 58, 55, 52, 50, 48],
  },
  {
    name: "Bitcoin",
    ticker: "BTCUSD",
    exchange: "CRYPTO",
    value: "$109,916.84",
    change: 0.33,
    changeValue: "+$361.57",
    chartData: [50, 52, 55, 58, 61, 64, 67, 70, 73, 76, 79, 82, 85, 88, 90],
  },
];

const watchlistStocks = [
  {
    name: "Tata Technologies",
    ticker: "TATATECH",
    exchange: "NSE",
    price: "₹692.25",
    change: -1.09,
    logo: "🔷",
  },
  {
    name: "ICICI Lombard General",
    ticker: "ICICIGI",
    exchange: "NSE",
    price: "₹1,993.7",
    change: -1.01,
    logo: "🏦",
  },
  {
    name: "Infosys Limited",
    ticker: "INFY",
    exchange: "NSE",
    price: "₹1,482.3",
    change: -0.77,
    logo: "🏢",
  },
  {
    name: "Reliance Industries",
    ticker: "RELIANCE",
    exchange: "BSE",
    price: "₹1,486.5",
    change: -0.13,
    logo: "⚡",
  },
];

export function MarketOverview({ onStockSelect }: MarketOverviewProps) {
  return (
    <div className="space-y-6">
      {/* Top Section: Market Indices + Watchlist */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Market Indices */}
        <div className="lg:col-span-2">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {marketIndices.map((index) => (
              <MarketIndexCard key={index.ticker} {...index} />
            ))}
          </div>
        </div>

        {/* Right: Watchlist */}
        <div className="lg:col-span-1">
          <Watchlist stocks={watchlistStocks} onStockClick={onStockSelect} />
        </div>
      </div>

      {/* Market Summary + Sentiment */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <MarketSummary />
        </div>
        <div className="lg:col-span-1 space-y-6">
          <SentimentHeatmapCompact />
          <TopMoversCompact onStockClick={onStockSelect} />
        </div>
      </div>

      {/* Recent Developments */}
      <RecentDevelopments />

      {/* Standouts */}
      <Standouts onStockClick={onStockSelect} />
    </div>
  );
}
