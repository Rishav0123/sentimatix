import { TrendingUp, TrendingDown, ArrowUpDown } from "lucide-react";
import { useState } from "react";

export interface Stock {
  name: string;
  ticker: string;
  sector: string;
  index: string;
  country: string;
  price: string;
  change: number;
  volume: string;
  marketCap: string;
  sentiment: number;
  logo: string;
}

interface StockTableProps {
  stocks: Stock[];
  onStockClick: (ticker: string) => void;
}

type SortKey = "name" | "price" | "change" | "volume" | "marketCap" | "sentiment";
type SortOrder = "asc" | "desc";

export function StockTable({ stocks, onStockClick }: StockTableProps) {
  const [sortKey, setSortKey] = useState<SortKey>("sentiment");
  const [sortOrder, setSortOrder] = useState<SortOrder>("desc");

  const handleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortOrder(sortOrder === "asc" ? "desc" : "asc");
    } else {
      setSortKey(key);
      setSortOrder("desc");
    }
  };

  const sortedStocks = [...stocks].sort((a, b) => {
    let aValue: any = a[sortKey];
    let bValue: any = b[sortKey];

    // Convert string values to numbers for numeric columns
    if (sortKey === "price") {
      aValue = parseFloat(a.price.replace(/[^0-9.-]+/g, ""));
      bValue = parseFloat(b.price.replace(/[^0-9.-]+/g, ""));
    } else if (sortKey === "volume" || sortKey === "marketCap") {
      aValue = parseFloat(a[sortKey].replace(/[^0-9.-]+/g, ""));
      bValue = parseFloat(b[sortKey].replace(/[^0-9.-]+/g, ""));
    }

    if (sortOrder === "asc") {
      return aValue > bValue ? 1 : -1;
    } else {
      return aValue < bValue ? 1 : -1;
    }
  });

  const getSentimentColor = (sentiment: number) => {
    if (sentiment >= 30) return "text-[#10B981]";      // Positive: >= 30
    if (sentiment >= 10) return "text-[#3B82F6]";      // Moderate positive: 10-29
    if (sentiment >= -10) return "text-blue-400";      // Neutral: -10 to 9
    if (sentiment >= -30) return "text-yellow-500";    // Moderate negative: -30 to -11
    return "text-red-500";                             // Negative: < -30
  };

  const getSentimentBg = (sentiment: number) => {
    if (sentiment >= 30) return "bg-[#10B981]/10";     // Positive: >= 30
    if (sentiment >= 10) return "bg-[#3B82F6]/10";     // Moderate positive: 10-29
    if (sentiment >= -10) return "bg-blue-400/10";     // Neutral: -10 to 9
    if (sentiment >= -30) return "bg-yellow-500/10";   // Moderate negative: -30 to -11
    return "bg-red-500/10";                            // Negative: < -30
  };

  return (
    <div className="bg-[#111827] rounded-xl border border-gray-800 overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-gray-800">
              <th className="text-left p-4 text-[#9CA3AF] text-xs">
                <button
                  onClick={() => handleSort("name")}
                  className="flex items-center gap-1 hover:text-[#E5E7EB] transition-colors"
                >
                  Stock
                  <ArrowUpDown className="w-3 h-3" />
                </button>
              </th>
              <th className="text-left p-4 text-[#9CA3AF] text-xs">Sector</th>
              <th className="text-left p-4 text-[#9CA3AF] text-xs">Index</th>
              <th className="text-right p-4 text-[#9CA3AF] text-xs">
                <button
                  onClick={() => handleSort("price")}
                  className="flex items-center gap-1 ml-auto hover:text-[#E5E7EB] transition-colors"
                >
                  Price
                  <ArrowUpDown className="w-3 h-3" />
                </button>
              </th>
              <th className="text-right p-4 text-[#9CA3AF] text-xs">
                <button
                  onClick={() => handleSort("change")}
                  className="flex items-center gap-1 ml-auto hover:text-[#E5E7EB] transition-colors"
                >
                  Change
                  <ArrowUpDown className="w-3 h-3" />
                </button>
              </th>
              <th className="text-right p-4 text-[#9CA3AF] text-xs">
                <button
                  onClick={() => handleSort("volume")}
                  className="flex items-center gap-1 ml-auto hover:text-[#E5E7EB] transition-colors"
                >
                  Volume
                  <ArrowUpDown className="w-3 h-3" />
                </button>
              </th>
              <th className="text-right p-4 text-[#9CA3AF] text-xs">
                <button
                  onClick={() => handleSort("marketCap")}
                  className="flex items-center gap-1 ml-auto hover:text-[#E5E7EB] transition-colors"
                >
                  Market Cap
                  <ArrowUpDown className="w-3 h-3" />
                </button>
              </th>
              <th className="text-right p-4 text-[#9CA3AF] text-xs">
                <button
                  onClick={() => handleSort("sentiment")}
                  className="flex items-center gap-1 ml-auto hover:text-[#E5E7EB] transition-colors"
                >
                  Sentiment
                  <ArrowUpDown className="w-3 h-3" />
                </button>
              </th>
            </tr>
          </thead>
          <tbody>
            {sortedStocks.map((stock, index) => {
              const isPositive = stock.change >= 0;
              return (
                <tr
                  key={index}
                  onClick={() => onStockClick(stock.ticker)}
                  className="border-b border-gray-800 hover:bg-[#0B1120] transition-colors cursor-pointer group"
                >
                  <td className="p-4">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded bg-[#0B1120] border border-gray-800 flex items-center justify-center text-sm">
                        {stock.logo}
                      </div>
                      <div>
                        <p className="text-[#E5E7EB] group-hover:text-[#3B82F6] transition-colors">
                          {stock.name}
                        </p>
                        <p className="text-[#9CA3AF] text-xs">{stock.ticker}</p>
                      </div>
                    </div>
                  </td>
                  <td className="p-4">
                    <span className="text-[#9CA3AF] text-sm">{stock.sector}</span>
                  </td>
                  <td className="p-4">
                    <span className="text-[#9CA3AF] text-sm">{stock.index}</span>
                  </td>
                  <td className="p-4 text-right">
                    <span className="text-[#E5E7EB]">{stock.price}</span>
                  </td>
                  <td className="p-4 text-right">
                    <div
                      className={`inline-flex items-center gap-1 px-2 py-1 rounded ${
                        isPositive
                          ? "bg-[#10B981]/10 text-[#10B981]"
                          : "bg-red-500/10 text-red-500"
                      }`}
                    >
                      {isPositive ? (
                        <TrendingUp className="w-3 h-3" />
                      ) : (
                        <TrendingDown className="w-3 h-3" />
                      )}
                      <span className="text-sm">
                        {isPositive ? "+" : ""}
                        {stock.change.toFixed(2)}%
                      </span>
                    </div>
                  </td>
                  <td className="p-4 text-right">
                    <span className="text-[#9CA3AF] text-sm">{stock.volume}</span>
                  </td>
                  <td className="p-4 text-right">
                    <span className="text-[#E5E7EB]">{stock.marketCap}</span>
                  </td>
                  <td className="p-4 text-right">
                    <div
                      className={`inline-flex items-center gap-2 px-2 py-1 rounded ${getSentimentBg(
                        stock.sentiment
                      )}`}
                    >
                      <span className={`text-sm ${getSentimentColor(stock.sentiment)}`}>
                        {stock.sentiment > 0 ? '+' : ''}{Math.round(stock.sentiment)}
                      </span>
                      <div className="w-12 h-1.5 bg-gray-800 rounded-full overflow-hidden">
                        <div
                          className={`h-full ${
                            stock.sentiment >= 30
                              ? "bg-[#10B981]"
                              : stock.sentiment >= 10
                              ? "bg-[#3B82F6]"
                              : stock.sentiment >= -10
                              ? "bg-blue-400"
                              : stock.sentiment >= -30
                              ? "bg-yellow-500"
                              : "bg-red-500"
                          }`}
                          style={{ width: `${Math.max(0, (stock.sentiment + 100) / 2)}%` }}
                        />
                      </div>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {sortedStocks.length === 0 && (
        <div className="p-8 text-center text-[#9CA3AF]">
          No stocks found matching your filters
        </div>
      )}
    </div>
  );
}
