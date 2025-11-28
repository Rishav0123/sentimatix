import { Search, SlidersHorizontal, X } from "lucide-react";
import { useState } from "react";

interface FilterBarProps {
  onFilterChange: (filters: FilterState) => void;
}

export interface FilterState {
  search: string;
  sector: string;
  index: string;
  country: string;
  marketCap: string;
  sentiment: string;
}

const sectors = [
  "All Sectors",
  "Technology",
  "Finance",
  "Healthcare",
  "Energy",
  "Consumer",
  "Industrial",
  "Materials",
  "Utilities",
  "Real Estate",
  "Telecom",
];

const indices = [
  "All Indices",
  "NIFTY 50",
  "NIFTY 100",
  "NIFTY 500",
  "BSE Sensex",
  "Nifty Bank",
  "Nifty IT",
  "Nifty Pharma",
];

const countries = ["All Countries", "India", "United States", "United Kingdom", "Japan", "China"];

const marketCaps = ["All", "Large Cap", "Mid Cap", "Small Cap"];

const sentiments = ["All", "Positive", "Neutral", "Negative"];

export function FilterBar({ onFilterChange }: FilterBarProps) {
  const [filters, setFilters] = useState<FilterState>({
    search: "",
    sector: "All Sectors",
    index: "All Indices",
    country: "All Countries",
    marketCap: "All",
    sentiment: "All",
  });

  const [showAdvanced, setShowAdvanced] = useState(false);

  const updateFilter = (key: keyof FilterState, value: string) => {
    const newFilters = { ...filters, [key]: value };
    setFilters(newFilters);
    onFilterChange(newFilters);
  };

  const clearFilters = () => {
    const defaultFilters: FilterState = {
      search: "",
      sector: "All Sectors",
      index: "All Indices",
      country: "All Countries",
      marketCap: "All",
      sentiment: "All",
    };
    setFilters(defaultFilters);
    onFilterChange(defaultFilters);
  };

  const hasActiveFilters =
    filters.search ||
    filters.sector !== "All Sectors" ||
    filters.index !== "All Indices" ||
    filters.country !== "All Countries" ||
    filters.marketCap !== "All" ||
    filters.sentiment !== "All";

  return (
    <div className="bg-[#111827] rounded-xl p-6 border border-gray-800">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <h3 className="text-[#E5E7EB]">Stock Screener</h3>
          {hasActiveFilters && (
            <button
              onClick={clearFilters}
              className="flex items-center gap-1 text-xs text-[#9CA3AF] hover:text-[#E5E7EB] transition-colors"
            >
              <X className="w-3 h-3" />
              Clear all
            </button>
          )}
        </div>
        <button
          onClick={() => setShowAdvanced(!showAdvanced)}
          className="flex items-center gap-2 px-3 py-1.5 bg-[#0B1120] border border-gray-800 rounded-lg text-[#9CA3AF] hover:text-[#E5E7EB] hover:border-gray-700 transition-colors text-sm"
        >
          <SlidersHorizontal className="w-4 h-4" />
          {showAdvanced ? "Hide" : "Advanced"} Filters
        </button>
      </div>

      {/* Search */}
      <div className="mb-4">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#9CA3AF]" />
          <input
            type="text"
            placeholder="Search by stock name or ticker..."
            value={filters.search}
            onChange={(e) => updateFilter("search", e.target.value)}
            className="w-full bg-[#0B1120] border border-gray-800 rounded-lg pl-10 pr-4 py-2.5 text-[#E5E7EB] placeholder:text-[#9CA3AF] focus:outline-none focus:border-[#3B82F6] transition-colors text-sm"
          />
        </div>
      </div>

      {/* Basic Filters */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        <div>
          <label className="block text-[#9CA3AF] text-xs mb-1.5">Sector</label>
          <select
            value={filters.sector}
            onChange={(e) => updateFilter("sector", e.target.value)}
            className="w-full bg-[#0B1120] border border-gray-800 rounded-lg px-3 py-2 text-[#E5E7EB] text-sm focus:outline-none focus:border-[#3B82F6] transition-colors"
          >
            {sectors.map((sector) => (
              <option key={sector} value={sector}>
                {sector}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-[#9CA3AF] text-xs mb-1.5">Index</label>
          <select
            value={filters.index}
            onChange={(e) => updateFilter("index", e.target.value)}
            className="w-full bg-[#0B1120] border border-gray-800 rounded-lg px-3 py-2 text-[#E5E7EB] text-sm focus:outline-none focus:border-[#3B82F6] transition-colors"
          >
            {indices.map((index) => (
              <option key={index} value={index}>
                {index}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-[#9CA3AF] text-xs mb-1.5">Country</label>
          <select
            value={filters.country}
            onChange={(e) => updateFilter("country", e.target.value)}
            className="w-full bg-[#0B1120] border border-gray-800 rounded-lg px-3 py-2 text-[#E5E7EB] text-sm focus:outline-none focus:border-[#3B82F6] transition-colors"
          >
            {countries.map((country) => (
              <option key={country} value={country}>
                {country}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Advanced Filters */}
      {showAdvanced && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mt-4 pt-4 border-t border-gray-800">
          <div>
            <label className="block text-[#9CA3AF] text-xs mb-1.5">Market Cap</label>
            <select
              value={filters.marketCap}
              onChange={(e) => updateFilter("marketCap", e.target.value)}
              className="w-full bg-[#0B1120] border border-gray-800 rounded-lg px-3 py-2 text-[#E5E7EB] text-sm focus:outline-none focus:border-[#3B82F6] transition-colors"
            >
              {marketCaps.map((cap) => (
                <option key={cap} value={cap}>
                  {cap}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-[#9CA3AF] text-xs mb-1.5">Sentiment</label>
            <select
              value={filters.sentiment}
              onChange={(e) => updateFilter("sentiment", e.target.value)}
              className="w-full bg-[#0B1120] border border-gray-800 rounded-lg px-3 py-2 text-[#E5E7EB] text-sm focus:outline-none focus:border-[#3B82F6] transition-colors"
            >
              {sentiments.map((sentiment) => (
                <option key={sentiment} value={sentiment}>
                  {sentiment}
                </option>
              ))}
            </select>
          </div>
        </div>
      )}
    </div>
  );
}
