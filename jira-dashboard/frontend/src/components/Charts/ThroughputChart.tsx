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
  // When provided, chart renders one line per series for the chosen metric
  overlaySeries?: Array<{ name: string; data: ThroughputData[]; color?: string }>;
  overlayMetric?: keyof Pick<ThroughputData, 'created' | 'resolved'>;
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

const ThroughputChart: React.FC<ThroughputChartProps> = ({ data, showMovingAverage = false, maPeriod = 7, maSource = 'resolved', maType = 'EMA', overlaySeries = [], overlayMetric = 'resolved' }) => {
  // If overlay mode is active, we construct a merged dataset keyed by date
  const isOverlay = overlaySeries && overlaySeries.length > 0;

  const colorPalette = [
    '#3b82f6', // blue
    '#10b981', // green
    '#ef4444', // red
    '#f59e0b', // amber
    '#8b5cf6', // violet
    '#14b8a6', // teal
    '#ec4899', // pink
    '#22c55e', // emerald
  ];

  const overlayConfig = useMemo(() => {
    if (!isOverlay) return { merged: [], seriesKeys: [] as Array<{ key: string; name: string; color: string }> };
    // Collect union of all dates
    const dateSet = new Set<string>();
    overlaySeries.forEach((s) => (s.data || []).forEach((p) => dateSet.add(p.date)));
    const dates = Array.from(dateSet.values()).sort((a, b) => new Date(a).getTime() - new Date(b).getTime());

    // Assign fixed keys and colors per series
    const seriesKeys = overlaySeries.map((s, idx) => ({
      key: `s${idx}`,
      name: s.name,
      color: s.color || colorPalette[idx % colorPalette.length],
    }));

    // Build map from series index to its data by date
    const seriesDataMaps = overlaySeries.map((s) => {
      const m = new Map<string, ThroughputData>();
      (s.data || []).forEach((p) => m.set(p.date, p));
      return m;
    });

    const merged = dates.map((date) => {
      const row: any = { date };
      seriesDataMaps.forEach((m, idx) => {
        const p = m.get(date);
        const value = p ? (p as any)[overlayMetric] as number : 0;
        row[seriesKeys[idx].key] = value;
      });
      return row;
    });

    return { merged, seriesKeys };
  }, [isOverlay, overlaySeries, overlayMetric]);

  const maData = useMemo(() => {
    if (isOverlay) return data; // MA disabled in overlay mode
    if (!showMovingAverage) return data;
    const calc = maType === 'EMA' ? computeEMA : computeSMA;
    return calc(data || [], maPeriod, maSource);
  }, [data, isOverlay, showMovingAverage, maPeriod, maSource, maType]);

  return (
    <div className="bg-white rounded-lg shadow-md p-6 border border-gray-200">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Ticket Throughput</h3>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={isOverlay ? overlayConfig.merged : maData}>
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
              if (isOverlay) return [value, name as string];
              return [value, name === 'created' ? 'Created' : name === 'resolved' ? 'Resolved' : `${maType} (${maPeriod})`];
            }}
          />
          <Legend />
          {isOverlay ? (
            <>
              {overlayConfig.seriesKeys.map((s) => (
                <Line
                  key={s.key}
                  type="monotone"
                  dataKey={s.key}
                  stroke={s.color}
                  strokeWidth={2}
                  dot={false}
                  name={s.name}
                />
              ))}
            </>
          ) : (
            <>
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
            </>
          )}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

export default ThroughputChart;