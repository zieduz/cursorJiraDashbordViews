import React from 'react';
import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';

interface ControlPoint {
  jira_id: string;
  cycle_time_days?: number;
  lead_time_days?: number;
  resolved_at: string;
}

interface ControlChartProps {
  data: ControlPoint[];
  average_days: number;
  p85_days: number;
  p95_days: number;
  mode: 'cycle' | 'lead';
}

const ControlChart: React.FC<ControlChartProps> = ({ data, average_days, p85_days, p95_days, mode }) => {
  const yKey = mode === 'lead' ? 'lead_time_days' : 'cycle_time_days';
  const title = mode === 'lead' ? 'Control Chart (Lead Time)' : 'Control Chart (Cycle Time)';

  const formattedData = data.map((d) => ({
    ...d,
    date: d.resolved_at,
    value: d[yKey as keyof ControlPoint] as number | undefined,
  })).filter((d) => typeof d.value === 'number') as Array<{ jira_id: string; date: string; value: number }>;

  return (
    <div className="bg-white rounded-lg shadow-md p-6 border border-gray-200">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">{title}</h3>
      <ResponsiveContainer width="100%" height={300}>
        <ScatterChart>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis
            dataKey="date"
            name="Resolved"
            tickFormatter={(value) => new Date(value).toLocaleDateString()}
          />
          <YAxis dataKey="value" name="Days" />
          <Tooltip cursor={{ strokeDasharray: '3 3' }} formatter={(value: any) => [`${value} days`, 'Duration']} labelFormatter={(value) => new Date(value).toLocaleDateString()} />
          <Scatter data={formattedData} fill="#3b82f6" />
          {average_days > 0 && <ReferenceLine y={average_days} stroke="#9CA3AF" strokeDasharray="4 4" label={{ value: `Avg ${average_days.toFixed(1)}d`, position: 'right', fill: '#6b7280', fontSize: 12 }} />}
          {p85_days > 0 && <ReferenceLine y={p85_days} stroke="#f59e0b" strokeDasharray="4 4" label={{ value: `P85 ${p85_days.toFixed(1)}d`, position: 'right', fill: '#92400e', fontSize: 12 }} />}
          {p95_days > 0 && <ReferenceLine y={p95_days} stroke="#ef4444" strokeDasharray="4 4" label={{ value: `P95 ${p95_days.toFixed(1)}d`, position: 'right', fill: '#991b1b', fontSize: 12 }} />}
        </ScatterChart>
      </ResponsiveContainer>
    </div>
  );
};

export default ControlChart;
