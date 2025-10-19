# 🚀 Jira Performance Dashboard & Forecast

A full-stack application that connects to Jira REST API to visualize team performance and forecast future velocity using machine learning.

## 🧱 Architecture Overview

- **Frontend:** React + TypeScript + Tailwind CSS + Recharts
- **Backend:** FastAPI (Python) + SQLAlchemy + PostgreSQL
- **Database:** PostgreSQL
- **Auth:** OAuth2 (Jira API) + API Token support
- **ML:** Scikit-learn for velocity forecasting
- **Deployment:** Docker + Docker Compose

## 🔍 Core Features

### 1. Jira Integration
- Connect via API token or OAuth2
- Fetch data by project, filter, or sprint
- Real-time data synchronization

### 2. KPIs & Metrics
- Total tickets created/resolved/in progress (daily, weekly, monthly)
- Productivity per user and per project
- Ticket throughput over time
- Number of commits per Jira issue
- SLA compliance (% resolved on time)
- Average resolution time

### 3. Visualization
- Dynamic dashboard with filters (date range, user, project)
- Charts: Line, Bar, Donut, Heatmap
- KPI cards for quick overview
- Forecast graph with confidence intervals

### 4. Forecast Logic
- Linear regression for velocity prediction
- Confidence intervals for forecast accuracy
- Sprint-level predictions
- Trend analysis (increasing/decreasing/stable)

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Node.js 18+ (for local development)
- Python 3.11+ (for local development)

### Option 1: Docker Compose (Recommended)

1. **Clone and setup:**
   ```bash
   git clone <repository-url>
   cd jira-dashboard
   cp .env.example .env
   ```

2. **Configure environment:**
   Edit `.env` file with your Jira credentials:
   ```env
   JIRA_BASE_URL=https://your-domain.atlassian.net
   JIRA_USERNAME=your-email@example.com
   JIRA_API_TOKEN=your-api-token
   ```

3. **Start the application:**
   ```bash
   docker-compose up -d
   ```

4. **Access the application:**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### Option 2: Local Development

#### Backend Setup

1. **Navigate to backend:**
   ```bash
   cd backend
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Setup database:**
   ```bash
   # Start PostgreSQL (using Docker)
   docker run -d --name postgres -e POSTGRES_DB=jira_dashboard -e POSTGRES_USER=user -e POSTGRES_PASSWORD=password -p 5432:5432 postgres:15-alpine
   
   # Create tables
   python -c "from app.database import engine; from app.models import Base; Base.metadata.create_all(bind=engine)"

   # Optionally trigger an initial Jira sync (requires .env configured)
   # curl -X POST http://localhost:8000/api/jira/sync
   ```

5. **Start the backend:**
   ```bash
   uvicorn app.main:app --reload
   ```

#### Frontend Setup

1. **Navigate to frontend:**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Start the frontend:**
   ```bash
   npm start
   ```

## 📊 API Documentation

### Endpoints

#### Metrics
- `GET /api/metrics` - Get comprehensive metrics
- `GET /api/metrics/summary` - Get quick metrics summary

#### Forecast
- `GET /api/forecast` - Get velocity forecast
- `GET /api/forecast/sprint` - Get sprint-specific forecast

#### Tickets
- `GET /api/tickets` - Get tickets with filters
- `GET /api/tickets/{id}` - Get specific ticket
- `GET /api/tickets/jira/{jira_id}` - Get ticket by Jira ID

### Example API Response

#### Metrics Response
```json
{
  "total_tickets": 150,
  "tickets_created": 150,
  "tickets_resolved": 120,
  "tickets_in_progress": 25,
  "productivity_per_user": [
    {
      "user": "John Doe",
      "tickets_created": 30,
      "tickets_resolved": 28,
      "avg_story_points": 5.2,
      "avg_time_spent": 8.5
    }
  ],
  "productivity_per_project": [
    {
      "project": "E-commerce Platform",
      "tickets_created": 60,
      "tickets_resolved": 50,
      "avg_story_points": 4.8,
      "total_story_points": 288
    }
  ],
  "ticket_throughput": [
    {
      "date": "2024-01-01",
      "created": 5,
      "resolved": 3
    }
  ],
  "commits_per_issue": [
    {
      "ticket_id": "PROJ-123",
      "commit_count": 3
    }
  ],
  "sla_compliance": 85.5,
  "average_resolution_time": 24.5
}
```

#### Forecast Response
```json
{
  "predicted_velocity": [
    {
      "date": "2024-01-15",
      "velocity": 12.5
    }
  ],
  "confidence_interval": [
    {
      "date": "2024-01-15",
      "lower": 8.2,
      "upper": 16.8
    }
  ],
  "trend": "increasing",
  "next_sprint_prediction": {
    "velocity": 175.0,
    "confidence": 0.85,
    "days": 14
  },
  "model_accuracy": 0.85
}
```

## 🛠️ Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:password@localhost:5432/jira_dashboard` |
| `JIRA_BASE_URL` | Your Jira instance URL | Required |
| `JIRA_USERNAME` | Jira username/email | Required |
| `JIRA_API_TOKEN` | Jira API token | Required |
| `JIRA_CLIENT_ID` | OAuth2 client ID | Optional |
| `JIRA_CLIENT_SECRET` | OAuth2 client secret | Optional |
| `SECRET_KEY` | JWT secret key | Required |
| `CORS_ORIGINS` | Allowed CORS origins | `http://localhost:3000,http://localhost:5173` |

### Jira API Setup

1. **Generate API Token:**
   - Go to https://id.atlassian.com/manage-profile/security/api-tokens
   - Create a new API token
   - Copy the token to your `.env` file

2. **OAuth2 Setup (Optional):**
   - Create an OAuth2 app in your Jira instance
   - Set redirect URI to `http://localhost:3000/auth/callback`
   - Add client ID and secret to `.env`

## 🧪 Development

### Database Migrations

```bash
# Generate migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head
```

### Running Tests

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

### Code Quality

```bash
# Backend linting
cd backend
black .
flake8 .

# Frontend linting
cd frontend
npm run lint
```

## 🚀 Deployment

### Production Deployment

1. **Update environment variables for production**
2. **Build and deploy:**
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

### Vercel Deployment (Frontend)

1. **Install Vercel CLI:**
   ```bash
   npm i -g vercel
   ```

2. **Deploy:**
   ```bash
   cd frontend
   vercel --prod
   ```

### Render Deployment (Backend)

1. **Connect your repository to Render**
2. **Set environment variables**
3. **Deploy automatically on push**

## 📈 Features Roadmap

- [ ] Real-time Jira webhook integration
- [ ] Advanced forecasting models (ARIMA, LSTM)
- [ ] Team capacity planning
- [ ] Burndown charts
- [ ] Custom report generation
- [ ] Slack/Teams integration
- [ ] Mobile app
- [ ] Advanced analytics and insights

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation:** Check this README and API docs at `/docs`
- **Issues:** Create an issue on GitHub
- **Discussions:** Use GitHub Discussions for questions

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) for the excellent Python web framework
- [React](https://reactjs.org/) for the frontend framework
- [Recharts](https://recharts.org/) for beautiful charts
- [Tailwind CSS](https://tailwindcss.com/) for styling
- [Atlassian Jira](https://www.atlassian.com/software/jira) for the project management platform