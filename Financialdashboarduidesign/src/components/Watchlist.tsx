import { Plus } from "lucide-react";

interface WatchlistStock {
  name: string;
  ticker: string;
  exchange: string;
  price: string;
  change: number;
  logo: string;
}

interface WatchlistProps {
  stocks: WatchlistStock[];
  onStockClick: (ticker: string) => void;
}

export function Watchlist({ stocks, onStockClick }: WatchlistProps) {
  return (
    <div className="bg-[#111827] rounded-xl p-4 border border-gray-800">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-[#E5E7EB]">Create Watchlist</h3>
        <button className="w-6 h-6 rounded bg-[#0B1120] border border-gray-800 hover:border-gray-700 flex items-center justify-center transition-colors">
          <Plus className="w-4 h-4 text-[#9CA3AF]" />
        </button>
      </div>

      <div className="space-y-2">
        {stocks.map((stock, index) => {
          const isPositive = stock.change >= 0;
          return (
            <div
              key={index}
              onClick={() => onStockClick(stock.ticker)}
              className="flex items-center justify-between p-3 rounded-lg hover:bg-[#0B1120] transition-colors cursor-pointer group"
            >
              <div className="flex items-center gap-3 flex-1">
                <div className="w-8 h-8 rounded bg-[#0B1120] border border-gray-800 flex items-center justify-center text-sm">
                  {stock.logo}
                </div>
                <div className="flex-1">
                  <p className="text-[#E5E7EB] text-sm">{stock.name}</p>
                  <p className="text-[#9CA3AF] text-xs">
                    {stock.ticker} · {stock.exchange}
                  </p>
                </div>
              </div>
              <div className="text-right">
                <p className="text-[#E5E7EB] text-sm">{stock.price}</p>
                <p
                  className={`text-xs ${
                    isPositive ? "text-[#10B981]" : "text-red-500"
                  }`}
                >
                  {isPositive ? "+" : ""}
                  {stock.change.toFixed(2)}%
                </p>
              </div>
              <button className="ml-3 w-6 h-6 rounded border border-gray-800 hover:border-gray-700 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                <Plus className="w-3 h-3 text-[#9CA3AF]" />
              </button>
            </div>
          );
        })}
      </div>

      {/* Gainers/Active Tabs */}
      <div className="mt-4 pt-4 border-t border-gray-800">
        <div className="flex gap-4 mb-3">
          <button className="text-[#E5E7EB] text-sm pb-1 border-b-2 border-[#3B82F6]">
            Gainers
          </button>
          <button className="text-[#9CA3AF] text-sm pb-1 hover:text-[#E5E7EB] transition-colors">
            Active
          </button>
        </div>

        <div className="space-y-2">
          <div className="flex items-center justify-between p-2 rounded hover:bg-[#0B1120] transition-colors cursor-pointer">
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 rounded bg-[#0B1120] flex items-center justify-center text-xs">
                🟢
              </div>
              <div>
                <p className="text-[#E5E7EB] text-sm">Mufin Green Finance</p>
                <p className="text-[#9CA3AF] text-xs">MUFIN · BSE</p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-[#E5E7EB] text-sm">₹118.16</p>
              <p className="text-[#10B981] text-xs">+19.74%</p>
            </div>
          </div>

          <div className="flex items-center justify-between p-2 rounded hover:bg-[#0B1120] transition-colors cursor-pointer">
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 rounded bg-[#0B1120] flex items-center justify-center text-xs">
                🔷
              </div>
              <div>
                <p className="text-[#E5E7EB] text-sm">Navin Fluorine</p>
                <p className="text-[#9CA3AF] text-xs">NAVINFLUOR · BSE</p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-[#E5E7EB] text-sm">₹5,696.6</p>
              <p className="text-[#10B981] text-xs">+14.48%</p>
            </div>
          </div>
        </div>
      </div>

      {/* Cryptocurrencies */}
      <div className="mt-4 pt-4 border-t border-gray-800">
        <h4 className="text-[#E5E7EB] text-sm mb-3">Popular Cryptocurrencies</h4>
        <div className="space-y-2">
          {[
            { name: "Bitcoin", ticker: "BTCUSD", price: "$109,911.05", change: 0.32, logo: "₿" },
            { name: "Ethereum", ticker: "ETHUSD", price: "$3,851.7", change: 0.15, logo: "Ξ" },
            { name: "Solana", ticker: "SOLUSD", price: "$186.21", change: -1.03, logo: "◎" },
            { name: "XRP", ticker: "XRPUSD", price: "$2.50", change: -0.45, logo: "✕" },
          ].map((crypto, index) => (
            <div
              key={index}
              className="flex items-center justify-between p-2 rounded hover:bg-[#0B1120] transition-colors cursor-pointer"
            >
              <div className="flex items-center gap-2">
                <div className="w-6 h-6 rounded bg-[#0B1120] flex items-center justify-center text-xs">
                  {crypto.logo}
                </div>
                <div>
                  <p className="text-[#E5E7EB] text-sm">{crypto.name}</p>
                  <p className="text-[#9CA3AF] text-xs">{crypto.ticker} · CRYPTO</p>
                </div>
              </div>
              <div className="text-right">
                <p className="text-[#E5E7EB] text-sm">{crypto.price}</p>
                <p
                  className={`text-xs ${
                    crypto.change >= 0 ? "text-[#10B981]" : "text-red-500"
                  }`}
                >
                  {crypto.change >= 0 ? "+" : ""}
                  {crypto.change.toFixed(2)}%
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
