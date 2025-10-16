export interface Ticket {
  id: number;
  jira_id: string;
  project_id: number;
  assignee_id?: number;
  summary: string;
  description?: string;
  status: string;
  priority?: string;
  issue_type?: string;
  customer?: string;
  labels?: string[];
  story_points?: number;
  time_estimate?: number;
  time_spent?: number;
  created_at: string;
  updated_at?: string;
  resolved_at?: string;
}

export interface Project {
  id: number;
  key: string;
  name: string;
  description?: string;
  created_at: string;
}

export interface Metrics {
  total_tickets: number;
  tickets_created: number;
  tickets_resolved: number;
  tickets_in_progress: number;
  productivity_per_user: Array<{
    user: string;
    tickets_created: number;
    tickets_resolved: number;
    avg_story_points: number;
    avg_time_spent: number;
  }>;
  productivity_per_project: Array<{
    project: string;
    tickets_created: number;
    tickets_resolved: number;
    avg_story_points: number;
    total_story_points: number;
  }>;
  ticket_throughput: Array<{
    date: string;
    created: number;
    resolved: number;
  }>;
  commits_per_issue: Array<{
    ticket_id: string;
    commit_count: number;
  }>;
  sla_compliance: number;
  average_resolution_time: number;
}

export interface Forecast {
  predicted_velocity: Array<{
    date: string;
    velocity: number;
  }>;
  confidence_interval: Array<{
    date: string;
    lower: number;
    upper: number;
  }>;
  trend: string;
  next_sprint_prediction: {
    velocity: number;
    confidence: number;
    days: number;
  };
  model_accuracy: number;
}

export interface Filters {
  project_id?: number;
  project_ids?: number[];
  user_id?: number;
  status?: string;
  customers?: string[];
  labels?: string[];
  start_date?: string;
  end_date?: string;
}

export interface AppConfig {
  jira_project_keys: string[];
  jira_created_since: string;
}