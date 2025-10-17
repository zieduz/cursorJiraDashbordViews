import React, { useEffect, useState } from 'react';
import { Copy, Trash2, RefreshCw, Layers, Calendar, FolderOpen, User, Tag, Building2 } from 'lucide-react';
import { apiService } from '../../services/api';
import { Filters, Granularity, Metrics } from '../../types';
import ThroughputChart from './ThroughputChart';

interface ThroughputPanelProps {
  id: string;
  initialFilters: Filters;
  onDuplicate: (filters: Filters) => void;
  onRemove: () => void;
}

const ThroughputPanel: React.FC<ThroughputPanelProps> = ({ id, initialFilters, onDuplicate, onRemove }) => {
  const [filters, setFilters] = useState<Filters>(initialFilters || {});
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<Metrics['ticket_throughput']>([]);
  const [projects, setProjects] = useState<Array<{ id: number; name: string; key?: string }>>([]);
  const [users, setUsers] = useState<Array<{ id: number; display_name: string }>>([]);
  const [statuses, setStatuses] = useState<string[]>([]);
  const [customers, setCustomers] = useState<string[]>([]);
  const [labels, setLabels] = useState<string[]>([]);
  const [showMA, setShowMA] = useState<boolean>(false);
  const [maType, setMaType] = useState<'EMA' | 'SMA'>('EMA');
  const [maPeriod, setMaPeriod] = useState<number>(7);
  const [maSource, setMaSource] = useState<'created' | 'resolved'>('resolved');
  const [overlayByCustomer, setOverlayByCustomer] = useState<boolean>(false);
  const [overlayMetric, setOverlayMetric] = useState<'created' | 'resolved'>('resolved');
  const [overlaySeries, setOverlaySeries] = useState<Array<{ name: string; data: Metrics['ticket_throughput'] }>>([]);

  const fetchThroughput = async () => {
    try {
      setLoading(true);
      setError(null);
      if (overlayByCustomer && (filters.customers && filters.customers.length > 0)) {
        const customers = filters.customers as string[];
        const series = await Promise.all(
          customers.map(async (c) => {
            const m = await apiService.getMetrics({ ...filters, customers: [c] });
            return { name: c, data: m.ticket_throughput };
          })
        );
        setOverlaySeries(series);
        setData(series[0]?.data || []);
      } else {
        const metrics = await apiService.getMetrics(filters);
        setData(metrics.ticket_throughput);
        setOverlaySeries([]);
      }
    } catch (e) {
      setError('Failed to load throughput');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    apiService.getFilterOptions().then(({ projects, users, statuses, customers, labels }) => {
      setProjects(projects as any);
      setUsers(users);
      setStatuses(statuses);
      setCustomers(customers || []);
      setLabels(labels || []);
    }).catch(() => {});
    fetchThroughput();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [JSON.stringify(filters), overlayByCustomer]);

  // Refetch when overlay toggled, handled above in deps

  return (
    <div className="bg-white rounded-lg shadow-md border border-gray-200">
      <div className="flex items-center justify-between p-4 border-b border-gray-200">
        <div className="flex flex-col gap-3 w-full">
          <div className="flex items-center gap-3">
            <h3 className="text-lg font-semibold text-gray-900">Ticket Throughput</h3>
            <div className="flex items-center gap-2">
              <label className="text-sm text-gray-600 flex items-center gap-1">
                <Layers className="h-4 w-4" />
                <span>Granularity</span>
              </label>
              <select
                value={(filters.group_by as Granularity) || 'day'}
                onChange={(e) => setFilters({ ...filters, group_by: e.target.value as Granularity })}
                className="px-2 py-1 border border-gray-300 rounded-md text-sm"
              >
                <option value="day">Day</option>
                <option value="week">Week</option>
                <option value="month">Month</option>
                <option value="year">Year</option>
              </select>
            </div>
            <div className="flex items-center gap-2">
              <label className="text-sm text-gray-600 flex items-center gap-1">
                <Calendar className="h-4 w-4" />
                <span>Start</span>
              </label>
              <input
                type="date"
                value={filters.start_date || ''}
                onChange={(e) => setFilters({ ...filters, start_date: e.target.value || undefined })}
                className="px-2 py-1 border border-gray-300 rounded-md text-sm"
              />
              <label className="text-sm text-gray-600 flex items-center gap-1">
                <span>End</span>
              </label>
              <input
                type="date"
                value={filters.end_date || ''}
                onChange={(e) => setFilters({ ...filters, end_date: e.target.value || undefined })}
                className="px-2 py-1 border border-gray-300 rounded-md text-sm"
              />
            </div>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">
                <FolderOpen className="h-3 w-3 inline mr-1" /> Projects
              </label>
              <select
                multiple
                value={(filters.project_ids || []).map(String)}
                onChange={(e) => {
                  const selected = Array.from(e.target.selectedOptions).map((o) => parseInt(o.value));
                  setFilters({ ...filters, project_ids: selected.length ? selected : undefined, project_id: undefined });
                }}
                className="w-full px-2 py-1 border border-gray-300 rounded-md h-24 text-sm"
              >
                {projects.map((p) => (
                  <option key={p.id} value={p.id}>{p.name}{p.key ? ` (${p.key})` : ''}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">
                <User className="h-3 w-3 inline mr-1" /> User
              </label>
              <select
                value={filters.user_id || ''}
                onChange={(e) => setFilters({ ...filters, user_id: e.target.value ? parseInt(e.target.value) : undefined })}
                className="w-full px-2 py-1 border border-gray-300 rounded-md text-sm"
              >
                <option value="">All Users</option>
                {users.map((u) => (
                  <option key={u.id} value={u.id}>{u.display_name}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">Status</label>
              <select
                value={filters.status || ''}
                onChange={(e) => setFilters({ ...filters, status: e.target.value || undefined })}
                className="w-full px-2 py-1 border border-gray-300 rounded-md text-sm"
              >
                <option value="">All Statuses</option>
                {statuses.map((s) => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">
                <Building2 className="h-3 w-3 inline mr-1" /> Customers
              </label>
              <select
                multiple
                value={filters.customers || []}
                onChange={(e) => setFilters({ ...filters, customers: Array.from(e.target.selectedOptions).map(o => o.value) })}
                className="w-full px-2 py-1 border border-gray-300 rounded-md h-24 text-sm"
              >
                {customers.map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">
                <Tag className="h-3 w-3 inline mr-1" /> Labels
              </label>
              <select
                multiple
                value={filters.labels || []}
                onChange={(e) => setFilters({ ...filters, labels: Array.from(e.target.selectedOptions).map(o => o.value) })}
                className="w-full px-2 py-1 border border-gray-300 rounded-md h-24 text-sm"
              >
                {labels.map((l) => (
                  <option key={l} value={l}>{l}</option>
                ))}
              </select>
            </div>
          </div>
          {/* Moving Average Overlay Controls */}
          <div className="flex items-center gap-2">
            <label className="text-sm text-gray-600">
              <input
                type="checkbox"
                className="mr-1 align-middle"
                checked={showMA}
                onChange={(e) => setShowMA(e.target.checked)}
              />
              <span>Moving Average</span>
            </label>
            <select
              value={maType}
              onChange={(e) => setMaType(e.target.value as 'EMA' | 'SMA')}
              className="px-2 py-1 border border-gray-300 rounded-md text-sm"
              disabled={!showMA || overlayByCustomer}
            >
              <option value="EMA">EMA</option>
              <option value="SMA">SMA</option>
            </select>
            <label className="text-sm text-gray-600">Period</label>
            <select
              value={maPeriod}
              onChange={(e) => setMaPeriod(parseInt(e.target.value))}
              className="px-2 py-1 border border-gray-300 rounded-md text-sm"
              disabled={!showMA || overlayByCustomer}
            >
              <option value={7}>7</option>
              <option value={14}>14</option>
              <option value={30}>30</option>
              <option value={60}>60</option>
            </select>
            <label className="text-sm text-gray-600">Source</label>
            <select
              value={maSource}
              onChange={(e) => setMaSource(e.target.value as 'created' | 'resolved')}
              className="px-2 py-1 border border-gray-300 rounded-md text-sm"
              disabled={!showMA || overlayByCustomer}
            >
              <option value="resolved">Resolved</option>
              <option value="created">Created</option>
            </select>
            <span className="mx-2 text-gray-300">|</span>
            <label className="text-sm text-gray-600">
              <input
                type="checkbox"
                className="mr-1 align-middle"
                checked={overlayByCustomer}
                onChange={(e) => setOverlayByCustomer(e.target.checked)}
              />
              <span>Overlay by Customer</span>
            </label>
            <label className={`text-sm text-gray-600 ${!overlayByCustomer ? 'opacity-50' : ''}`}>Metric</label>
            <select
              value={overlayMetric}
              onChange={(e) => setOverlayMetric(e.target.value as 'created' | 'resolved')}
              className="px-2 py-1 border border-gray-300 rounded-md text-sm"
              disabled={!overlayByCustomer}
            >
              <option value="resolved">Resolved</option>
              <option value="created">Created</option>
            </select>
          </div>
        </div>
        <div className="flex items-center gap-2 pl-4">
          <button
            onClick={() => onDuplicate(filters)}
            className="h-8 px-3 inline-flex items-center gap-2 rounded-md border bg-gray-100 text-gray-700 border-gray-300 hover:bg-gray-200 text-sm"
            title="Duplicate panel"
          >
            <Copy className="h-4 w-4" />
            Clone
          </button>
          <button
            onClick={fetchThroughput}
            className="h-8 px-3 inline-flex items-center gap-2 rounded-md border bg-blue-600 text-white border-blue-700 hover:bg-blue-700 text-sm"
            title="Refresh"
          >
            <RefreshCw className={`${loading ? 'animate-spin' : ''} h-4 w-4`} />
            Refresh
          </button>
          <button
            onClick={onRemove}
            className="h-8 px-3 inline-flex items-center gap-2 rounded-md border bg-red-50 text-red-700 border-red-200 hover:bg-red-100 text-sm"
            title="Remove panel"
          >
            <Trash2 className="h-4 w-4" />
            Remove
          </button>
        </div>
      </div>
      <div className="p-6">
        {error ? (
          <div className="text-red-600 text-sm">{error}</div>
        ) : (
          <ThroughputChart 
            data={data}
            showMovingAverage={showMA && !overlayByCustomer}
            maType={maType}
            maPeriod={maPeriod}
            maSource={maSource}
            overlaySeries={overlayByCustomer ? overlaySeries : []}
            overlayMetric={overlayMetric}
          />
        )}
      </div>
    </div>
  );
};

export default ThroughputPanel;
