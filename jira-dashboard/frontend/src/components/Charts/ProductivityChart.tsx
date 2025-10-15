import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';

interface ProductivityData {
  name: string;
  tickets_created: number;
  tickets_resolved: number;
}

interface ProductivityChartProps {
  data: ProductivityData[];
  title: string;
}

const ProductivityChart: React.FC<ProductivityChartProps> = ({ data, title }) => {
  return (
    <div className="bg-white rounded-lg shadow-md p-6 border border-gray-200">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">{title}</h3>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis 
            dataKey="name" 
            tick={{ fontSize: 12 }}
            angle={-45}
            textAnchor="end"
            height={80}
          />
          <YAxis tick={{ fontSize: 12 }} />
          <Tooltip />
          <Legend />
          <Bar 
            dataKey="tickets_created" 
            fill="#3b82f6" 
            name="Created"
          />
          <Bar 
            dataKey="tickets_resolved" 
            fill="#10b981" 
            name="Resolved"
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};

export default ProductivityChart;