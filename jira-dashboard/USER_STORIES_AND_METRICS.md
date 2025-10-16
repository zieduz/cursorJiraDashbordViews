## Jira Performance Dashboard — User Stories and Metrics

This document summarizes the key stakeholder user stories supported by the dashboard and enumerates the available charts/metrics with their practical benefits.

### Supported Roles and User Stories

- **Product Manager**
  - As a PM, I want to see ticket throughput and velocity forecasts so I can plan release scope and timelines with confidence.
  - As a PM, I want SLA and average resolution time so I can ensure customer commitments are met.
  - As a PM, I want to segment metrics by project and label so I can assess initiative performance.

- **Engineering Manager**
  - As an EM, I want resolved vs in‑progress vs created counts so I can spot bottlenecks and manage WIP.
  - As an EM, I want productivity by user/project so I can balance workloads and identify coaching opportunities.
  - As an EM, I want commits per issue so I can detect risky/high‑churn tickets early.

- **Scrum Master / Team Lead**
  - As a TL, I want daily created vs resolved so I can track flow and keep the backlog healthy.
  - As a TL, I want velocity forecasts (with confidence) so I can plan sprint capacity and scope.
  - As a TL, I want filters for users/status/customers so our stand‑ups focus on the right work.

- **Developer**
  - As a Developer, I want to see my created vs resolved and average story points/time so I can calibrate estimates.
  - As a Developer, I want commits per issue so I can coordinate on complex tickets and reduce rework.

- **Support / Success Manager**
  - As a Support lead, I want SLA compliance and average resolution time, filtered by customer, to maintain satisfaction.

- **Executive / Stakeholder**
  - As an Executive, I want a concise summary (resolution rate, SLA, average resolution time) to gauge delivery health.

### Metrics and Charts (What You See and Why It Matters)

All metrics support filtering by `project_id`/`project_ids`, `user_id`, `status`, `customers`, `labels`, `start_date`, `end_date` where applicable.

- **KPI: Total Tickets**
  - What: Count of tickets created in the selected period.
  - Why: Indicates backlog size and demand; helps assess workload trends.

- **KPI: Resolved Tickets (+ Resolution Rate)**
  - What: Count resolved; UI also shows percent resolved of total.
  - Why: Measures delivered throughput; early signal of under/over‑capacity.

- **KPI: In Progress**
  - What: Tickets in non‑resolved statuses.
  - Why: WIP gauge; too high implies context switching and cycle‑time risk.

- **KPI: SLA Compliance (+ Avg Resolution Time)**
  - What: Percent resolved within SLA (7 days); average resolution time (hours).
  - Why: Service reliability and customer satisfaction indicators; guides process improvements.

- **Chart: Ticket Throughput (Daily Created vs Resolved)**
  - What: Time series of tickets created and resolved per day.
  - Why: Reveals flow stability, backlog growth/shrinkage, and seasonal patterns.

- **Chart: Velocity Forecast (with Confidence Interval)**
  - What: Predicted daily story‑point velocity, confidence bounds, trend (increasing/stable/decreasing), next‑sprint prediction, and model accuracy.
  - Why: Data‑driven capacity planning; better sprint and release commitments.

- **Chart: Productivity by User**
  - What (UI): Created vs resolved by user.
  - Also available via API: average story points and average time spent per user.
  - Why: Identifies outliers, imbalances, and coaching opportunities; supports fair workload distribution.

- **Chart: Productivity by Project**
  - What (UI): Created vs resolved by project.
  - Also available via API: average story points and total story points per project.
  - Why: Compares delivery across projects to prioritize staffing and investments.

- **Chart: Commits per Issue (Top 20)**
  - What: Number of commits linked to each issue (top 20 by commit count).
  - Why: Highlights high‑churn or risky tickets; useful for code review focus and scope control.

### Filters and Segmentation (How You Slice the Data)

- **Projects**: Single or multiple `project_id` filters.
- **Users**: `user_id` for individual contribution views.
- **Status**: Focus on specific workflow states.
- **Customers**: Compare SLA and resolution performance by customer.
- **Labels**: Attribute‑based segmentation for initiatives or themes.
- **Date Range**: Any custom `start_date`/`end_date` window.

### Quick Metrics Summary API (For Dashboards/Reports)

- Period summary returns: `total_tickets`, `resolved_tickets`, `resolution_rate`, `sla_compliance`, `avg_resolution_time`.
- Why: Lightweight snapshot for leadership and automated reports.

### Related Endpoints

- Metrics: `GET /api/metrics`, `GET /api/metrics/summary`
- Forecast: `GET /api/forecast`, `GET /api/forecast/sprint`
- Tickets (supporting views): `GET /api/tickets` (with same filters)

### Notes

- SLA window is 7 days as implemented in the backend.
- Commits are joined to issues for commit‑per‑issue analytics.
- Forecasts use a regression‑based approach with an R²‑style model accuracy to convey confidence.
