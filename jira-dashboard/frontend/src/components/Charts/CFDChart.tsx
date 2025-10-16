import React from 'react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

interface CFDPoint {
  date: string;
  open: number;
  done: number;
}

interface CFDChartProps {
  data: CFDPoint[];
}

const CFDChart: React.FC<CFDChartProps> = ({ data }) => {
  return (
    <div className="bg-white rounded-lg shadow-md p-6 border border-gray-200">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Cumulative Flow Diagram</h3>
      <ResponsiveContainer width="100%" height={300}>
        <AreaChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis
            dataKey="date"
            tick={{ fontSize: 12 }}
            tickFormatter={(value) => new Date(value).toLocaleDateString()}
          />
          <YAxis tick={{ fontSize: 12 }} />
          <Tooltip
            labelFormatter={(value) => new Date(value).toLocaleDateString()}
            formatter={(value, name) => [value, name === 'open' ? 'Open (WIP)' : 'Done']}
          />
          <Legend />
          <Area type="monotone" dataKey="open" stackId="1" stroke="#f59e0b" fill="#f59e0b" fillOpacity={0.3} name="Open (WIP)" />
          <Area type="monotone" dataKey="done" stackId="1" stroke="#10b981" fill="#10b981" fillOpacity={0.3} name="Done" />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
};

export default CFDChart;
