import React, { useMemo } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

interface ThroughputPoint {
  date: string;
  created: number;
  resolved: number;
}

interface EMAChartProps {
  data: ThroughputPoint[];
  period?: number; // smoothing period in points (default 7)
  sourceKey?: keyof Pick<ThroughputPoint, 'created' | 'resolved'>; // default 'resolved'
}

function computeEMA(points: ThroughputPoint[], period: number, key: 'created' | 'resolved') {
  if (!points || points.length === 0) return [] as Array<ThroughputPoint & { ema: number }>;
  const k = 2 / (period + 1);
  // Ensure data is sorted by date ascending
  const sorted = [...points].sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
  const result: Array<ThroughputPoint & { ema: number }> = [];
  let prevEma = (sorted[0] as any)[key] as number;
  for (let i = 0; i < sorted.length; i++) {
    const v = (sorted[i] as any)[key] as number;
    const ema = i === 0 ? prevEma : (v * k) + prevEma * (1 - k);
    result.push({ ...sorted[i], ema });
    prevEma = ema;
  }
  return result;
}

const EMAChart: React.FC<EMAChartProps> = ({ data, period = 7, sourceKey = 'resolved' }) => {
  const emaData = useMemo(() => computeEMA(data || [], period, sourceKey), [data, period, sourceKey]);

  const sourceLabel = sourceKey === 'resolved' ? 'Resolved' : 'Created';

  return (
    <div className="bg-white rounded-lg shadow-md p-6 border border-gray-200">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">EMA of {sourceLabel} ({`P=${period}`})</h3>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={emaData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis
            dataKey="date"
            tick={{ fontSize: 12 }}
            tickFormatter={(value) => new Date(value).toLocaleDateString()}
          />
          <YAxis tick={{ fontSize: 12 }} />
          <Tooltip
            labelFormatter={(value) => new Date(value).toLocaleDateString()}
            formatter={(value, name) => {
              if (name === 'ema') return [Number(value).toFixed(2), `EMA (${period})`];
              return [value, sourceLabel];
            }}
          />
          <Legend />
          <Line
            type="monotone"
            dataKey={sourceKey}
            stroke={sourceKey === 'resolved' ? '#10b981' : '#3b82f6'}
            strokeWidth={2}
            name={sourceLabel}
          />
          <Line
            type="monotone"
            dataKey="ema"
            stroke="#7c3aed"
            strokeWidth={3}
            dot={false}
            name={`EMA (${period})`}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

export default EMAChart;
