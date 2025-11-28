interface ComparisonMetricProps {
  label: string;
  values: (string | number)[];
  logos: string[];
  tickers: string[];
  type?: "text" | "change" | "sentiment" | "bar";
}

export function ComparisonMetric({
  label,
  values,
  logos,
  tickers,
  type = "text",
}: ComparisonMetricProps) {
  const renderValue = (value: string | number, index: number) => {
    if (type === "change") {
      const numValue = typeof value === "string" ? parseFloat(value) : value;
      const isPositive = numValue >= 0;
      return (
        <span
          className={`${
            isPositive ? "text-[#10B981]" : "text-red-500"
          }`}
        >
          {isPositive ? "+" : ""}
          {numValue.toFixed(2)}%
        </span>
      );
    }

    if (type === "sentiment") {
      const numValue = typeof value === "string" ? parseFloat(value) : value;
      const color =
        numValue >= 70
          ? "text-[#10B981]"
          : numValue >= 50
          ? "text-blue-400"
          : "text-red-500";
      return <span className={color}>{numValue}</span>;
    }

    if (type === "bar") {
      const numValue = typeof value === "string" ? parseFloat(value) : value;
      const color =
        numValue >= 70
          ? "bg-[#10B981]"
          : numValue >= 50
          ? "bg-blue-400"
          : "bg-red-500";
      return (
        <div className="flex items-center gap-2">
          <div className="flex-1 h-2 bg-gray-800 rounded-full overflow-hidden">
            <div
              className={`h-full ${color} rounded-full`}
              style={{ width: `${numValue}%` }}
            />
          </div>
          <span className="text-[#9CA3AF] text-xs w-8">{numValue}</span>
        </div>
      );
    }

    return <span className="text-[#E5E7EB]">{value}</span>;
  };

  return (
    <div className="bg-[#0B1120] rounded-lg p-4 border border-gray-800">
      <p className="text-[#9CA3AF] text-xs mb-3">{label}</p>
      <div className="grid gap-3" style={{ gridTemplateColumns: `repeat(${values.length}, 1fr)` }}>
        {values.map((value, index) => (
          <div key={index} className="flex items-center gap-2">
            <span className="text-base">{logos[index]}</span>
            <div className="flex-1">{renderValue(value, index)}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
