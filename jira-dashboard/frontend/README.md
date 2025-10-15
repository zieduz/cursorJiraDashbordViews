# Frontend - Jira Performance Dashboard

React frontend for the Jira Performance Dashboard application.

## 🚀 Quick Start

### Prerequisites
- Node.js 18+
- npm or yarn

### Installation

1. **Install dependencies:**
   ```bash
   npm install
   ```

2. **Setup environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your API URL
   ```

3. **Start development server:**
   ```bash
   npm start
   ```

4. **Open browser:**
   Navigate to http://localhost:3000

## 🏗️ Project Structure

```
src/
├── components/          # React components
│   ├── Charts/         # Chart components
│   ├── Dashboard.tsx   # Main dashboard
│   ├── Filters.tsx     # Filter controls
│   └── KPICard.tsx     # KPI display cards
├── services/           # API services
│   └── api.ts         # API client
├── types/             # TypeScript types
│   └── index.ts       # Type definitions
└── App.tsx            # Main app component
```

## 🎨 Components

### Dashboard
Main dashboard component with:
- KPI cards
- Charts and visualizations
- Filters
- Forecast summary

### Charts
- `ThroughputChart` - Ticket creation/resolution over time
- `VelocityChart` - Velocity forecast with confidence intervals
- `ProductivityChart` - User/project productivity
- `CommitsChart` - Commits per issue

### Filters
- Project selection
- User selection
- Status filtering
- Date range selection
- Quick filter buttons

## 🔧 Configuration

### Environment Variables
- `REACT_APP_API_URL` - Backend API URL

### API Integration
The frontend communicates with the backend through:
- REST API calls
- Axios for HTTP requests
- TypeScript interfaces for type safety

## 🧪 Testing

```bash
# Run tests
npm test

# Run tests with coverage
npm test -- --coverage

# Run tests in watch mode
npm test -- --watch
```

## 🏗️ Building

```bash
# Build for production
npm run build

# Analyze bundle size
npm run build && npx serve -s build
```

## 🚀 Deployment

### Docker
```bash
docker build -t jira-dashboard-frontend .
docker run -p 80:80 jira-dashboard-frontend
```

### Vercel
```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel --prod
```

### Netlify
```bash
# Build
npm run build

# Deploy to Netlify
# Upload build folder to Netlify
```

## 🎨 Styling

- **Tailwind CSS** for utility-first styling
- **Custom components** for reusable UI elements
- **Responsive design** for mobile and desktop
- **Dark mode support** (planned)

## 📱 Features

### Dashboard Features
- Real-time metrics display
- Interactive charts
- Advanced filtering
- Forecast visualization
- Responsive design

### Chart Types
- Line charts for trends
- Bar charts for comparisons
- Area charts for forecasts
- Responsive charts

## 🔧 Development

### Code Style
- ESLint for linting
- Prettier for formatting
- TypeScript for type safety

### State Management
- React hooks for local state
- Context API for global state (if needed)
- No external state management library

### Performance
- Code splitting
- Lazy loading
- Memoization where appropriate
- Optimized re-renders