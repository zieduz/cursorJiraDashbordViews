import React, { useState, useEffect } from 'react';
import { apiService } from '../../services/api';
import { ActivityHeatmapResponse } from '../../types';
import HeatmapChart from '../Charts/HeatmapChart';
import { AlertCircle, RefreshCw, Calendar, Users, FolderOpen } from 'lucide-react';

interface ActivityFilters {
  projectIds: number[];
  assigneeIds: number[];
  dateRange: {
    start: Date;
    end: Date;
  };
  normalize: boolean;
}

const ActivityDashboard: React.FC = () => {
  const [heatmapData, setHeatmapData] = useState<ActivityHeatmapResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Filter states
  const [projects, setProjects] = useState<Array<{ id: number; name: string; key?: string }>>([]);
  const [users, setUsers] = useState<Array<{ id: number; display_name: string }>>([]);
  const [filters, setFilters] = useState<ActivityFilters>({
    projectIds: [],
    assigneeIds: [],
    dateRange: {
      start: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000), // Last 30 days
      end: new Date()
    },
    normalize: false
  });

  // Fetch filter options
  useEffect(() => {
    apiService.getFilterOptions()
      .then(({ projects, users }) => {
        setProjects(projects);
        setUsers(users);
      })
      .catch((err) => {
        console.error('Error fetching filter options:', err);
      });
  }, []);

  // Fetch heatmap data
  const fetchHeatmapData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await apiService.getJiraActivityHeatmap({
        projects: filters.projectIds.length > 0 ? filters.projectIds : undefined,
        assignees: filters.assigneeIds.length > 0 ? filters.assigneeIds : undefined,
        start_date: filters.dateRange.start.toISOString(),
        end_date: filters.dateRange.end.toISOString(),
        normalize: filters.normalize,
        event_types: ['jira_comment', 'jira_status_change']
      });
      
      setHeatmapData(response);
    } catch (err) {
      console.error('Error fetching heatmap data:', err);
      setError('Failed to fetch activity data. Please check if the backend is running.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHeatmapData();
  }, [filters]);

  // Format date for input
  const formatDateForInput = (date: Date) => {
    return date.toISOString().split('T')[0];
  };

  if (loading && !heatmapData) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading activity data...</p>
        </div>
      </div>
    );
  }

  if (error && !heatmapData) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Error Loading Activity Data</h2>
          <p className="text-gray-600 mb-4">{error}</p>
          <button
            onClick={fetchHeatmapData}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Jira Activity Heatmap</h1>
          <p className="text-gray-600">Visualize team activity patterns across time</p>
        </div>

        {/* Filters */}
        <div className="bg-white rounded-lg shadow-md p-6 border border-gray-200 mb-8">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Projects Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                <FolderOpen className="inline h-4 w-4 mr-1" />
                Projects
              </label>
              <select
                multiple
                value={filters.projectIds.map(String)}
                onChange={(e) => {
                  const selected = Array.from(e.target.selectedOptions).map(o => parseInt(o.value));
                  setFilters(prev => ({ ...prev, projectIds: selected }));
                }}
                className="w-full h-24 px-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {projects.map((project) => (
                  <option key={project.id} value={project.id}>
                    {project.key ? `${project.key} - ` : ''}{project.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Assignees Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                <Users className="inline h-4 w-4 mr-1" />
                Assignees
              </label>
              <select
                multiple
                value={filters.assigneeIds.map(String)}
                onChange={(e) => {
                  const selected = Array.from(e.target.selectedOptions).map(o => parseInt(o.value));
                  setFilters(prev => ({ ...prev, assigneeIds: selected }));
                }}
                className="w-full h-24 px-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {users.map((user) => (
                  <option key={user.id} value={user.id}>
                    {user.display_name}
                  </option>
                ))}
              </select>
            </div>

            {/* Date Range */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                <Calendar className="inline h-4 w-4 mr-1" />
                Date Range
              </label>
              <div className="space-y-2">
                <input
                  type="date"
                  value={formatDateForInput(filters.dateRange.start)}
                  onChange={(e) => {
                    const date = new Date(e.target.value);
                    setFilters(prev => ({
                      ...prev,
                      dateRange: { ...prev.dateRange, start: date }
                    }));
                  }}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <input
                  type="date"
                  value={formatDateForInput(filters.dateRange.end)}
                  onChange={(e) => {
                    const date = new Date(e.target.value);
                    setFilters(prev => ({
                      ...prev,
                      dateRange: { ...prev.dateRange, end: date }
                    }));
                  }}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>

            {/* Options */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Options</label>
              <div className="space-y-2">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={filters.normalize}
                    onChange={(e) => {
                      setFilters(prev => ({ ...prev, normalize: e.target.checked }));
                    }}
                    className="mr-2"
                  />
                  <span className="text-sm text-gray-700">Normalize values</span>
                </label>
                <button
                  onClick={fetchHeatmapData}
                  disabled={loading}
                  className={`w-full px-4 py-2 inline-flex items-center justify-center gap-2 rounded-md border ${
                    loading ? 'bg-gray-200 text-gray-500 border-gray-300' : 'bg-blue-600 text-white border-blue-700 hover:bg-blue-700'
                  } transition-colors`}
                >
                  <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
                  {loading ? 'Loading...' : 'Refresh'}
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Heatmap */}
        <div className="bg-white rounded-lg shadow-md p-6 border border-gray-200">
          <div className="mb-4">
            <h2 className="text-lg font-semibold text-gray-900">Activity Pattern</h2>
            <p className="text-sm text-gray-600">
              Showing {heatmapData?.total_events || 0} events 
              {filters.normalize ? ' (normalized)' : ''}
            </p>
          </div>
          
          {heatmapData && heatmapData.matrix ? (
            <HeatmapChart 
              data={heatmapData.matrix} 
              normalized={filters.normalize}
            />
          ) : (
            <div className="text-center py-8 text-gray-500">
              No activity data available for the selected filters
            </div>
          )}

          {/* Legend */}
          <div className="mt-6 flex items-center justify-center gap-8">
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-blue-100 border border-gray-300"></div>
              <span className="text-sm text-gray-600">Low activity</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-blue-400 border border-gray-300"></div>
              <span className="text-sm text-gray-600">Medium activity</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-blue-600 border border-gray-300"></div>
              <span className="text-sm text-gray-600">High activity</span>
            </div>
          </div>
        </div>

        {/* Summary Stats */}
        {heatmapData && (
          <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-white rounded-lg shadow-md p-6 border border-gray-200 text-center">
              <div className="text-2xl font-bold text-blue-600">{heatmapData.total_events}</div>
              <div className="text-sm text-gray-600">Total Events</div>
            </div>
            <div className="bg-white rounded-lg shadow-md p-6 border border-gray-200 text-center">
              <div className="text-2xl font-bold text-green-600">
                {Math.round(heatmapData.total_events / 7 / 24) || 0}
              </div>
              <div className="text-sm text-gray-600">Average Events per Hour</div>
            </div>
            <div className="bg-white rounded-lg shadow-md p-6 border border-gray-200 text-center">
              <div className="text-2xl font-bold text-purple-600">
                {(() => {
                  const flat = heatmapData.matrix.flat();
                  const maxHour = Math.max(...flat);
                  const maxIndex = flat.indexOf(maxHour);
                  const day = Math.floor(maxIndex / 24);
                  const hour = maxIndex % 24;
                  const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
                  return `${days[day]} ${hour}:00`;
                })()}
              </div>
              <div className="text-sm text-gray-600">Peak Activity Time</div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ActivityDashboard;