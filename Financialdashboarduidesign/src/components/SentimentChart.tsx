import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";
import { useState } from "react";

const mockData = [
  { date: "Jan 1", price: 17.2, sentiment: 65 },
  { date: "Jan 8", price: 17.5, sentiment: 68 },
  { date: "Jan 15", price: 17.3, sentiment: 62 },
  { date: "Jan 22", price: 17.8, sentiment: 70 },
  { date: "Jan 29", price: 18.1, sentiment: 72 },
  { date: "Feb 5", price: 17.9, sentiment: 69 },
  { date: "Feb 12", price: 18.3, sentiment: 75 },
  { date: "Feb 19", price: 18.0, sentiment: 71 },
  { date: "Feb 26", price: 18.5, sentiment: 78 },
  { date: "Mar 4", price: 18.7, sentiment: 80 },
];

const timeRanges = ["1D", "1W", "1M", "3M", "1Y"];

export function SentimentChart() {
  const [selectedRange, setSelectedRange] = useState("1M");

  return (
    <div className="bg-[#111827] rounded-xl p-6 border border-gray-800">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-[#E5E7EB] text-xl">Sentiment & Stock Movement</h3>
        <div className="flex gap-2">
          {timeRanges.map((range) => (
            <button
              key={range}
              onClick={() => setSelectedRange(range)}
              className={`px-3 py-1.5 rounded-lg text-sm transition-colors ${
                selectedRange === range
                  ? "bg-[#3B82F6] text-white"
                  : "bg-[#0B1120] text-[#9CA3AF] hover:text-[#E5E7EB]"
              }`}
            >
              {range}
            </button>
          ))}
        </div>
      </div>

      <ResponsiveContainer width="100%" height={350}>
        <LineChart data={mockData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis dataKey="date" stroke="#9CA3AF" style={{ fontSize: "12px" }} />
          <YAxis yAxisId="left" stroke="#3B82F6" style={{ fontSize: "12px" }} />
          <YAxis yAxisId="right" orientation="right" stroke="#10B981" style={{ fontSize: "12px" }} />
          <Tooltip
            contentStyle={{
              backgroundColor: "#111827",
              border: "1px solid #374151",
              borderRadius: "8px",
              color: "#E5E7EB",
            }}
          />
          <Legend wrapperStyle={{ color: "#9CA3AF" }} />
          <Line
            yAxisId="left"
            type="monotone"
            dataKey="price"
            stroke="#3B82F6"
            strokeWidth={2}
            dot={{ fill: "#3B82F6", r: 4 }}
            name="Price ($)"
          />
          <Line
            yAxisId="right"
            type="monotone"
            dataKey="sentiment"
            stroke="#10B981"
            strokeWidth={2}
            dot={{ fill: "#10B981", r: 4 }}
            name="Sentiment Score"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
