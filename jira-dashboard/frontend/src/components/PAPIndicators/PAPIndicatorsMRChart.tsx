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
import { PAPAuthorMetric } from '../../types';

interface PAPIndicatorsMRChartProps {
  data: PAPAuthorMetric[];
}

const PAPIndicatorsMRChart: React.FC<PAPIndicatorsMRChartProps> = ({ data }) => {
  // Sort by count descending
  const sortedData = [...data].sort((a, b) => b.count - a.count);

  return (
    <div className="bg-white rounded-lg shadow-md p-6 border border-gray-200">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Merge Requests Created by Author</h3>
      <ResponsiveContainer width="100%" height={Math.max(300, data.length * 40)}>
        <BarChart
          layout="vertical"
          data={sortedData}
          margin={{ top: 5, right: 30, left: 100, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis type="number" />
          <YAxis 
            type="category" 
            dataKey="author" 
            width={90}
            tick={{ fontSize: 12 }}
          />
          <Tooltip />
          <Bar dataKey="count" fill="#8b5cf6" name="MRs Created" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};

export default PAPIndicatorsMRChart;

