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
  ReferenceLine,
} from 'recharts';

interface ThroughputPoint {
  date: string;
  created: number;
  resolved: number;
}

type Mode = 'burnup' | 'burndown';

interface BurnChartProps {
  data: ThroughputPoint[]; // throughput over time
  mode?: Mode; // default 'burnup'
  title?: string;
  // Optionally specify total scope; if omitted, inferred from max cumulative created
  totalScope?: number;
}

function buildSeries(points: ThroughputPoint[]) {
  const sorted = [...(points || [])].sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
  let cumCreated = 0;
  let cumResolved = 0;
  return sorted.map((p) => {
    cumCreated += p.created || 0;
    cumResolved += p.resolved || 0;
    return {
      date: p.date,
      created: p.created,
      resolved: p.resolved,
      cumCreated,
      cumResolved,
      remaining: Math.max(cumCreated - cumResolved, 0),
    };
  });
}

const BurnChart: React.FC<BurnChartProps> = ({ data, mode = 'burnup', title, totalScope }) => {
  const series = useMemo(() => buildSeries(data || []), [data]);
  const inferredScope = Math.max(...series.map((d) => d.cumCreated || 0), 0);
  const scope = totalScope ?? inferredScope;

  const chartTitle = title || (mode === 'burnup' ? 'Burn-Up Chart' : 'Burn-Down Chart');

  // Build ideal lines (linear) across the time range
  const idealData = useMemo(() => {
    if (!series.length) return [] as Array<any>;
    const n = series.length;
    const initialRemaining = Math.max(series[0].cumCreated - series[0].cumResolved, 0);
    return series.map((d, i) => {
      const idealUp = (scope * i) / Math.max(n - 1, 1);
      const idealDown = initialRemaining - (initialRemaining * i) / Math.max(n - 1, 1);
      return { ...d, idealUp, idealDown: Math.max(idealDown, 0) };
    });
  }, [series, scope]);

  return (
    <div className="bg-white rounded-lg shadow-md p-6 border border-gray-200">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">{chartTitle}</h3>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={idealData.length ? idealData : series}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis
            dataKey="date"
            tick={{ fontSize: 12 }}
            tickFormatter={(value) => new Date(value).toLocaleDateString()}
          />
          <YAxis tick={{ fontSize: 12 }} />
          <Tooltip
            labelFormatter={(value) => new Date(value).toLocaleDateString()}
          />
          <Legend />

          {mode === 'burnup' ? (
            <>
              <Line type="monotone" dataKey="cumResolved" stroke="#10b981" strokeWidth={3} name="Completed" dot={false} />
              <Line type="monotone" dataKey="idealUp" stroke="#6b7280" strokeDasharray="5 5" strokeWidth={2} dot={false} name="Ideal" />
              <ReferenceLine y={scope} stroke="#6b7280" strokeDasharray="4 4" label={{ value: 'Total Scope', position: 'right', fill: '#6b7280', fontSize: 12 }} />
              <Line type="monotone" dataKey="cumCreated" stroke="#3b82f6" strokeWidth={2} name="Scope (cumulative)" dot={false} />
            </>
          ) : (
            <>
              <Line type="monotone" dataKey="remaining" stroke="#ef4444" strokeWidth={3} name="Remaining" dot={false} />
              <Line type="monotone" dataKey="idealDown" stroke="#6b7280" strokeDasharray="5 5" strokeWidth={2} dot={false} name="Ideal" />
              <ReferenceLine y={0} stroke="#6b7280" strokeDasharray="4 4" label={{ value: 'Done', position: 'right', fill: '#6b7280', fontSize: 12 }} />
            </>
          )}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

export default BurnChart;
