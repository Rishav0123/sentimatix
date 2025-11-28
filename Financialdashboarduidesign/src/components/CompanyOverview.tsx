import { InsightCard } from "./InsightCard";

export function CompanyOverview() {
  return (
    <div className="bg-[#111827] rounded-xl p-6 border border-gray-800">
      <div className="flex items-center gap-4 mb-6">
        <div className="w-16 h-16 bg-[#3B82F6]/20 rounded-xl flex items-center justify-center text-3xl">
          🏢
        </div>
        <div>
          <h2 className="text-[#E5E7EB] text-2xl">Infosys Ltd</h2>
          <p className="text-[#9CA3AF]">INFY • NYSE</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <InsightCard
          title="Current Price"
          value="$18.45"
          trend={[45, 52, 48, 55, 61, 58, 65, 70, 68, 72]}
        />
        <InsightCard
          title="Daily Change"
          value="$0.67"
          change={3.77}
        />
        <InsightCard
          title="Market Cap"
          value="$76.8B"
          subtitle="Billion USD"
        />
        <InsightCard
          title="Sentiment Score"
          value="78/100"
          change={5.2}
        />
      </div>
    </div>
  );
}
