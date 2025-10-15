import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Area,
  AreaChart
} from 'recharts';

interface VelocityData {
  date: string;
  velocity: number;
  lower?: number;
  upper?: number;
}

interface VelocityChartProps {
  data: VelocityData[];
  showConfidenceInterval?: boolean;
}

const VelocityChart: React.FC<VelocityChartProps> = ({ 
  data, 
  showConfidenceInterval = false 
}) => {
  return (
    <div className="bg-white rounded-lg shadow-md p-6 border border-gray-200">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Velocity Forecast</h3>
      <ResponsiveContainer width="100%" height={300}>
        {showConfidenceInterval && data[0]?.lower !== undefined ? (
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
              formatter={(value, name) => [
                value, 
                name === 'velocity' ? 'Predicted Velocity' : 
                name === 'upper' ? 'Upper Bound' : 'Lower Bound'
              ]}
            />
            <Legend />
            <Area
              type="monotone"
              dataKey="upper"
              stackId="1"
              stroke="#3b82f6"
              fill="#3b82f6"
              fillOpacity={0.1}
              name="Confidence Interval"
            />
            <Area
              type="monotone"
              dataKey="lower"
              stackId="1"
              stroke="#3b82f6"
              fill="#3b82f6"
              fillOpacity={0.1}
            />
            <Line 
              type="monotone" 
              dataKey="velocity" 
              stroke="#1d4ed8" 
              strokeWidth={3}
              name="Predicted Velocity"
            />
          </AreaChart>
        ) : (
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
              formatter={(value) => [value, 'Velocity']}
            />
            <Legend />
            <Line 
              type="monotone" 
              dataKey="velocity" 
              stroke="#1d4ed8" 
              strokeWidth={3}
              name="Predicted Velocity"
            />
          </LineChart>
        )}
      </ResponsiveContainer>
    </div>
  );
};

export default VelocityChart;