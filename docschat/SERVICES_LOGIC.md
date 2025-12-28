# Backend Services Logic

This document details the core business logic encapsulated in the backend services.

## 1. Metrics Service (`metrics_service.py`)

The `MetricsService` class handles all calculations for dashboard charts and KPIs.

### Key Concepts

- **Resolved Status**: A ticket is considered "Resolved" (Done) if:
  1. It has a `resolved_at` timestamp.
  2. Its current status is **NOT** in the `NON_RESOLVED_STATUSES` list.
  
  **Non-Resolved Statuses**:
  - "Ready for Dev", "Open", "In Progress", "Waiting", "Created", "Reopened", "Blocked", "Confirmed", "Draft", "Pending", "In Coding", etc.

### Core Functions

- **`get_metrics(...)`**: Aggregates all KPIs including total tickets, resolution rate, productivity stats, throughput, and SLA compliance.
- **`get_ticket_throughput(...)`**: Calculates `created` vs `resolved` counts per period (day/week/month/year).
- **`get_cumulative_flow(...)`**: Builds upon throughput data to show cumulative "Open" (WIP) vs "Done" tickets over time.
- **`get_cycle_time_metrics(...)`**:
  - **Cycle Time**: Time from `started_at` (First "In Progress") to `resolved_at`.
  - Fallback: Uses `created_at` if `started_at` is missing.
  - Returns raw scatter points and P85/P95/Average stats.
- **`get_lead_time_metrics(...)`**:
  - **Lead Time**: Time from `created_at` to `resolved_at`.
- **`_get_sla_compliance(...)`**: Calculates percentage of tickets resolved within 7 days.

---

## 2. Forecast Service (`forecast_service.py`)

The `ForecastService` uses historical data to predict future team velocity.

### Logic
1. **Historical Data**: Fetches daily velocity (sum of Story Points or Count of resolved tickets) for the last 90 days.
2. **Model**: Uses **Linear Regression** (`sklearn`).
   - Features: `day_of_week`, `day_number` (trend).
   - Target: `velocity`.
3. **Prediction**:
   - Predicts velocity for the next N days.
   - Calculates 95% Confidence Intervals.
   - Determines trend ("increasing", "decreasing", "stable") by comparing recent 7-day avg vs older 7-day avg.
4. **Sprint Forecast**: Sums up predicted velocity for the next 14 days (default sprint length).

---

## 3. PAP Service (`pap_service.py`)

The `PAPService` (Process & Performance) aggregates activity metrics, potentially filtering by specific tracked users (configured in settings).

### Metrics Tracked
- **Jira Comments**: Count of comments by User & Project.
- **Status Changes**: Count of transitions by User & Project.
- **GitLab MRs**: Count of Merge Requests created by Author.

This service relies on `ActivityEvent` records which are populated via webhooks or sync jobs.
