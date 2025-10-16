import axios from 'axios';
import { Metrics, Forecast, Ticket, Filters, Project, AppConfig, CumulativeFlowPoint, DurationStats } from '../types';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const apiService = {
  // Filters options
  getFilterOptions: async (): Promise<{ projects: Array<{ id: number; name: string; key?: string }>; users: Array<{ id: number; display_name: string }>; statuses: string[]; customers: string[]; labels: string[] }> => {
    const response = await api.get(`/api/filters/options`);
    return response.data;
  },

  // Config
  getConfig: async (): Promise<AppConfig> => {
    const response = await api.get(`/api/config/`);
    return response.data;
  },

  // Projects
  getProjects: async (): Promise<Project[]> => {
    const response = await api.get(`/api/projects/`);
    return response.data;
  },

  // Metrics
  getMetrics: async (filters?: Filters): Promise<Metrics> => {
    const params = new URLSearchParams();
    if (filters?.project_id) params.append('project_id', filters.project_id.toString());
    if (filters?.project_ids && filters.project_ids.length) params.append('project_ids', filters.project_ids.join(','));
    if (filters?.user_id) params.append('user_id', filters.user_id.toString());
    if (filters?.status) params.append('status', filters.status);
    if (filters?.customers && filters.customers.length) params.append('customers', filters.customers.join(','));
    if (filters?.labels && filters.labels.length) params.append('labels', filters.labels.join(','));
    if (filters?.start_date) params.append('start_date', filters.start_date);
    if (filters?.end_date) params.append('end_date', filters.end_date);
    if ((filters as any)?.group_by) params.append('group_by', (filters as any).group_by);
    
    const response = await api.get(`/api/metrics?${params.toString()}`);
    return response.data;
  },

  getMetricsSummary: async (days: number = 30, project_id?: number) => {
    const params = new URLSearchParams();
    params.append('days', days.toString());
    if (project_id) params.append('project_id', project_id.toString());
    
    const response = await api.get(`/api/metrics/summary?${params.toString()}`);
    return response.data;
  },

  // Forecast
  getForecast: async (days_ahead: number = 30, project_id?: number, user_id?: number): Promise<Forecast> => {
    const params = new URLSearchParams();
    params.append('days_ahead', days_ahead.toString());
    if (project_id) params.append('project_id', project_id.toString());
    if (user_id) params.append('user_id', user_id.toString());
    
    const response = await api.get(`/api/forecast?${params.toString()}`);
    return response.data;
  },

  // CFD and Control/Lead Time
  getCumulativeFlow: async (filters?: Filters): Promise<{ cfd: CumulativeFlowPoint[] }> => {
    const params = new URLSearchParams();
    if (filters?.project_id) params.append('project_id', filters.project_id.toString());
    if (filters?.project_ids && filters.project_ids.length) params.append('project_ids', filters.project_ids.join(','));
    if (filters?.user_id) params.append('user_id', filters.user_id.toString());
    if (filters?.status) params.append('status', filters.status);
    if (filters?.customers && filters.customers.length) params.append('customers', filters.customers.join(','));
    if (filters?.labels && filters.labels.length) params.append('labels', filters.labels.join(','));
    if (filters?.start_date) params.append('start_date', filters.start_date);
    if (filters?.end_date) params.append('end_date', filters.end_date);
    if ((filters as any)?.group_by) params.append('group_by', (filters as any).group_by);

    const response = await api.get(`/api/metrics/cfd?${params.toString()}`);
    return response.data;
  },

  getControlChart: async (filters?: Filters): Promise<DurationStats> => {
    const params = new URLSearchParams();
    if (filters?.project_id) params.append('project_id', filters.project_id.toString());
    if (filters?.project_ids && filters.project_ids.length) params.append('project_ids', filters.project_ids.join(','));
    if (filters?.user_id) params.append('user_id', filters.user_id.toString());
    if (filters?.customers && filters.customers.length) params.append('customers', filters.customers.join(','));
    if (filters?.labels && filters.labels.length) params.append('labels', filters.labels.join(','));
    if (filters?.start_date) params.append('start_date', filters.start_date);
    if (filters?.end_date) params.append('end_date', filters.end_date);

    const response = await api.get(`/api/metrics/control-chart?${params.toString()}`);
    return response.data;
  },

  getLeadTime: async (filters?: Filters): Promise<DurationStats> => {
    const params = new URLSearchParams();
    if (filters?.project_id) params.append('project_id', filters.project_id.toString());
    if (filters?.project_ids && filters.project_ids.length) params.append('project_ids', filters.project_ids.join(','));
    if (filters?.user_id) params.append('user_id', filters.user_id.toString());
    if (filters?.customers && filters.customers.length) params.append('customers', filters.customers.join(','));
    if (filters?.labels && filters.labels.length) params.append('labels', filters.labels.join(','));
    if (filters?.start_date) params.append('start_date', filters.start_date);
    if (filters?.end_date) params.append('end_date', filters.end_date);

    const response = await api.get(`/api/metrics/lead-time?${params.toString()}`);
    return response.data;
  },

  getSprintForecast: async (sprint_length_days: number = 14, project_id?: number) => {
    const params = new URLSearchParams();
    params.append('sprint_length_days', sprint_length_days.toString());
    if (project_id) params.append('project_id', project_id.toString());
    
    const response = await api.get(`/api/forecast/sprint?${params.toString()}`);
    return response.data;
  },

  // Tickets
  getTickets: async (filters?: Filters & { limit?: number; offset?: number }): Promise<Ticket[]> => {
    const params = new URLSearchParams();
    if (filters?.project_id) params.append('project_id', filters.project_id.toString());
    if (filters?.project_ids && filters.project_ids.length) params.append('project_ids', filters.project_ids.join(','));
    if (filters?.user_id) params.append('user_id', filters.user_id.toString());
    if (filters?.status) params.append('status', filters.status);
    if (filters?.customers && filters.customers.length) params.append('customers', filters.customers.join(','));
    if (filters?.labels && filters.labels.length) params.append('labels', filters.labels.join(','));
    if (filters?.start_date) params.append('start_date', filters.start_date);
    if (filters?.end_date) params.append('end_date', filters.end_date);
    if (filters?.limit) params.append('limit', filters.limit.toString());
    if (filters?.offset) params.append('offset', filters.offset.toString());
    
    const response = await api.get(`/api/tickets?${params.toString()}`);
    return response.data;
  },

  getTicket: async (id: number): Promise<Ticket> => {
    const response = await api.get(`/api/tickets/${id}`);
    return response.data;
  },

  // Jira sync
  syncJira: async (project_keys?: string[], created_since?: string): Promise<any> => {
    const payload: any = {};
    if (project_keys && project_keys.length) payload.project_keys = project_keys;
    if (created_since) payload.created_since = created_since;
    const response = await api.post(`/api/jira/sync`, payload);
    return response.data;
  },
};