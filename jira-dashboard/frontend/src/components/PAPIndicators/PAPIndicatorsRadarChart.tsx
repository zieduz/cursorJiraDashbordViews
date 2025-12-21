import React from 'react';
import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  Legend,
  Tooltip
} from 'recharts';
import { PAPIndicatorsMetrics } from '../../types';

interface PAPIndicatorsRadarChartProps {
  data: PAPIndicatorsMetrics;
}

const PAPIndicatorsRadarChart: React.FC<PAPIndicatorsRadarChartProps> = ({ data }) => {
  // Aggregate total metrics per user/author
  const userMetrics: any = {};

  // Comments
  data.comments_by_user_project.forEach(d => {
    if (!userMetrics[d.user]) userMetrics[d.user] = { name: d.user, comments: 0, status_changes: 0, mrs: 0 };
    userMetrics[d.user].comments += d.count;
  });

  // Status changes
  data.status_changes_by_user_project.forEach(d => {
    if (!userMetrics[d.user]) userMetrics[d.user] = { name: d.user, comments: 0, status_changes: 0, mrs: 0 };
    userMetrics[d.user].status_changes += d.count;
  });

  // MRs
  data.mrs_by_author.forEach(d => {
    // Note: author name might differ slightly from display_name if sync mapping is not exact
    if (!userMetrics[d.author]) userMetrics[d.author] = { name: d.author, comments: 0, status_changes: 0, mrs: 0 };
    userMetrics[d.author].mrs += d.count;
  });

  const chartData = Object.values(userMetrics);
  const users = chartData.map((d: any) => d.name);

  // Normalize data for radar (0 to 100 scale based on max in each category)
  const maxComments = Math.max(...chartData.map((d: any) => d.comments), 1);
  const maxStatus = Math.max(...chartData.map((d: any) => d.status_changes), 1);
  const maxMRs = Math.max(...chartData.map((d: any) => d.mrs), 1);

  // Reformat for RadarChart: one entry per metric, multiple data keys for users
  // Recharts RadarChart typically handles data as: [{subject: 'Comments', userA: 10, userB: 20}, ...]
  const radarData = [
    { subject: 'Comments', ...Object.fromEntries(chartData.map((d: any) => [d.name, (d.comments / maxComments) * 100])) },
    { subject: 'Status Changes', ...Object.fromEntries(chartData.map((d: any) => [d.name, (d.status_changes / maxStatus) * 100])) },
    { subject: 'MRs Created', ...Object.fromEntries(chartData.map((d: any) => [d.name, (d.mrs / maxMRs) * 100])) },
  ];

  const colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];

  return (
    <div className="bg-white rounded-lg shadow-md p-6 border border-gray-200">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">User Performance Comparison (Normalized)</h3>
      <ResponsiveContainer width="100%" height={400}>
        <RadarChart cx="50%" cy="50%" outerRadius="80%" data={radarData}>
          <PolarGrid />
          <PolarAngleAxis dataKey="subject" />
          <PolarRadiusAxis angle={30} domain={[0, 100]} />
          {users.map((user, index) => (
            <Radar
              key={user}
              name={user}
              dataKey={user}
              stroke={colors[index % colors.length]}
              fill={colors[index % colors.length]}
              fillOpacity={0.4}
            />
          ))}
          <Tooltip />
          <Legend />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
};

export default PAPIndicatorsRadarChart;

