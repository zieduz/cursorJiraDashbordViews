import React from 'react';
import Dashboard from './components/Dashboard';
import ActivityDashboard from './components/ActivityHeatmap/ActivityDashboard';
import PAPIndicatorsDashboard from './components/PAPIndicators/PAPIndicatorsDashboard';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import './App.css';

function App() {
  return (
    <Router>
      <div className="App">
        <nav className="bg-white shadow-sm border-b">
          <div className="container mx-auto px-4">
            <div className="flex items-center h-16 space-x-8">
              <Link to="/" className="font-semibold text-gray-900">
                Jira Dashboard
              </Link>
              <Link to="/activity/jira" className="text-gray-600 hover:text-gray-900">
                Jira Activity
              </Link>
              <Link to="/pap-indicators" className="text-gray-600 hover:text-gray-900">
                Team Performance
              </Link>
            </div>
          </div>
        </nav>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/activity/jira" element={<ActivityDashboard />} />
          <Route path="/pap-indicators" element={<PAPIndicatorsDashboard />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
