import React from 'react';
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
}

const ThroughputChart: React.FC<ThroughputChartProps> = ({ data }) => {
  return (
    <div className="bg-white rounded-lg shadow-md p-6 border border-gray-200">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Ticket Throughput</h3>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis 
            dataKey="date" 
            tick={{ fontSize: 12 }}
            tickFormatter={(value) => new Date(value).toLocaleDateString()}
          />
          <YAxis tick={{ fontSize: 12 }} />
          <Tooltip 
            labelFormatter={(value) => new Date(value).toLocaleDateString()}
            formatter={(value, name) => [value, name === 'created' ? 'Created' : 'Resolved']}
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
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

export default ThroughputChart;