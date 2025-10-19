# 🚀 Quick Start Guide

Get the Jira Performance Dashboard running in 5 minutes!

## Prerequisites
- Docker and Docker Compose installed
- Basic understanding of Jira API

## Option 1: One-Command Setup (Recommended)

```bash
# Clone and setup
git clone <your-repo-url>
cd jira-dashboard

# Run setup script
./setup.sh
```

## Option 2: Manual Setup

### 1. Configure Environment
```bash
cp .env.example .env
# Edit .env with your Jira credentials
```

### 2. Start with Docker
```bash
docker-compose up -d --build
```

### 3. Access the Application
- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs

## 🎯 What You'll See

### Dashboard Features
- **KPI Cards:** Total tickets, resolution rate, SLA compliance
- **Charts:** Throughput trends, velocity forecasts, productivity metrics
- **Filters:** Filter by project, user, date range, status
- **Forecast:** ML-powered velocity predictions with confidence intervals

### Data Source
- Data is fetched from Jira via REST API using your credentials in `.env`
- Trigger a data sync with `POST /api/jira/sync` or rely on startup sync when configured

## 🔧 Configuration

### Jira API Setup
1. Get your Jira API token from https://id.atlassian.com/manage-profile/security/api-tokens
2. Update `.env` file:
   ```env
   JIRA_BASE_URL=https://your-domain.atlassian.net
   JIRA_USERNAME=your-email@example.com
   JIRA_API_TOKEN=your-api-token
   ```

### Customization
- Update `frontend/src/components/` for UI changes
- Adjust forecasting parameters in `backend/app/services/forecast_service.py`

## 🚨 Troubleshooting

### Common Issues

**Services won't start:**
```bash
docker-compose logs
```

**Database connection issues:**
```bash
docker-compose restart postgres
```

**Frontend not loading:**
- Check if backend is running on port 8000
- Verify CORS settings in backend

**No data showing:**
- Ensure Jira credentials are configured in `.env`
- Trigger a sync: `curl -X POST http://localhost:8000/api/jira/sync`
- Look at backend logs for errors

### Reset Everything
```bash
docker-compose down -v
docker-compose up -d --build
```

## 📊 Understanding the Data

### Metrics Explained
- **SLA Compliance:** Percentage of tickets resolved within 7 days
- **Velocity:** Story points completed per day
- **Throughput:** Tickets created vs resolved over time
- **Productivity:** User and project performance metrics

### Forecast Accuracy
- Model accuracy shows how well the forecast matches historical data
- Confidence intervals indicate forecast uncertainty
- Trend shows if velocity is increasing, decreasing, or stable

## 🎨 Customization

### Adding New Metrics
1. Update `backend/app/services/metrics_service.py`
2. Add new endpoint in `backend/app/api/metrics.py`
3. Create chart component in `frontend/src/components/Charts/`
4. Update dashboard in `frontend/src/components/Dashboard.tsx`

### Styling Changes
- Modify `frontend/tailwind.config.js` for theme changes
- Update component styles in `frontend/src/components/`
- Add new chart types using Recharts

## 🚀 Next Steps

1. **Connect Real Jira Data:** Update `.env` with your Jira credentials
2. **Customize Metrics:** Add project-specific KPIs
3. **Deploy:** Use Docker Compose or deploy to cloud
4. **Integrate:** Connect with Slack, Teams, or other tools

## 📚 Learn More

- [Full Documentation](README.md)
- [API Reference](http://localhost:8000/docs)
- [Backend README](backend/README.md)
- [Frontend README](frontend/README.md)

## 🆘 Need Help?

- Check the logs: `docker-compose logs -f`
- Review the API docs: http://localhost:8000/docs
- Create an issue on GitHub
- Check the troubleshooting section above

---

**Happy Dashboarding! 📊✨**