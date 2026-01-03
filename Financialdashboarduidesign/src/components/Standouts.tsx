import { useState, useEffect } from "react";
import { StandoutCard } from "./StandoutCard";

interface StandoutsProps {
  onStockClick: (ticker: string) => void;
}

interface StandoutStock {
  name: string;
  ticker: string;
  exchange: string;
  price: string;
  change: number;
  changeValue: string;
  logo: string;
  volume: string;
  marketCap: string;
  peRatio: string;
  dividendYield: string;
  chartData: number[];
  description: string;
}

export function Standouts({ onStockClick }: StandoutsProps) {
  const [standoutStocks, setStandoutStocks] = useState<StandoutStock[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchStandouts = async () => {
      try {
        setLoading(true);
        console.log('📈 Fetching standouts from API...');
        
        const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
        const response = await fetch(`${API_BASE_URL}/api/standouts?limit=4`);
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('✅ Standouts data received:', data);
        setStandoutStocks(data);
        setError(null);
      } catch (err) {
        console.error('❌ Error fetching standout stocks:', err);
        setError('Failed to load standout stocks');
        
        // Fallback to mock data
        setStandoutStocks([
          {
            name: "Reliance Industries",
            ticker: "RELIANCE",
            exchange: "NSE",
            price: "₹1,556.20",
            change: 2.46,
            changeValue: "+2.46%",
            logo: "🏭",
            volume: "5.8M",
            marketCap: "₹10.5T",
            peRatio: "25.4",
            dividendYield: "0.35%",
            chartData: [1500, 1520, 1510, 1530, 1540, 1535, 1545, 1550, 1548, 1552, 1556, 1556],
            description: "Reliance Industries gained 2.46% today driven by strong quarterly results and positive outlook for its digital and retail businesses."
          }
        ]);
      } finally {
        setLoading(false);
      }
    };

    fetchStandouts();
  }, []);

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h3 className="text-[#E5E7EB] text-xl">Standouts</h3>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="bg-[#1F2937] rounded-lg p-4 animate-pulse">
              <div className="h-4 bg-gray-600 rounded mb-2"></div>
              <div className="h-6 bg-gray-600 rounded mb-2"></div>
              <div className="h-3 bg-gray-600 rounded"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-[#E5E7EB] text-xl">Standouts</h3>
        {error && (
          <span className="text-red-400 text-sm">Using fallback data</span>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {standoutStocks.map((stock) => (
          <StandoutCard
            key={stock.ticker}
            {...stock}
            onClick={() => onStockClick(stock.ticker)}
          />
        ))}
      </div>
    </div>
  );
}
