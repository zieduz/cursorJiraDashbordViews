import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer
} from 'recharts';

interface CommitsData {
  ticket_id: string;
  commit_count: number;
}

interface CommitsChartProps {
  data: CommitsData[];
}

const CommitsChart: React.FC<CommitsChartProps> = ({ data }) => {
  // Limit to top 20 tickets for better visualization
  const topTickets = data
    .sort((a, b) => b.commit_count - a.commit_count)
    .slice(0, 20);

  return (
    <div className="bg-white rounded-lg shadow-md p-6 border border-gray-200">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Commits per Issue (Top 20)</h3>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={topTickets}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis 
            dataKey="ticket_id" 
            tick={{ fontSize: 10 }}
            angle={-45}
            textAnchor="end"
            height={80}
          />
          <YAxis tick={{ fontSize: 12 }} />
          <Tooltip 
            formatter={(value) => [value, 'Commits']}
            labelFormatter={(value) => `Ticket: ${value}`}
          />
          <Bar 
            dataKey="commit_count" 
            fill="#8b5cf6"
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};

export default CommitsChart;