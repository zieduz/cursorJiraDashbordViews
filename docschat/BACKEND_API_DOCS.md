# Backend API Documentation

This document describes the API endpoints available in the Jira Dashboard backend.

## 1. Activity Analytics API
**Base URL**: `/api/analytics`

### `GET /jira/activity/heatmap`
Returns a 7x24 matrix of Jira activity counts (comments, status changes) for heatmap visualization.

- **Parameters**:
  - `projects` (optional): Comma-separated project IDs.
  - `event_types` (optional): Comma-separated types (`jira_comment`, `jira_status_change`). Default: both.
  - `assignees` (optional): Comma-separated user IDs.
  - `start_date` (required): ISO8601 UTC datetime.
  - `end_date` (required): ISO8601 UTC datetime.
  - `normalize` (optional): Boolean (default `false`). If true, returns ratios (0-1) instead of counts.

- **Response**:
  ```json
  {
    "matrix": [[0, ...], ...], // 7 rows (Sun-Sat) x 24 columns (0-23h)
    "total_events": 120,
    "filters": { ... }
  }
  ```

---

## 2. Commits API
**Base URL**: `/api/commits`

### `POST /ingest`
Ingests commit metadata and associates them with Jira tickets by parsing Jira keys from commit messages.

- **Payload**:
  ```json
  {
    "commits": [
      {
        "commit_hash": "abc1234",
        "message": "Fix bug PROJ-123",
        "created_at": "2023-01-01T12:00:00Z",
        "author_email": "user@example.com",
        "author_name": "John Doe",
        "project_key": "PROJ"
      }
    ]
  }
  ```

---

## 3. Filters API
**Base URL**: `/api/filters`

### `GET /options`
Returns dynamic filter options derived from the database.

- **Response**:
  ```json
  {
    "projects": [{ "id": 1, "name": "Mobile App", "key": "MOB" }],
    "users": [{ "id": 5, "display_name": "Jane Smith" }],
    "statuses": ["Open", "In Progress", "Done"],
    "customers": ["Client A", "Client B"],
    "labels": ["bug", "feature"]
  }
  ```

---

## 4. Forecast API
**Base URL**: `/api/forecast`

### `GET /`
Get velocity forecast using machine learning (Linear Regression).

- **Parameters**:
  - `days_ahead` (optional): Default 30.
  - `project_id` (optional): Filter by project.
  - `user_id` (optional): Filter by user.

- **Response**:
  ```json
  {
    "predicted_velocity": [{ "date": "2023-10-01", "velocity": 5.2 }, ...],
    "confidence_interval": [{ "date": "...", "lower": 4.1, "upper": 6.3 }],
    "trend": "increasing",
    "next_sprint_prediction": {
      "velocity": 25.5,
      "confidence": 0.85,
      "days": 14
    },
    "model_accuracy": 0.85
  }
  ```

### `GET /sprint`
Get forecast specifically for the next sprint.

- **Parameters**:
  - `sprint_length_days` (optional): Default 14.
  - `project_id` (optional).

---

## 5. Metrics API
**Base URL**: `/api/metrics`

### `GET /`
Get comprehensive metrics and KPIs.

- **Parameters**:
  - `start_date`, `end_date`: YYYY-MM-DD.
  - `project_id`, `project_ids`: Filter by project(s).
  - `user_id`: Filter by user.
  - `status`: Filter by ticket status.
  - `customers`: Comma-separated list.
  - `labels`: Comma-separated list.
  - `group_by`: Aggregation granularity (`day`, `week`, `month`, `year`).

- **Response**:
  Returns objects containing `total_tickets`, `tickets_resolved`, `productivity_per_user`, `ticket_throughput`, `sla_compliance`, `average_resolution_time`, etc.

### `GET /summary`
Quick metrics summary (Last N days).

### `GET /cfd`
Get Cumulative Flow Diagram data. Returns `open` vs `done` counts over time.

### `GET /control-chart`
Get Cycle Time metrics (scatter plot points + percentiles).

### `GET /lead-time`
Get Lead Time metrics (scatter plot points + percentiles).

---

## 6. PAP Indicators API (Process & Performance)
**Base URL**: `/api/pap-indicators`

### `GET /summary`
Aggregated performance indicators (comments, status changes, MRs).

- **Parameters**:
  - `start_date`, `end_date`: ISO8601 UTC.

- **Response**:
  ```json
  {
    "comments_by_user_project": [...],
    "status_changes_by_user_project": [...],
    "mrs_by_author": [...],
    "filters": { "tracked_emails": [...] }
  }
  ```

---

## 7. Projects API
**Base URL**: `/api/projects`

### `GET /`
List all projects.

---

## 8. Tickets API
**Base URL**: `/api/tickets`

### `GET /`
Get tickets list with filtering and pagination.

- **Parameters**: `project_id`, `user_id`, `status`, `customers`, `labels`, `start_date`, `end_date`, `limit`, `offset`.

### `GET /{ticket_id}`
Get a specific ticket by internal DB ID.

### `GET /jira/{jira_id}`
Get a specific ticket by Jira Key (e.g., `PROJ-123`).
