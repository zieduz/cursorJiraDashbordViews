# CLAUDE.md — AI Assistant Guide for Jira Performance Dashboard

## Project Overview

A full-stack Jira Performance Dashboard that connects to Jira REST API to visualize team performance metrics and forecast future velocity using machine learning. Features real-time KPI cards, interactive charts, predictive analytics, activity heatmaps, and GitLab integration.

## Repository Structure

```
cursorJiraDashbordViews/
├── jira-dashboard/
│   ├── frontend/          # React 19 + TypeScript + Tailwind CSS
│   ├── backend/           # FastAPI + SQLAlchemy + PostgreSQL
│   ├── docker-compose.yml # Production orchestration
│   └── docker-compose.dev.yml
├── agenticiaproject/      # Agentic abstraction layer
├── .prompts/              # Prompt templates
├── DEVELOPER_GUIDE.md     # Detailed module breakdown
└── CLAUDE.md              # This file
```

## Tech Stack

| Layer    | Technology                                                  |
|----------|-------------------------------------------------------------|
| Frontend | React 19, TypeScript 4.9, Tailwind CSS 3.4, Recharts, Axios |
| Backend  | FastAPI 0.104, SQLAlchemy 2.0, Pydantic 2.5, Alembic       |
| Database | PostgreSQL 15 (Docker)                                      |
| ML       | scikit-learn 1.3 (linear regression, confidence intervals)  |
| Infra    | Docker Compose, Node 18+, Python 3.11+                     |

## Quick Commands

### Frontend (`jira-dashboard/frontend/`)
```bash
npm start              # Dev server on :3000
npm run build          # Production build
npm test               # Jest + React Testing Library
```

### Backend (`jira-dashboard/backend/`)
```bash
uvicorn app.main:app --reload   # Dev server on :8000
pytest                          # Run tests
black .                         # Format code
flake8 .                        # Lint
```

### Database
```bash
alembic revision --autogenerate -m "description"   # Generate migration
alembic upgrade head                               # Apply migrations
```

### Docker
```bash
docker-compose up -d --build    # Start all services (postgres:5432, backend:8000, frontend:3000)
docker-compose down -v          # Shutdown with volume cleanup
```

## Architecture

```
React Frontend (port 3000)
    ↓ Axios HTTP calls
FastAPI Routers (port 8000)
    ↓
Service Layer (metrics_service, forecast_service, pap_service)
    ↓
SQLAlchemy ORM → PostgreSQL (port 5432)
    ↑
Jira REST API / GitLab API (external sync)
```

### Key Backend Files
- `app/main.py` — FastAPI app entry, CORS, middleware, error handling
- `app/config.py` — Pydantic Settings (all env vars)
- `app/models.py` — ORM models: Project, User, Ticket, Commit, Activity
- `app/schemas.py` — Pydantic response schemas (API contracts)
- `app/jira_client.py` — Jira HTTP client (Basic + Bearer auth, retry/backoff)
- `app/gitlab_client.py` — GitLab HTTP client for commit tracking
- `app/services/metrics_service.py` — KPI calculations (throughput, productivity, SLA, CFD, control chart)
- `app/services/forecast_service.py` — ML forecasting (linear regression, confidence intervals)
- `app/services/pap_service.py` — Team Performance (PAP) indicators
- `app/api/` — Route handlers grouped by domain (metrics, forecast, tickets, projects, filters, jira_sync, activity, gitlab, commits, pap_indicators, config)
- `app/exceptions.py` — Custom exceptions (JiraConnectionError, ValidationError, etc.)

### Key Frontend Files
- `src/App.tsx` — Routing (3 pages: Dashboard, Activity Heatmap, PAP Indicators)
- `src/components/Dashboard.tsx` — Main dashboard with KPIs and charts
- `src/components/Filters.tsx` — Filter controls (project, user, date, status, labels)
- `src/components/Charts/` — All chart components (Throughput, Velocity, Productivity, CFD, Control, Burn, EMA, Heatmap, LeadTime, Commits)
- `src/components/ActivityHeatmap/` — Jira activity heatmap dashboard
- `src/components/PAPIndicators/` — Team performance indicator charts (Radar, MR, Comments, Status)
- `src/services/api.ts` — Axios API client with all backend endpoint calls
- `src/types/index.ts` — TypeScript interfaces (Metrics, Forecast, Ticket, Project, Filters, etc.)

## API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/metrics` | Full metrics (KPIs, throughput, productivity, CFD, control chart) |
| GET | `/api/metrics/summary` | Quick summary |
| GET | `/api/metrics/cfd` | Cumulative Flow Diagram data |
| GET | `/api/metrics/control-chart` | Cycle time control chart |
| GET | `/api/metrics/lead-time` | Lead time metrics |
| GET | `/api/forecast` | Velocity forecast with confidence intervals |
| GET | `/api/forecast/sprint` | Sprint-specific prediction |
| GET | `/api/tickets` | Tickets list with filters |
| GET | `/api/tickets/{id}` | Ticket by DB ID |
| GET | `/api/tickets/jira/{jira_id}` | Ticket by Jira ID |
| GET | `/api/projects` | Project list |
| GET | `/api/filters/options` | Dynamic filter dropdown values |
| POST | `/api/jira/sync` | Trigger Jira data sync |
| GET | `/api/config` | Runtime config (safe for frontend) |
| GET | `/api/pap-indicators` | Team performance indicators |

## Code Conventions

### Python (Backend)
- **Style:** PEP8, formatted with Black, linted with Flake8
- **Naming:** snake_case for functions/variables, PascalCase for classes
- **Type hints:** Use Pydantic schemas for API contracts, type annotations on functions
- **Dependency injection:** Use FastAPI's `Depends()` pattern (e.g., `get_db` for sessions)
- **Error handling:** Custom exceptions in `exceptions.py` with structured JSON error payloads
- **Request tracking:** X-Request-ID header middleware

### TypeScript (Frontend)
- **Style:** ESLint (react-app config), strict TypeScript enabled
- **Naming:** camelCase for variables/functions, PascalCase for components/types
- **Components:** Functional components with hooks (useState, useEffect, useCallback)
- **State:** React component state (no Redux/Zustand)
- **API calls:** Centralized in `services/api.ts`, all return typed responses

### Database
- **Migrations:** Always use Alembic — never modify schema directly
- **Models:** SQLAlchemy declarative with lifecycle timestamps (created_at, updated_at)
- **Indexes:** Applied on frequently queried fields (jira_id, email, project_id)

## Environment Variables

### Required
- `DATABASE_URL` — PostgreSQL connection string
- `JIRA_BASE_URL` — Jira instance URL
- `JIRA_USERNAME` — Jira email/username
- `JIRA_API_TOKEN` — Jira API token
- `SECRET_KEY` — JWT secret key

### Optional
- `JIRA_AUTH_TYPE` — `basic` (default) or `bearer`
- `JIRA_BEARER_TOKEN` — PAT for Jira Data Center
- `JIRA_API_VERSION` — `2` or `3` (auto-detected)
- `JIRA_PROJECT_KEYS` — Comma-separated projects to sync
- `JIRA_STORY_POINTS_FIELD` — Custom field key (default: `customfield_10016`)
- `JIRA_CREATED_SINCE` — Date filter (YYYY-MM-DD)
- `JIRA_DEBUG` — Enable verbose logging
- `GITLAB_BASE_URL` — GitLab instance URL
- `GITLAB_TOKEN` — GitLab personal access token
- `GITLAB_PROJECT_IDS` — JSON array or CSV of project IDs
- `CORS_ORIGINS` — Comma-separated allowed origins
- `REACT_APP_API_URL` — Backend URL for frontend (default: `http://localhost:8000`)

See `.env.example` files in `jira-dashboard/`, `jira-dashboard/backend/`, and `jira-dashboard/frontend/` for full templates.

## Application Pages (Routes)

1. **Main Dashboard** (`/`) — Jira metrics, throughput, velocity, productivity charts, KPI cards
2. **Activity Heatmap** (`/activity/jira`) — Jira activity tracking and heatmap visualization
3. **Team Performance** (`/pap-indicators`) — PAP indicators (radar chart, merge requests, comments, status)

## Authentication

- **Jira Cloud:** Basic Auth (email + API token)
- **Jira Data Center:** Bearer Token (Personal Access Token)
- **Internal API:** JWT via python-jose + bcrypt password hashing
- Auth type is configured via `JIRA_AUTH_TYPE` environment variable

## Testing

- **Backend:** `cd jira-dashboard/backend && pytest` (pytest + pytest-asyncio)
- **Frontend:** `cd jira-dashboard/frontend && npm test` (Jest + Testing Library)
- Always run tests before submitting changes

## Common Tasks for AI Assistants

### Adding a new chart
1. Create component in `frontend/src/components/Charts/`
2. Add TypeScript types in `frontend/src/types/index.ts`
3. Add API call in `frontend/src/services/api.ts`
4. Wire into `Dashboard.tsx` or create a new route in `App.tsx`

### Adding a new API endpoint
1. Create route handler in `backend/app/api/`
2. Add Pydantic schemas in `backend/app/schemas.py`
3. Add service logic in `backend/app/services/`
4. Register router in `backend/app/api/__init__.py`
5. Add corresponding frontend API call in `frontend/src/services/api.ts`

### Adding a new database model
1. Define model in `backend/app/models.py`
2. Generate migration: `alembic revision --autogenerate -m "add model"`
3. Apply migration: `alembic upgrade head`
4. Add Pydantic schema in `backend/app/schemas.py`

### Modifying Jira sync logic
- Sync logic lives in `backend/app/api/jira_sync.py`
- Jira API calls go through `backend/app/jira_client.py`
- Field mapping and data transformation happen in the sync endpoint
