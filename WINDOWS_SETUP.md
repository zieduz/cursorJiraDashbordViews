# 🪟 How to Start the Jira Dashboard Application on Windows

This guide will help you get the Jira Performance Dashboard running on a Windows environment.

## 📋 Prerequisites

Before starting, ensure you have the following installed on your Windows machine:

### 1. Docker Desktop for Windows
- Download from: https://www.docker.com/products/docker-desktop/
- Install Docker Desktop
- Make sure Docker Desktop is running (you'll see the Docker icon in your system tray)

### 2. Git for Windows (if cloning the repository)
- Download from: https://git-scm.com/download/win
- Or use GitHub Desktop: https://desktop.github.com/

### 3. Code Editor (Optional but recommended)
- Visual Studio Code: https://code.visualstudio.com/
- Or any editor of your choice

## 🚀 Quick Start (Recommended)

### Method 1: Using Command Prompt or PowerShell

1. **Open Command Prompt or PowerShell as Administrator**
   - Press `Win + X` and select "Command Prompt (Admin)" or "PowerShell (Admin)"

2. **Navigate to the project directory**
   ```cmd
   cd C:\path\to\your\jira-dashboard
   ```

3. **Create environment file**
   ```cmd
   copy .env.example .env
   ```

4. **Edit the .env file**
   - Open `.env` in any text editor (Notepad, VS Code, etc.)
   - Update with your Jira credentials:
   ```env
   JIRA_BASE_URL=https://your-domain.atlassian.net
   JIRA_USERNAME=your-email@example.com
   JIRA_API_TOKEN=your-api-token
   ```

5. **Start the application**
   ```cmd
   docker-compose up -d --build
   ```

6. **Wait for services to start** (about 30-60 seconds)

7. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### Method 2: Using Windows Subsystem for Linux (WSL2)

If you have WSL2 installed, you can use the Linux setup script:

1. **Open WSL2 terminal**
   ```bash
   wsl
   ```

2. **Navigate to the project**
   ```bash
   cd /mnt/c/path/to/your/jira-dashboard
   ```

3. **Make setup script executable and run**
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```

## 🔧 Detailed Setup Instructions

### Step 1: Get Your Jira API Token

1. Go to https://id.atlassian.com/manage-profile/security/api-tokens
2. Click "Create API token"
3. Give it a name (e.g., "Jira Dashboard")
4. Copy the generated token

### Step 2: Configure Environment Variables

Edit the `.env` file with your actual Jira credentials:

```env
# Database (keep as is for Docker setup)
DATABASE_URL=postgresql://user:password@localhost:5432/jira_dashboard

# Jira API (REQUIRED - update these)
JIRA_BASE_URL=https://yourcompany.atlassian.net
JIRA_USERNAME=your.email@company.com
JIRA_API_TOKEN=your-actual-api-token-here

# App Settings (keep defaults or customize)
SECRET_KEY=your-secret-key-here
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# Frontend
REACT_APP_API_URL=http://localhost:8000
```

### Step 3: Start the Application

**Option A: Using Docker Compose (Recommended)**
```cmd
docker-compose up -d --build
```

**Option B: Using Docker Compose with logs**
```cmd
docker-compose up --build
```
(This will show logs in the terminal - useful for debugging)

### Step 4: Verify Everything is Working

1. **Check if containers are running:**
   ```cmd
   docker-compose ps
   ```

2. **View logs if needed:**
   ```cmd
   docker-compose logs
   ```

3. **Access the application:**
   - Open your web browser
   - Go to http://localhost:3000
   - You should see the Jira Dashboard interface

## 🛠️ Troubleshooting

### Common Issues on Windows

**1. Docker Desktop not running**
- Make sure Docker Desktop is started
- Check the system tray for the Docker icon
- Restart Docker Desktop if needed

**2. Port already in use**
- If port 3000 or 8000 is already in use:
  ```cmd
  netstat -ano | findstr :3000
  netstat -ano | findstr :8000
  ```
- Kill the process using that port or change ports in docker-compose.yml

**3. Permission issues**
- Run Command Prompt or PowerShell as Administrator
- Make sure Docker Desktop has permission to access your drives

**4. Services won't start**
```cmd
# Check logs
docker-compose logs

# Restart everything
docker-compose down
docker-compose up -d --build
```

**5. Database connection issues**
```cmd
# Restart just the database
docker-compose restart postgres
```

**6. Frontend not loading**
- Check if backend is running on port 8000
- Verify CORS settings in the backend
- Check browser console for errors

### Reset Everything
If you encounter persistent issues:
```cmd
# Stop and remove everything
docker-compose down -v

# Remove all containers and images
docker system prune -a

# Start fresh
docker-compose up -d --build
```

## 📊 What You'll See

Once running, you'll have access to:

### Dashboard Features
- **KPI Cards:** Total tickets, resolution rate, SLA compliance
- **Charts:** Throughput trends, velocity forecasts, productivity metrics
- **Filters:** Filter by project, user, date range, status
- **Forecast:** ML-powered velocity predictions

### Sample Data
The application comes with 90 days of mock data including:
- 3 sample projects
- 5 users with varying productivity
- Realistic ticket and commit patterns

## 🎯 Next Steps

1. **Connect Real Jira Data:** Update `.env` with your actual Jira credentials
2. **Customize Metrics:** Modify the dashboard for your specific needs
3. **Deploy:** Consider deploying to a cloud service for team access

## 🆘 Getting Help

- **Check logs:** `docker-compose logs -f`
- **API Documentation:** http://localhost:8000/docs
- **Reset application:** `docker-compose down -v && docker-compose up -d --build`

## 📝 Windows-Specific Notes

- Use Command Prompt or PowerShell (not Git Bash for Docker commands)
- Make sure Docker Desktop is running before starting the application
- If you're behind a corporate firewall, you may need to configure Docker Desktop proxy settings
- Windows Defender might prompt you to allow Docker - make sure to allow it

---

**Happy Dashboarding on Windows! 🪟📊✨**