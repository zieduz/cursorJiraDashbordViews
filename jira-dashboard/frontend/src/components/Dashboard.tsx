import React, { useState, useEffect } from 'react';
import { 
  BarChart3, 
  CheckCircle, 
  Clock, 
  TrendingUp, 
  Users, 
  FolderOpen,
  AlertCircle,
  RefreshCw
} from 'lucide-react';
import { apiService } from '../services/api';
import { Metrics, Forecast, Filters as FilterType, AppConfig } from '../types';
import KPICard from './KPICard';
import Filters from './Filters';
import ThroughputPanel from './Charts/ThroughputPanel';
import VelocityChart from './Charts/VelocityChart';
import ProductivityChart from './Charts/ProductivityChart';
import CFDChart from './Charts/CFDChart';
import ControlChart from './Charts/ControlChart';
import EMAChart from './Charts/EMAChart';
import BurnChart from './Charts/BurnChart';
import CommitsChart from './Charts/CommitsChart';

const Dashboard: React.FC = () => {
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [forecast, setForecast] = useState<Forecast | null>(null);
  const [filters, setFilters] = useState<FilterType>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Load projects, users, and statuses for filters
  const [projects, setProjects] = useState<Array<{ id: number; name: string; key?: string }>>([]);
  const [users, setUsers] = useState<Array<{ id: number; display_name: string }>>([]);
  const [statuses, setStatuses] = useState<string[]>([]);
  const [customers, setCustomers] = useState<string[]>([]);
  const [labels, setLabels] = useState<string[]>([]);
  const [cfdData, setCfdData] = useState<Array<{ date: string; open: number; done: number }>>([]);
  const [controlData, setControlData] = useState<{ cycle: { points: any[]; average_days: number; p85_days: number; p95_days: number }, lead: { points: any[]; average_days: number; p85_days: number; p95_days: number } }>({ cycle: { points: [], average_days: 0, p85_days: 0, p95_days: 0 }, lead: { points: [], average_days: 0, p85_days: 0, p95_days: 0 } });
  const [controlMode, setControlMode] = useState<'cycle' | 'lead'>('cycle');
  const [resyncLoading, setResyncLoading] = useState<boolean>(false);
  const [panels, setPanels] = useState<Array<{ id: string; filters: FilterType }>>([
    { id: 'panel-1', filters: {} }
  ]);
  const [resyncDate, setResyncDate] = useState<string>('');
  const [resyncProjectKeys, setResyncProjectKeys] = useState<string[]>([]);

  const triggerResync = async () => {
    try {
      setResyncLoading(true);
      // Call backend sync with selected params (fallback to configured defaults if empty)
      const keys = resyncProjectKeys && resyncProjectKeys.length ? resyncProjectKeys : undefined;
      const since = resyncDate || undefined;
      await apiService.syncJira(keys, since);
      // After resync completes, refresh filter options and dashboard data
      await Promise.all([
        apiService.getFilterOptions().then(({ projects, users, statuses, customers, labels }) => {
          setProjects(projects as any);
          setUsers(users);
          setStatuses(statuses);
          setCustomers(customers || []);
          setLabels(labels || []);
        }),
        fetchData(),
      ]);
    } catch (err) {
      console.error('Resync failed:', err);
      setError('Resync failed. Please check backend logs.');
    } finally {
      setResyncLoading(false);
    }
  };

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [metricsData, forecastData, cfdResp, cycleStats, leadStats] = await Promise.all([
        apiService.getMetrics(filters),
        apiService.getForecast(30, filters.project_id, filters.user_id),
        apiService.getCumulativeFlow({ ...filters, group_by: (filters as any)?.group_by || 'day' }),
        apiService.getControlChart(filters),
        apiService.getLeadTime(filters),
      ]);

      setMetrics(metricsData);
      setForecast(forecastData);
      setCfdData(cfdResp.cfd || []);
      setControlData({ cycle: cycleStats as any, lead: leadStats as any });
    } catch (err) {
      setError('Failed to fetch data. Please check if the backend is running.');
      console.error('Error fetching data:', err);
    } finally {
      setLoading(false);
    }
  };

  const addPanel = (filtersToClone?: FilterType) => {
    const newId = `panel-${Date.now()}`;
    setPanels((prev) => [...prev, { id: newId, filters: filtersToClone ? { ...filtersToClone } : {} }]);
  };

  const duplicatePanel = (id: string, cloneFilters: FilterType) => {
    addPanel(cloneFilters);
  };

  const removePanel = (id: string) => {
    setPanels((prev) => prev.filter((p) => p.id !== id));
  };

  useEffect(() => {
    fetchData();
  }, [filters]);

  useEffect(() => {
    // Fetch filter options once on mount
    Promise.all([
      apiService.getFilterOptions(),
      apiService.getConfig(),
    ])
      .then(([{ projects, users, statuses, customers, labels }, config]) => {
        setProjects(projects as any);
        setUsers(users);
        setStatuses(statuses);
        setCustomers(customers || []);
        setLabels(labels || []);
        // Prefill resync controls from backend config
        setResyncDate((config as AppConfig).jira_created_since || '');
        setResyncProjectKeys(((config as AppConfig).jira_project_keys || []) as string[]);
      })
      .catch((err) => {
        console.error('Error fetching initial data:', err);
      });
  }, []);

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

  const userProductivityData = metrics.productivity_per_user.map((item) => ({
    name: item.user,
    tickets_created: item.tickets_created,
    tickets_resolved: item.tickets_resolved,
  }));

  const projectProductivityData = metrics.productivity_per_project.map((item) => ({
    name: item.project,
    tickets_created: item.tickets_created,
    tickets_resolved: item.tickets_resolved,
  }));

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Jira Performance Dashboard</h1>
          <p className="text-gray-600">Track team performance and forecast future velocity</p>
        </div>

        {/* Actions + Filters */}
        <div className="flex flex-col lg:flex-row gap-4 items-stretch lg:items-end mb-4">
          <div className="flex-1">
        <Filters
          filters={filters}
          onFiltersChange={handleFiltersChange}
          projects={projects}
            users={users}
            statuses={statuses}
            customers={customers}
            labels={labels}
          />
          </div>
          <div className="flex flex-col items-stretch gap-2 lg:items-end">
            <div className="flex gap-2 items-end">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Sync Since</label>
                <input
                  type="date"
                  value={resyncDate}
                  onChange={(e) => setResyncDate(e.target.value)}
                  className="h-10 px-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Projects (Keys)</label>
                <select
                  multiple
                  value={resyncProjectKeys}
                  onChange={(e) => setResyncProjectKeys(Array.from(e.target.selectedOptions).map(o => o.value))}
                  className="h-28 px-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  {projects.filter(p => !!p.key).map((p) => (
                    <option key={p.key} value={p.key!}>{p.key} — {p.name}</option>
                  ))}
                </select>
              </div>
            </div>
            <button
              onClick={triggerResync}
              disabled={resyncLoading}
              className={`h-10 px-4 inline-flex items-center gap-2 rounded-md border ${resyncLoading ? 'bg-gray-200 text-gray-500 border-gray-300' : 'bg-blue-600 text-white border-blue-700 hover:bg-blue-700'} transition-colors`}
              title="Resync Jira data"
            >
              <RefreshCw className={`h-4 w-4 ${resyncLoading ? 'animate-spin' : ''}`} />
              {resyncLoading ? 'Resyncing…' : 'Resync Jira'}
            </button>
          </div>
        </div>

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
          {/* Clonable Throughput Panels */}
          <div className="flex flex-col gap-6">
            {panels.map((p) => (
              <ThroughputPanel
                key={p.id}
                id={p.id}
                initialFilters={p.filters}
                onDuplicate={(f) => duplicatePanel(p.id, f)}
                onRemove={() => removePanel(p.id)}
              />
            ))}
            <button
              onClick={() => addPanel({})}
              className="self-start h-9 px-4 inline-flex items-center gap-2 rounded-md border bg-gray-100 text-gray-700 border-gray-300 hover:bg-gray-200 text-sm"
            >
              + Add Throughput Panel
            </button>
          </div>

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

        {/* EMA + Burn Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <EMAChart
            data={metrics.ticket_throughput}
            period={7}
            sourceKey="resolved"
          />
          <BurnChart
            data={metrics.ticket_throughput}
            mode="burnup"
          />
        </div>

        {/* Productivity Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <ProductivityChart
            data={userProductivityData}
            title="Productivity by User"
          />
          <ProductivityChart
            data={projectProductivityData}
            title="Productivity by Project"
          />
        </div>

        {/* Flow + Control Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <CFDChart data={cfdData} />
          <div className="flex flex-col gap-3">
            <div className="flex items-center justify-between">
              <div className="text-sm text-gray-600">View</div>
              <div className="flex gap-2">
                <button
                  className={`h-8 px-3 rounded-md border text-sm ${controlMode === 'cycle' ? 'bg-blue-600 text-white border-blue-700' : 'bg-gray-100 text-gray-700 border-gray-300'}`}
                  onClick={() => setControlMode('cycle')}
                >
                  Cycle Time
                </button>
                <button
                  className={`h-8 px-3 rounded-md border text-sm ${controlMode === 'lead' ? 'bg-blue-600 text-white border-blue-700' : 'bg-gray-100 text-gray-700 border-gray-300'}`}
                  onClick={() => setControlMode('lead')}
                >
                  Lead Time
                </button>
              </div>
            </div>
            <ControlChart
              data={controlMode === 'lead' ? controlData.lead.points : controlData.cycle.points}
              average_days={(controlMode === 'lead' ? controlData.lead.average_days : controlData.cycle.average_days) || 0}
              p85_days={(controlMode === 'lead' ? controlData.lead.p85_days : controlData.cycle.p85_days) || 0}
              p95_days={(controlMode === 'lead' ? controlData.lead.p95_days : controlData.cycle.p95_days) || 0}
              mode={controlMode}
            />
          </div>
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