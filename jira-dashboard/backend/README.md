# Backend API - Jira Performance Dashboard

FastAPI backend for the Jira Performance Dashboard application.

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 15+
- pip

### Installation

1. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Setup environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Setup database:**
   ```bash
   # Create tables
   python -c "from app.database import engine; from app.models import Base; Base.metadata.create_all(bind=engine)"
   ```

5. **Run the server:**
   ```bash
   uvicorn app.main:app --reload
   ```

## 📊 API Endpoints

### Metrics
- `GET /api/metrics` - Get comprehensive metrics
- `GET /api/metrics/summary` - Get quick metrics summary

### Forecast
- `GET /api/forecast` - Get velocity forecast
- `GET /api/forecast/sprint` - Get sprint-specific forecast

### Tickets
- `GET /api/tickets` - Get tickets with filters
- `GET /api/tickets/{id}` - Get specific ticket
- `GET /api/tickets/jira/{jira_id}` - Get ticket by Jira ID

### Health
- `GET /` - Root endpoint
- `GET /health` - Health check

## 🗄️ Database Schema

### Tables
- `projects` - Jira projects
- `users` - Jira users
- `tickets` - Jira tickets/issues
- `commits` - Git commits linked to tickets

### Models
- `Project` - Project information
- `User` - User information
- `Ticket` - Ticket/issue information
- `Commit` - Commit information

## 🔧 Configuration

### Environment Variables
- `DATABASE_URL` - PostgreSQL connection string
- `JIRA_BASE_URL` - Jira instance URL
- `JIRA_USERNAME` - Jira username
- `JIRA_API_TOKEN` - Jira API token
- `SECRET_KEY` - JWT secret key
- `CORS_ORIGINS` - Allowed CORS origins

## 🧪 Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test
pytest tests/test_metrics.py
```

## 📝 Development

### Code Style
- Use Black for formatting
- Use flake8 for linting
- Follow PEP 8 guidelines

### Database Migrations
```bash
# Generate migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head
```

## 🚀 Deployment

### Docker
```bash
docker build -t jira-dashboard-backend .
docker run -p 8000:8000 jira-dashboard-backend
```

### Production
- Use gunicorn for production
- Set up proper logging
- Configure reverse proxy (nginx)
- Use environment-specific settings