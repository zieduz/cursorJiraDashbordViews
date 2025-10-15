import React, { useState, useEffect } from 'react';
import { 
  BarChart3, 
  CheckCircle, 
  Clock, 
  TrendingUp, 
  Users, 
  FolderOpen,
  AlertCircle
} from 'lucide-react';
import { apiService } from '../services/api';
import { Metrics, Forecast, Filters as FilterType } from '../types';
import KPICard from './KPICard';
import Filters from './Filters';
import ThroughputChart from './Charts/ThroughputChart';
import VelocityChart from './Charts/VelocityChart';
import ProductivityChart from './Charts/ProductivityChart';
import CommitsChart from './Charts/CommitsChart';

const Dashboard: React.FC = () => {
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [forecast, setForecast] = useState<Forecast | null>(null);
  const [filters, setFilters] = useState<FilterType>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Mock data for projects and users (in real app, these would come from API)
  const projects = [
    { id: 1, name: 'E-commerce Platform' },
    { id: 2, name: 'Mobile App' },
    { id: 3, name: 'Analytics Dashboard' }
  ];

  const users = [
    { id: 1, display_name: 'John Doe' },
    { id: 2, display_name: 'Jane Smith' },
    { id: 3, display_name: 'Mike Johnson' },
    { id: 4, display_name: 'Sarah Wilson' },
    { id: 5, display_name: 'David Brown' }
  ];

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [metricsData, forecastData] = await Promise.all([
        apiService.getMetrics(filters),
        apiService.getForecast(30, filters.project_id, filters.user_id)
      ]);

      setMetrics(metricsData);
      setForecast(forecastData);
    } catch (err) {
      setError('Failed to fetch data. Please check if the backend is running.');
      console.error('Error fetching data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [filters]);

  const handleFiltersChange = (newFilters: FilterType) => {
    setFilters(newFilters);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Error Loading Dashboard</h2>
          <p className="text-gray-600 mb-4">{error}</p>
          <button
            onClick={fetchData}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!metrics || !forecast) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Jira Performance Dashboard</h1>
          <p className="text-gray-600">Track team performance and forecast future velocity</p>
        </div>

        {/* Filters */}
        <Filters
          filters={filters}
          onFiltersChange={handleFiltersChange}
          projects={projects}
          users={users}
        />

        {/* KPI Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <KPICard
            title="Total Tickets"
            value={metrics.total_tickets}
            icon={BarChart3}
            color="blue"
          />
          <KPICard
            title="Resolved Tickets"
            value={metrics.tickets_resolved}
            change={`${((metrics.tickets_resolved / Math.max(metrics.total_tickets, 1)) * 100).toFixed(1)}% resolved`}
            changeType="positive"
            icon={CheckCircle}
            color="green"
          />
          <KPICard
            title="In Progress"
            value={metrics.tickets_in_progress}
            icon={Clock}
            color="yellow"
          />
          <KPICard
            title="SLA Compliance"
            value={`${metrics.sla_compliance.toFixed(1)}%`}
            change={`Avg: ${metrics.average_resolution_time.toFixed(1)}h`}
            changeType={metrics.sla_compliance > 80 ? 'positive' : 'negative'}
            icon={TrendingUp}
            color={metrics.sla_compliance > 80 ? 'green' : 'red'}
          />
        </div>

        {/* Charts Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Throughput Chart */}
          <ThroughputChart data={metrics.ticket_throughput} />

          {/* Velocity Forecast Chart */}
          <VelocityChart 
            data={forecast.predicted_velocity.map((item, index) => ({
              ...item,
              lower: forecast.confidence_interval[index]?.lower,
              upper: forecast.confidence_interval[index]?.upper
            }))}
            showConfidenceInterval={true}
          />
        </div>

        {/* Productivity Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <ProductivityChart
            data={metrics.productivity_per_user}
            title="Productivity by User"
          />
          <ProductivityChart
            data={metrics.productivity_per_project}
            title="Productivity by Project"
          />
        </div>

        {/* Commits Chart */}
        <div className="mb-8">
          <CommitsChart data={metrics.commits_per_issue} />
        </div>

        {/* Forecast Summary */}
        <div className="bg-white rounded-lg shadow-md p-6 border border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Forecast Summary</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">
                {forecast.next_sprint_prediction.velocity.toFixed(1)}
              </div>
              <div className="text-sm text-gray-600">Story Points (Next Sprint)</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">
                {forecast.trend}
              </div>
              <div className="text-sm text-gray-600">Trend</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600">
                {(forecast.model_accuracy * 100).toFixed(1)}%
              </div>
              <div className="text-sm text-gray-600">Model Accuracy</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;