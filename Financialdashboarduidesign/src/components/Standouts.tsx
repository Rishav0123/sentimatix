import { StandoutCard } from "./StandoutCard";

interface StandoutsProps {
  onStockClick: (ticker: string) => void;
}

const standoutStocks = [
  {
    name: "Navin Fluorine International Limited",
    ticker: "NAVINFLUOR",
    exchange: "BSE",
    price: "₹5,696.68",
    change: 14.48,
    changeValue: "+14.48%",
    logo: "🔷",
    volume: "298.69K",
    marketCap: "289.75B",
    peRatio: "85.63",
    dividendYield: "0.23%",
    chartData: [
      5200, 5150, 5100, 5050, 5000, 4950, 4900, 4950, 5000, 5100, 5200, 5300, 5400, 5500, 5600,
      5650, 5680, 5696,
    ],
    description:
      "Navin Fluorine shares surged sharply today after the company reported a stellar quarterly result with net profit soaring 192%, announced an interim dividend, and said multiple ongoing with increased capacity targets.",
  },
  {
    name: "TD Power Systems Limited",
    ticker: "TDPOWERSYS",
    exchange: "BSE",
    price: "₹774.68",
    change: 12.95,
    changeValue: "+12.95%",
    logo: "⚡",
    volume: "540.1K",
    marketCap: "120.98B",
    peRatio: "21.4",
    dividendYield: "0.86%",
    chartData: [
      700, 695, 690, 685, 680, 675, 670, 680, 690, 700, 710, 720, 730, 740, 750, 760, 770, 774,
    ],
    description:
      "TD Power Systems shares surged significantly today after announcing a sharp 48% jump in Q2 profit driven by robust revenue and export growth, alongside a declared dividend, amid boosted investor sentiment.",
  },
  {
    name: "Bandhan Bank Limited",
    ticker: "BANDHANBNK",
    exchange: "BSE",
    price: "₹156.55",
    change: -8.18,
    changeValue: "-8.18%",
    logo: "🏦",
    volume: "4.89M",
    marketCap: "252.2B",
    peRatio: "20.54",
    dividendYield: "0.00%",
    chartData: [
      180, 178, 176, 174, 172, 170, 168, 166, 164, 162, 160, 158, 156, 157, 158, 157, 156, 156,
    ],
    description:
      "Bandhan Bank's stock plummeted sharply today after the company reported disappointing Q2 financial results, including a significant drop in net profit and weaker performance compared to peers, which led to widespread selling interest among investors.",
  },
  {
    name: "Chennai Petroleum Corporation Limited",
    ticker: "CHENNPETRO",
    exchange: "BSE",
    price: "₹988.85",
    change: 18.8,
    changeValue: "+18.8%",
    logo: "🛢️",
    volume: "2.63M",
    marketCap: "145.54B",
    peRatio: "12.45",
    dividendYield: "0.51%",
    chartData: [
      820, 825, 830, 835, 840, 845, 850, 860, 870, 880, 900, 920, 940, 960, 970, 980, 985, 988,
    ],
    description:
      "Chennai Petroleum Corporation shares rallied significantly today after the company announced strong quarterly earnings with improved refining margins and higher throughput, boosting investor confidence in the oil refining sector.",
  },
];

export function Standouts({ onStockClick }: StandoutsProps) {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-[#E5E7EB] text-xl">Standouts</h3>
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
