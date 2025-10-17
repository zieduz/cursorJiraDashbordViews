import React, { useMemo, useState } from 'react';
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
  initialSmoothing?: 'EMA' | 'SMA';
  showControls?: boolean;
}

function computeEMA(points: ThroughputPoint[], period: number, key: 'created' | 'resolved') {
  if (!points || points.length === 0) return [] as Array<ThroughputPoint & { ma: number }>;
  const k = 2 / (period + 1);
  const sorted = [...points].sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
  const result: Array<ThroughputPoint & { ma: number }> = [];
  let prevEma = (sorted[0] as any)[key] as number;
  for (let i = 0; i < sorted.length; i++) {
    const v = (sorted[i] as any)[key] as number;
    const ema = i === 0 ? prevEma : (v * k) + prevEma * (1 - k);
    result.push({ ...sorted[i], ma: ema });
    prevEma = ema;
  }
  return result;
}

function computeSMA(points: ThroughputPoint[], period: number, key: 'created' | 'resolved') {
  if (!points || points.length === 0) return [] as Array<ThroughputPoint & { ma: number }>;
  const sorted = [...points].sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
  const result: Array<ThroughputPoint & { ma: number }> = [];
  let windowSum = 0;
  const values = sorted.map((p) => (p as any)[key] as number);
  for (let i = 0; i < sorted.length; i++) {
    windowSum += values[i];
    if (i >= period) {
      windowSum -= values[i - period];
    }
    const denom = Math.min(i + 1, period);
    result.push({ ...sorted[i], ma: windowSum / denom });
  }
  return result;
}

const EMAChart: React.FC<EMAChartProps> = ({ data, period = 7, sourceKey = 'resolved', initialSmoothing = 'EMA', showControls = true }) => {
  const [localPeriod, setLocalPeriod] = useState<number>(period);
  const [localSource, setLocalSource] = useState<'created' | 'resolved'>(sourceKey);
  const [smoothing, setSmoothing] = useState<'EMA' | 'SMA'>(initialSmoothing);

  const maData = useMemo(() => {
    if (smoothing === 'EMA') return computeEMA(data || [], localPeriod, localSource);
    return computeSMA(data || [], localPeriod, localSource);
  }, [data, localPeriod, localSource, smoothing]);

  const sourceLabel = localSource === 'resolved' ? 'Resolved' : 'Created';

  return (
    <div className="bg-white rounded-lg shadow-md p-6 border border-gray-200">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">{smoothing} of {sourceLabel} ({`P=${localPeriod}`})</h3>
        {showControls && (
          <div className="flex items-center gap-2">
            <label className="text-sm text-gray-600">Smoothing</label>
            <select
              value={smoothing}
              onChange={(e) => setSmoothing(e.target.value as 'EMA' | 'SMA')}
              className="px-2 py-1 border border-gray-300 rounded-md text-sm"
            >
              <option value="EMA">EMA</option>
              <option value="SMA">SMA</option>
            </select>
            <label className="text-sm text-gray-600">Period</label>
            <select
              value={localPeriod}
              onChange={(e) => setLocalPeriod(parseInt(e.target.value))}
              className="px-2 py-1 border border-gray-300 rounded-md text-sm"
            >
              <option value={7}>7</option>
              <option value={14}>14</option>
              <option value={30}>30</option>
              <option value={60}>60</option>
            </select>
            <label className="text-sm text-gray-600">Source</label>
            <select
              value={localSource}
              onChange={(e) => setLocalSource(e.target.value as 'created' | 'resolved')}
              className="px-2 py-1 border border-gray-300 rounded-md text-sm"
            >
              <option value="resolved">Resolved</option>
              <option value="created">Created</option>
            </select>
          </div>
        )}
      </div>
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
            formatter={(value, name) => {
              if (name === 'ma') return [Number(value).toFixed(2), `${smoothing} (${localPeriod})`];
              return [value, sourceLabel];
            }}
          />
          <Legend />
          <Line
            type="monotone"
            dataKey={localSource}
            stroke={localSource === 'resolved' ? '#10b981' : '#3b82f6'}
            strokeWidth={2}
            name={sourceLabel}
          />
          <Line
            type="monotone"
            dataKey="ma"
            stroke="#7c3aed"
            strokeWidth={3}
            dot={false}
            name={`${smoothing} (${localPeriod})`}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

export default EMAChart;
