import React, { useMemo } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';

interface ThroughputData {
  date: string;
  created: number;
  resolved: number;
}

interface ThroughputChartProps {
  data: ThroughputData[];
  showMovingAverage?: boolean;
  maPeriod?: number;
  maSource?: keyof Pick<ThroughputData, 'created' | 'resolved'>;
  maType?: 'EMA' | 'SMA';
}

function computeEMA(points: ThroughputData[], period: number, key: 'created' | 'resolved') {
  if (!points || points.length === 0) return [] as Array<ThroughputData & { ma: number }>;
  const k = 2 / (period + 1);
  const sorted = [...points].sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
  const result: Array<ThroughputData & { ma: number }> = [];
  let prev = (sorted[0] as any)[key] as number;
  for (let i = 0; i < sorted.length; i++) {
    const v = (sorted[i] as any)[key] as number;
    const ema = i === 0 ? prev : (v * k) + prev * (1 - k);
    result.push({ ...sorted[i], ma: ema });
    prev = ema;
  }
  return result;
}

function computeSMA(points: ThroughputData[], period: number, key: 'created' | 'resolved') {
  if (!points || points.length === 0) return [] as Array<ThroughputData & { ma: number }>;
  const sorted = [...points].sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
  const result: Array<ThroughputData & { ma: number }> = [];
  let windowSum = 0;
  const values = sorted.map((p) => (p as any)[key] as number);
  for (let i = 0; i < sorted.length; i++) {
    windowSum += values[i];
    if (i >= period) windowSum -= values[i - period];
    const denom = Math.min(i + 1, period);
    result.push({ ...sorted[i], ma: windowSum / denom });
  }
  return result;
}

const ThroughputChart: React.FC<ThroughputChartProps> = ({ data, showMovingAverage = false, maPeriod = 7, maSource = 'resolved', maType = 'EMA' }) => {
  const maData = useMemo(() => {
    if (!showMovingAverage) return data;
    const calc = maType === 'EMA' ? computeEMA : computeSMA;
    return calc(data || [], maPeriod, maSource);
  }, [data, showMovingAverage, maPeriod, maSource, maType]);
  return (
    <div className="bg-white rounded-lg shadow-md p-6 border border-gray-200">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Ticket Throughput</h3>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={maData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis 
            dataKey="date" 
            tick={{ fontSize: 12 }}
            tickFormatter={(value) => new Date(value).toLocaleDateString()}
          />
          <YAxis tick={{ fontSize: 12 }} />
          <Tooltip 
            labelFormatter={(value) => new Date(value).toLocaleDateString()}
            formatter={(value, name) => [value, name === 'created' ? 'Created' : name === 'resolved' ? 'Resolved' : `${maType} (${maPeriod})`]}
          />
          <Legend />
          <Line 
            type="monotone" 
            dataKey="created" 
            stroke="#3b82f6" 
            strokeWidth={2}
            name="Created"
          />
          <Line 
            type="monotone" 
            dataKey="resolved" 
            stroke="#10b981" 
            strokeWidth={2}
            name="Resolved"
          />
          {showMovingAverage && (
            <Line
              type="monotone"
              dataKey="ma"
              stroke="#7c3aed"
              strokeWidth={3}
              dot={false}
              name={`${maType} (${maPeriod})`}
            />
          )}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

export default ThroughputChart;