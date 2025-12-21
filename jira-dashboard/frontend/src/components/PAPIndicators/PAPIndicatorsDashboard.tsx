import React, { useState, useEffect } from 'react';
import { apiService } from '../../services/api';
import { PAPIndicatorsMetrics } from '../../types';
import PAPIndicatorsCommentsChart from './PAPIndicatorsCommentsChart';
import PAPIndicatorsStatusChart from './PAPIndicatorsStatusChart';
import PAPIndicatorsMRChart from './PAPIndicatorsMRChart';
import PAPIndicatorsRadarChart from './PAPIndicatorsRadarChart';
import { AlertCircle, RefreshCw, Calendar, BarChart3, Users } from 'lucide-react';

const PAPIndicatorsDashboard: React.FC = () => {
  const [data, setData] = useState<PAPIndicatorsMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  const [dateRange, setDateRange] = useState({
    start: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    end: new Date().toISOString().split('T')[0]
  });

  const fetchPerformanceData = async () => {
    try {
      setLoading(true);
      setError(null);
      const metrics = await apiService.getPAPIndicators({
        start_date: new Date(dateRange.start).toISOString(),
        end_date: new Date(dateRange.end).toISOString()
      });
      setData(metrics);
    } catch (err) {
      console.error('Error fetching PAP indicators:', err);
      setError('Failed to fetch performance indicators. Please check if the backend is running.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPerformanceData();
  }, [dateRange]);

  if (loading && !data) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading performance data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">Team Performance Indicators</h1>
            <p className="text-gray-600">Visualize and compare performance across Jira and GitLab activity</p>
          </div>
          
          <div className="flex flex-col sm:flex-row items-end gap-4 bg-white p-4 rounded-lg shadow-sm border border-gray-200">
            <div>
              <label className="block text-xs font-medium text-gray-500 uppercase mb-1">
                <Calendar className="inline h-3 w-3 mr-1" />
                Start Date
              </label>
              <input
                type="date"
                value={dateRange.start}
                onChange={(e) => setDateRange(prev => ({ ...prev, start: e.target.value }))}
                className="block w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-500 uppercase mb-1">
                <Calendar className="inline h-3 w-3 mr-1" />
                End Date
              </label>
              <input
                type="date"
                value={dateRange.end}
                onChange={(e) => setDateRange(prev => ({ ...prev, end: e.target.value }))}
                className="block w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
            <button
              onClick={fetchPerformanceData}
              className="p-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
              title="Refresh data"
            >
              <RefreshCw className={`h-5 w-5 ${loading ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-8 flex items-center gap-3 text-red-700">
            <AlertCircle className="h-5 w-5" />
            <p>{error}</p>
          </div>
        )}

        {data && (
          <div className="space-y-8">
            {/* Summary Row */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="bg-white rounded-lg shadow-md p-6 border border-gray-200">
                <div className="flex items-center gap-4 mb-2">
                  <div className="p-3 bg-blue-100 text-blue-600 rounded-full">
                    <BarChart3 className="h-6 w-6" />
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-gray-900">
                      {data.comments_by_user_project.reduce((acc, curr) => acc + curr.count, 0)}
                    </div>
                    <div className="text-sm text-gray-500 uppercase font-medium">Total Comments</div>
                  </div>
                </div>
              </div>
              
              <div className="bg-white rounded-lg shadow-md p-6 border border-gray-200">
                <div className="flex items-center gap-4 mb-2">
                  <div className="p-3 bg-green-100 text-green-600 rounded-full">
                    <RefreshCw className="h-6 w-6" />
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-gray-900">
                      {data.status_changes_by_user_project.reduce((acc, curr) => acc + curr.count, 0)}
                    </div>
                    <div className="text-sm text-gray-500 uppercase font-medium">Status Changes</div>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-lg shadow-md p-6 border border-gray-200">
                <div className="flex items-center gap-4 mb-2">
                  <div className="p-3 bg-purple-100 text-purple-600 rounded-full">
                    <Users className="h-6 w-6" />
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-gray-900">
                      {data.mrs_by_author.reduce((acc, curr) => acc + curr.count, 0)}
                    </div>
                    <div className="text-sm text-gray-500 uppercase font-medium">MRs Created</div>
                  </div>
                </div>
              </div>
            </div>

            {/* Main Charts */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              <PAPIndicatorsCommentsChart data={data.comments_by_user_project} />
              <PAPIndicatorsStatusChart data={data.status_changes_by_user_project} />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              <PAPIndicatorsMRChart data={data.mrs_by_author} />
              <PAPIndicatorsRadarChart data={data} />
            </div>

            {/* Configuration Info */}
            <div className="bg-gray-100 rounded-lg p-6 border border-gray-200">
              <h3 className="text-sm font-semibold text-gray-700 uppercase mb-3">Tracked Configuration</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <span className="text-xs text-gray-500 block">Tracked User Emails</span>
                  <div className="flex flex-wrap gap-2 mt-1">
                    {data.filters.tracked_emails.length > 0 ? (
                      data.filters.tracked_emails.map(email => (
                        <span key={email} className="px-2 py-1 bg-white border border-gray-300 rounded text-xs text-gray-600">
                          {email}
                        </span>
                      ))
                    ) : (
                      <span className="text-xs text-gray-400 italic">No specific users tracked (showing all active)</span>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default PAPIndicatorsDashboard;

