# Developer Guide — Jira Performance Dashboard

Last synced with `origin/main` on 2025-10-19.

This guide explains the application architecture, modules, data flow, and how to work on the codebase. It is organized by module to make onboarding and maintenance straightforward.

## Top-Level Overview

- Frontend: `jira-dashboard/frontend` (React + TypeScript + Tailwind + Recharts)
- Backend: `jira-dashboard/backend` (FastAPI + SQLAlchemy + Pydantic)
- Database: PostgreSQL
- Orchestration: Docker Compose

## Backend Modules (`jira-dashboard/backend/app`)

### 1) `main.py` (Application Entry)
- Initializes FastAPI app: title, description, version
- Configures CORS using `config.Settings.cors_origins`
- Mounts all API routers from `app/api/__init__.py`
- Global exception handling for consistent JSON errors
- Endpoints: `GET /` and `GET /health`
- Startup task: schedules Jira sync when credentials and project keys are set

Key functions:
- `add_request_id_header` middleware injects `X-Request-ID`
- `_json_error(request, status_code, error_type, message, details?, headers?)`

### 2) `config.py` (Configuration)
- `Settings` using `pydantic_settings.BaseSettings`
- Reads env vars for DB URL, Jira credentials, CORS, OAuth, timeouts, retries
- Computed properties for `cors_origins`, `jira_project_keys`, and `jira_created_since`

Important envs (see `README.md` for full list):
- `DATABASE_URL`, `JIRA_BASE_URL`, `JIRA_USERNAME`, `JIRA_API_TOKEN`, `CORS_ORIGINS`

### 3) `database.py` (Database Wiring)
- `engine`, `SessionLocal`, `Base`
- `get_db()` dependency that yields/cleans a SQLAlchemy session per request
- `ensure_schema(engine)`: adds newly introduced nullable columns if missing

### 4) `models.py` (ORM Models)
- `Project`, `User`, `Ticket`, `Commit` with relationships
- Lifecycle fields (`created_at`, `updated_at`, `started_at`, `resolved_at`) support metrics

### 5) `schemas.py` (Pydantic Schemas)
- API response models for `Project`, `User`, `Ticket`, `Commit`
- `MetricsResponse`, `ForecastResponse` aggregate shapes used by the UI
- `TicketFilters` common filter shape
- Field normalizers (e.g., `labels` string to list)

### 6) `exceptions.py` (Error Types & Handlers)
- Custom exceptions: `JiraConnectionError`, `JiraAuthenticationError`, `JiraAPIError`, `DatabaseError`, `ValidationError`
- Handlers produce consistent error payloads and log context

### 7) `jira_client.py` (Jira Integration)
- `JiraClient` async HTTP client with retry/backoff and dual auth (Basic/Bearer)
- Auto-selects API v2 for non-cloud base URLs if not configured
- Methods: `get_projects`, `get_project_issues`, `get_all_issues`, `get_users`, `parse_issue`
- `JiraOAuth` helper for OAuth2 URL and token exchange

### 8) `services/` (Business Logic)
- `metrics_service.py` — calculates KPIs, throughput, CFD, control chart (cycle time), lead time, SLA, average resolution time
- `forecast_service.py` — produces velocity forecasts and sprint predictions using linear regression with confidence intervals

### 9) `api/` (HTTP Endpoints)
- `tickets.py` — list tickets with filters; fetch by id or Jira id
- `metrics.py` — `/api/metrics`, `/api/metrics/summary`, `/api/metrics/cfd`, `/api/metrics/control-chart`, `/api/metrics/lead-time`
- `forecast.py` — `/api/forecast`, `/api/forecast/sprint`
- `projects.py` — list projects
- `config.py` — expose safe runtime config for frontend
- `filters.py` — dynamic filter options
- `jira_sync.py` — on-demand Jira sync; also exposes `run_startup_sync`
- `__init__.py` — aggregates routers as `api_router`

<!-- Note: Mock data utilities were removed on main. Use Jira sync to populate data. -->

## Frontend Modules (`jira-dashboard/frontend/src`)

### 1) `components/`
- `Dashboard.tsx`: main page composing filters, KPI cards, charts
- `Filters.tsx`: UI to select project(s), user, status, date range, labels, customers
- `KPICard.tsx`: generic stat card
- `components/Charts/`: Recharts-based components (Throughput, Velocity, Productivity, Commits, CFD, Control/Lead)

### 2) `services/api.ts`
- Axios client and typed API helpers for all backend endpoints
- Converts filter objects into query strings

### 3) `types/index.ts`
- TypeScript types mirroring backend schemas (`Metrics`, `Forecast`, `Ticket`, etc.)

## Data Flow

1. Frontend invokes REST endpoints via `api.ts`
2. FastAPI routes in `api/` validate and parse inputs
3. Services (`metrics_service`, `forecast_service`) query SQLAlchemy models
4. Pydantic `schemas` shape responses returned to the UI

## Local Development

- Backend: create venv, install `requirements.txt`, run `uvicorn app.main:app --reload`
- Frontend: `npm install && npm start` (ensure `REACT_APP_API_URL` points to backend)
- Data: trigger a Jira sync via `POST /api/jira/sync` or rely on startup sync when configured

## Testing

- Backend: `pytest` (consider adding coverage and CI)
- Frontend: `npm test`

## Adding Features (By Module)

- New metric:
  - Add logic in `services/metrics_service.py`
  - Expose via a new or existing route in `api/metrics.py`
  - Add UI in `components/Charts/` and wire to `Dashboard.tsx`

- New Jira-derived field:
  - Extend ORM in `models.py` and schema in `schemas.py`
  - Update parsing in `jira_client.py` and sync in `api/jira_sync.py`
  - Consider `ensure_schema` for non-breaking DB evolution

- New page/component:
  - Create TSX in `components/` and `components/Charts/`
  - Add types to `types/index.ts`
  - Call backend via `services/api.ts`

## Security & Ops

- Never log secrets; `JiraClient` masks values in debug output
- Use `CORS_ORIGINS` to limit frontend origins
- Prefer env vars via `.env` and `Settings`
- For production: run behind a reverse proxy, use gunicorn/uvicorn workers, enable TLS

## Module Dependency Graph (Backend)

- `main.py` → `api/api_router`, `config.Settings`, `database.Base/engine`
- `api/*` → `services/*`, `schemas.py`, `database.get_db`, `models.py`
- `services/*` → `models.py`, `sqlalchemy`, `numpy/pandas/sklearn` (forecast)
- `jira_client.py` → `config.Settings`, external Jira API

## Conventions

- Python: Black, flake8, PEP8; prefer explicit, descriptive names
- TypeScript: ESLint/Prettier; keep types in `types/index.ts`
- Commit messages: imperative mood, concise reason-focused summary

