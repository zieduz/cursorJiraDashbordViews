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
import { PAPUserProjectMetric } from '../../types';

interface PAPIndicatorsCommentsChartProps {
  data: PAPUserProjectMetric[];
}

const PAPIndicatorsCommentsChart: React.FC<PAPIndicatorsCommentsChartProps> = ({ data }) => {
  // Process data for grouped bar chart
  // Expected input: [{user, project, count}, ...]
  // Target format: [{user, ProjectA: count, ProjectB: count}, ...]
  
  const users = Array.from(new Set(data.map(d => d.user)));
  const projects = Array.from(new Set(data.map(d => d.project)));
  
  const chartData = users.map(user => {
    const userStats: any = { name: user };
    projects.forEach(project => {
      const match = data.find(d => d.user === user && d.project === project);
      userStats[project] = match ? match.count : 0;
    });
    return userStats;
  });

  const colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];

  return (
    <div className="bg-white rounded-lg shadow-md p-6 border border-gray-200">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Comments by User and Project</h3>
      <ResponsiveContainer width="100%" height={400}>
        <BarChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="name" />
          <YAxis />
          <Tooltip />
          <Legend />
          {projects.map((project, index) => (
            <Bar 
              key={project} 
              dataKey={project} 
              fill={colors[index % colors.length]} 
              stackId="a" 
            />
          ))}
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};

export default PAPIndicatorsCommentsChart;

