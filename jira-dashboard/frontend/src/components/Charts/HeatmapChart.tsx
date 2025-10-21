import React from 'react';

interface HeatmapChartProps {
  data: number[][]; // 7 rows (Sun..Sat) x 24 cols
  normalized?: boolean;
}

// Lightweight CSS heatmap (avoids adding a new charting lib)
const HeatmapChart: React.FC<HeatmapChartProps> = ({ data, normalized = false }) => {
  const flat = data.flat();
  const max = Math.max(1, ...(normalized ? [1] : flat));
  const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

  return (
    <div className="w-full">
      <div className="grid" style={{ gridTemplateColumns: `80px repeat(24, minmax(18px, 1fr))` }}>
        <div></div>
        {Array.from({ length: 24 }, (_, hour) => (
          <div key={hour} className="text-[10px] text-gray-500 text-center">{hour}</div>
        ))}
        {data.map((row, day) => (
          <React.Fragment key={day}>
            <div className="text-xs text-gray-700 pr-2 flex items-center justify-end">{days[day]}</div>
            {row.map((value, hour) => {
              const ratio = normalized ? value : (max === 0 ? 0 : value / max);
              const bg = `rgba(37, 99, 235, ${Math.max(0.05, Math.min(1, ratio))})`;
              return (
                <div
                  key={`${day}-${hour}`}
                  title={`${days[day]} ${hour}:00 — ${normalized ? `${(value * 100).toFixed(1)}%` : `${value} events`}`}
                  className="h-5 border border-white/40"
                  style={{ backgroundColor: bg }}
                />
              );
            })}
          </React.Fragment>
        ))}
      </div>
    </div>
  );
};

export default HeatmapChart;
