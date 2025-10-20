# Enhanced Activity Heatmap Design for Jira Dashboard

## Executive Summary

This design extends the existing Jira Performance Dashboard with activity heatmap visualizations for both Jira and GitLab. The enhancement maintains architectural consistency with the current application while adding powerful time-based activity analysis capabilities.

## Architecture Integration

### Backend Architecture Extensions

#### 1. New Database Tables

```sql
-- Core activity events table
CREATE TABLE activity_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source activity_source_enum NOT NULL, -- 'jira' | 'gitlab'
    event_type activity_event_enum NOT NULL,
    occurred_at_utc TIMESTAMP WITH TIME ZONE NOT NULL,
    
    -- Foreign keys to existing tables
    project_id INTEGER REFERENCES projects(id),
    user_id INTEGER REFERENCES users(id),
    ticket_id INTEGER REFERENCES tickets(id),
    
    -- GitLab-specific dimensions
    gitlab_project_id INTEGER,
    branch_name VARCHAR(255),
    mr_iid INTEGER,
    commit_sha VARCHAR(40),
    
    -- Actor information
    actor_user_id INTEGER REFERENCES users(id),
    actor_display_name VARCHAR(200),
    team_id INTEGER REFERENCES teams(id),
    
    -- Flexible metadata
    metadata JSONB DEFAULT '{}',
    
    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- High-performance aggregated data
CREATE TABLE activity_agg_hourly (
    id BIGSERIAL PRIMARY KEY,
    source activity_source_enum NOT NULL,
    event_type activity_event_enum NOT NULL,
    project_id INTEGER REFERENCES projects(id),
    branch_name VARCHAR(255),
    team_id INTEGER REFERENCES teams(id),
    date DATE NOT NULL,
    hour SMALLINT NOT NULL CHECK (hour >= 0 AND hour <= 23),
    day_of_week SMALLINT NOT NULL CHECK (day_of_week >= 0 AND day_of_week <= 6),
    event_count INTEGER NOT NULL DEFAULT 0,
    unique_users INTEGER NOT NULL DEFAULT 0,
    
    -- Ensure data consistency
    CONSTRAINT unique_activity_agg UNIQUE (source, event_type, project_id, branch_name, team_id, date, hour)
);

-- Teams table for user grouping
CREATE TABLE teams (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- User-team mapping
CREATE TABLE user_teams (
    user_id INTEGER REFERENCES users(id),
    team_id INTEGER REFERENCES teams(id),
    PRIMARY KEY (user_id, team_id)
);

-- GitLab integration configuration
CREATE TABLE gitlab_integrations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    base_url VARCHAR(500) NOT NULL,
    access_token_encrypted TEXT NOT NULL,
    webhook_secret VARCHAR(255),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Ingestion tracking
CREATE TABLE ingestion_cursors (
    id SERIAL PRIMARY KEY,
    source activity_source_enum NOT NULL,
    integration_id INTEGER,
    cursor_type VARCHAR(50) NOT NULL, -- 'timestamp' | 'sha' | 'id'
    cursor_value TEXT NOT NULL,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(source, integration_id, cursor_type)
);
```

#### 2. SQLAlchemy Models Extension

```python
# app/models.py additions

from enum import Enum
from sqlalchemy import Enum as SQLEnum, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB

class ActivitySource(str, Enum):
    JIRA = "jira"
    GITLAB = "gitlab"

class ActivityEventType(str, Enum):
    # Jira events
    JIRA_COMMENT = "jira_comment"
    JIRA_STATUS_CHANGE = "jira_status_change"
    
    # GitLab events
    GITLAB_COMMIT_CREATED = "gitlab_commit_created"
    GITLAB_MR_CREATED = "gitlab_mr_created"
    GITLAB_MR_APPROVED = "gitlab_mr_approved"
    GITLAB_MR_MERGED = "gitlab_mr_merged"

class Team(Base):
    __tablename__ = "teams"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), unique=True, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    users = relationship("User", secondary="user_teams", back_populates="teams")

class ActivityEvent(Base):
    __tablename__ = "activity_events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source = Column(SQLEnum(ActivitySource), nullable=False, index=True)
    event_type = Column(SQLEnum(ActivityEventType), nullable=False, index=True)
    occurred_at_utc = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # Relations to existing models
    project_id = Column(Integer, ForeignKey("projects.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    ticket_id = Column(Integer, ForeignKey("tickets.id"))
    
    # GitLab specific
    gitlab_project_id = Column(Integer)
    branch_name = Column(String(255))
    mr_iid = Column(Integer)
    commit_sha = Column(String(40))
    
    # Actor information
    actor_user_id = Column(Integer, ForeignKey("users.id"))
    actor_display_name = Column(String(200))
    team_id = Column(Integer, ForeignKey("teams.id"))
    
    metadata = Column(JSONB, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    project = relationship("Project", backref="activity_events")
    user = relationship("User", foreign_keys=[user_id], backref="activity_events")
    ticket = relationship("Ticket", backref="activity_events")
    actor = relationship("User", foreign_keys=[actor_user_id])
    team = relationship("Team", backref="activity_events")
    
    __table_args__ = (
        Index('idx_activity_events_composite', 'source', 'event_type', 'occurred_at_utc'),
        Index('idx_activity_events_gitlab', 'gitlab_project_id', 'branch_name', 'occurred_at_utc',
              postgresql_where=text("source = 'gitlab'")),
        Index('idx_activity_events_jira', 'ticket_id', 'occurred_at_utc',
              postgresql_where=text("source = 'jira'")),
    )

class ActivityAggHourly(Base):
    __tablename__ = "activity_agg_hourly"
    
    id = Column(BigInteger, primary_key=True)
    source = Column(SQLEnum(ActivitySource), nullable=False)
    event_type = Column(SQLEnum(ActivityEventType), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"))
    branch_name = Column(String(255))
    team_id = Column(Integer, ForeignKey("teams.id"))
    date = Column(Date, nullable=False)
    hour = Column(SmallInteger, nullable=False)
    day_of_week = Column(SmallInteger, nullable=False)
    event_count = Column(Integer, nullable=False, default=0)
    unique_users = Column(Integer, nullable=False, default=0)
    
    __table_args__ = (
        UniqueConstraint('source', 'event_type', 'project_id', 'branch_name', 
                        'team_id', 'date', 'hour', name='unique_activity_agg'),
        Index('idx_activity_agg_lookup', 'source', 'date', 'hour'),
    )
```

#### 3. New API Endpoints

```python
# app/api/activity.py

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional, Dict
from datetime import datetime, timezone
import pytz

router = APIRouter(prefix="/api/analytics", tags=["activity"])

@router.get("/jira/activity/heatmap")
async def get_jira_activity_heatmap(
    projects: List[int] = Query(default=[]),
    event_types: List[str] = Query(default=["jira_comment", "jira_status_change"]),
    assignees: List[int] = Query(default=[]),
    teams: List[int] = Query(default=[]),
    start_date: datetime = Query(...),
    end_date: datetime = Query(...),
    timezone: str = Query(default="UTC"),
    normalize: bool = Query(default=False),
    db: Session = Depends(get_db)
) -> Dict:
    """
    Get Jira activity heatmap data.
    Returns a 7x24 matrix of activity counts.
    """
    try:
        tz = pytz.timezone(timezone)
    except:
        raise HTTPException(400, "Invalid timezone")
    
    # Build query with filters
    query = db.query(
        func.extract('dow', func.timezone(timezone, ActivityEvent.occurred_at_utc)).label('dow'),
        func.extract('hour', func.timezone(timezone, ActivityEvent.occurred_at_utc)).label('hour'),
        func.count(ActivityEvent.id).label('count')
    ).filter(
        ActivityEvent.source == ActivitySource.JIRA,
        ActivityEvent.event_type.in_(event_types),
        ActivityEvent.occurred_at_utc >= start_date,
        ActivityEvent.occurred_at_utc <= end_date
    )
    
    if projects:
        query = query.filter(ActivityEvent.project_id.in_(projects))
    if assignees:
        query = query.filter(ActivityEvent.user_id.in_(assignees))
    if teams:
        query = query.filter(ActivityEvent.team_id.in_(teams))
    
    results = query.group_by('dow', 'hour').all()
    
    # Build 7x24 matrix
    matrix = [[0 for _ in range(24)] for _ in range(7)]
    total_count = 0
    
    for row in results:
        dow = int(row.dow)
        hour = int(row.hour)
        count = row.count
        matrix[dow][hour] = count
        total_count += count
    
    # Normalize if requested
    if normalize and total_count > 0:
        matrix = [[cell / total_count for cell in row] for row in matrix]
    
    return {
        "matrix": matrix,
        "total_events": total_count,
        "timezone": timezone,
        "filters": {
            "projects": projects,
            "event_types": event_types,
            "assignees": assignees,
            "teams": teams,
            "date_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            }
        }
    }

@router.get("/gitlab/activity/heatmap")
async def get_gitlab_activity_heatmap(
    projects: List[int] = Query(default=[]),
    branches: List[str] = Query(default=[]),
    branch_globs: List[str] = Query(default=[]),
    event_types: List[str] = Query(default=[
        "gitlab_commit_created", 
        "gitlab_mr_created",
        "gitlab_mr_approved",
        "gitlab_mr_merged"
    ]),
    start_date: datetime = Query(...),
    end_date: datetime = Query(...),
    timezone: str = Query(default="UTC"),
    normalize: bool = Query(default=False),
    db: Session = Depends(get_db)
) -> Dict:
    """
    Get GitLab activity heatmap data.
    Similar structure to Jira heatmap but with GitLab-specific filters.
    """
    # Implementation similar to Jira endpoint but with GitLab filters
    pass

@router.get("/{source}/activity/histogram")
async def get_activity_histogram(
    source: str,
    dimension: str = Query(..., regex="^(hour|dow)$"),
    # ... other query parameters
    db: Session = Depends(get_db)
) -> Dict:
    """Get activity histogram by hour of day or day of week."""
    pass
```

#### 4. Background Services

```python
# app/services/activity_ingestion.py

import asyncio
from datetime import datetime, timedelta
from typing import List, Optional
import httpx
from sqlalchemy.orm import Session

class ActivityIngestionService:
    """Orchestrates activity data ingestion from multiple sources."""
    
    def __init__(self, db: Session):
        self.db = db
        self.jira_service = JiraActivityIngestion(db)
        self.gitlab_service = GitLabActivityIngestion(db)
    
    async def run_ingestion_cycle(self):
        """Run a complete ingestion cycle for all sources."""
        tasks = []
        
        # Run Jira ingestion if configured
        if settings.jira_base_url:
            tasks.append(self.jira_service.ingest())
        
        # Run GitLab ingestion for each configured integration
        gitlab_integrations = self.db.query(GitLabIntegration).filter_by(is_active=True).all()
        for integration in gitlab_integrations:
            tasks.append(self.gitlab_service.ingest(integration))
        
        if tasks:
            await asyncio.gather(*tasks)

class JiraActivityIngestion:
    """Ingests Jira activity events."""
    
    async def ingest(self):
        """Ingest Jira comments and status changes."""
        cursor = self._get_cursor()
        
        # Fetch issues updated since cursor
        jql = f"updated >= '{cursor}' ORDER BY updated ASC"
        issues = await self._fetch_issues_with_changelog(jql)
        
        events = []
        for issue in issues:
            # Extract comment events
            for comment in issue.get('fields', {}).get('comment', {}).get('comments', []):
                events.append(self._create_comment_event(issue, comment))
            
            # Extract status change events from changelog
            for history in issue.get('changelog', {}).get('histories', []):
                for item in history.get('items', []):
                    if item.get('field') == 'status':
                        events.append(self._create_status_change_event(issue, history, item))
        
        # Bulk insert events
        if events:
            self.db.bulk_insert_mappings(ActivityEvent, events)
            self.db.commit()
            
            # Update cursor
            self._update_cursor(max(e['occurred_at_utc'] for e in events))

class GitLabActivityIngestion:
    """Ingests GitLab activity events."""
    
    async def ingest(self, integration: GitLabIntegration):
        """Ingest GitLab commits and MR events."""
        # Similar pattern to Jira ingestion
        pass

# app/services/activity_aggregation.py

class ActivityAggregationService:
    """Maintains materialized aggregates for performance."""
    
    async def refresh_aggregates(self, since: Optional[datetime] = None):
        """Incrementally refresh hourly aggregates."""
        if not since:
            since = datetime.utcnow() - timedelta(hours=24)
        
        # Delete stale aggregates
        self.db.query(ActivityAggHourly).filter(
            ActivityAggHourly.date >= since.date()
        ).delete()
        
        # Rebuild aggregates from raw events
        query = """
        INSERT INTO activity_agg_hourly (
            source, event_type, project_id, branch_name, team_id,
            date, hour, day_of_week, event_count, unique_users
        )
        SELECT 
            source,
            event_type,
            project_id,
            branch_name,
            team_id,
            DATE(occurred_at_utc) as date,
            EXTRACT(HOUR FROM occurred_at_utc) as hour,
            EXTRACT(DOW FROM occurred_at_utc) as day_of_week,
            COUNT(*) as event_count,
            COUNT(DISTINCT actor_user_id) as unique_users
        FROM activity_events
        WHERE occurred_at_utc >= :since
        GROUP BY 1, 2, 3, 4, 5, 6, 7, 8
        """
        
        self.db.execute(query, {"since": since})
        self.db.commit()
```

### Frontend Architecture Extensions

#### 1. New Components

```typescript
// src/components/ActivityHeatmap/HeatmapChart.tsx
import React from 'react';
import * as echarts from 'echarts';

interface HeatmapChartProps {
  data: number[][];
  timezone: string;
  normalized: boolean;
  onCellClick?: (day: number, hour: number) => void;
}

export const HeatmapChart: React.FC<HeatmapChartProps> = ({
  data,
  timezone,
  normalized,
  onCellClick
}) => {
  // ECharts heatmap implementation
  const options = {
    tooltip: {
      position: 'top',
      formatter: (params: any) => {
        const day = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'][params.data[1]];
        const hour = params.data[0];
        const value = params.data[2];
        return `${day} ${hour}:00 - ${normalized ? (value * 100).toFixed(1) + '%' : value + ' events'}`;
      }
    },
    grid: {
      height: '50%',
      top: '10%'
    },
    xAxis: {
      type: 'category',
      data: Array.from({ length: 24 }, (_, i) => i),
      splitArea: {
        show: true
      }
    },
    yAxis: {
      type: 'category',
      data: ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'],
      splitArea: {
        show: true
      }
    },
    visualMap: {
      min: 0,
      max: normalized ? 1 : Math.max(...data.flat()),
      calculable: true,
      orient: 'horizontal',
      left: 'center',
      bottom: '15%',
      color: ['#d94e5d', '#eac736', '#50a3ba'].reverse()
    },
    series: [{
      name: 'Activity',
      type: 'heatmap',
      data: data.flatMap((row, day) => 
        row.map((value, hour) => [hour, day, value])
      ),
      label: {
        show: false
      },
      emphasis: {
        itemStyle: {
          shadowBlur: 10,
          shadowColor: 'rgba(0, 0, 0, 0.5)'
        }
      }
    }]
  };
  
  return <div ref={chartRef} style={{ width: '100%', height: '400px' }} />;
};

// src/components/ActivityHeatmap/ActivityDashboard.tsx
import React, { useState, useEffect } from 'react';
import { HeatmapChart } from './HeatmapChart';
import { ActivityFilters } from './ActivityFilters';
import { useActivityData } from '../../hooks/useActivityData';

export const ActivityDashboard: React.FC<{ source: 'jira' | 'gitlab' }> = ({ source }) => {
  const [filters, setFilters] = useState<ActivityFilters>({
    eventTypes: source === 'jira' 
      ? ['jira_comment', 'jira_status_change']
      : ['gitlab_commit_created', 'gitlab_mr_created', 'gitlab_mr_approved', 'gitlab_mr_merged'],
    dateRange: {
      start: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000),
      end: new Date()
    },
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    normalize: false
  });
  
  const { data, loading, error } = useActivityData(source, filters);
  
  // Component implementation
};
```

#### 2. Router Integration

```typescript
// src/App.tsx modification
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import Dashboard from './components/Dashboard';
import { ActivityDashboard } from './components/ActivityHeatmap/ActivityDashboard';

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
              <Link to="/activity/gitlab" className="text-gray-600 hover:text-gray-900">
                GitLab Activity
              </Link>
            </div>
          </div>
        </nav>
        
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/activity/jira" element={<ActivityDashboard source="jira" />} />
          <Route path="/activity/gitlab" element={<ActivityDashboard source="gitlab" />} />
        </Routes>
      </div>
    </Router>
  );
}
```

## Key Enhancements Over Original Design

### 1. **Seamless Integration**
- Extends existing SQLAlchemy models and relationships
- Reuses authentication and configuration patterns
- Maintains consistent API structure and error handling
- Integrates with existing frontend component library

### 2. **Performance Optimizations**
- Connection pooling for GitLab API calls
- Intelligent caching with Redis integration
- Optimized PostgreSQL indexes for heatmap queries
- React component memoization for large datasets

### 3. **Enhanced Security**
- Encrypted storage for GitLab tokens using existing patterns
- Row-level security consistent with current implementation
- Webhook signature verification
- API rate limiting per integration

### 4. **Improved UX Features**
- Real-time updates via WebSocket when available
- Drill-down from heatmap cells to detailed event lists
- Comparative views (this period vs last period)
- Custom work hours highlighting per team
- Mobile-responsive heatmap visualization

### 5. **Operational Excellence**
- Prometheus metrics for ingestion performance
- Structured logging following existing patterns
- Health checks for each integration
- Graceful degradation when services unavailable

### 6. **Data Quality**
- Deduplication strategies for webhook retries
- Data validation using Pydantic schemas
- Audit trail for all ingested events
- Configurable data retention policies

## Migration Strategy

### Phase 1: Database Setup (Week 1)
1. Create new tables via Alembic migration
2. Deploy ActivityEvent and aggregation models
3. Set up GitLab integration configuration UI

### Phase 2: Backend Services (Week 2-3)
1. Implement ingestion services with feature flags
2. Deploy API endpoints behind feature flag
3. Set up background tasks for aggregation
4. Configure webhooks for real-time updates

### Phase 3: Frontend Implementation (Week 3-4)
1. Build heatmap components with Storybook
2. Integrate with existing filter system
3. Add navigation and routing
4. Implement export functionality

### Phase 4: Testing & Rollout (Week 5)
1. Load testing with production-scale data
2. Security audit of new endpoints
3. Progressive rollout to beta users
4. Documentation and training

## Configuration Updates

```python
# Additional settings in app/config.py
class Settings(BaseSettings):
    # ... existing settings ...
    
    # Activity feature flags
    activity_heatmap_enabled: bool = False
    activity_ingestion_interval_minutes: int = 15
    activity_aggregation_interval_minutes: int = 5
    
    # GitLab settings
    gitlab_webhook_secret: str = ""
    gitlab_api_timeout_seconds: int = 30
    gitlab_max_concurrent_requests: int = 10
    
    # Performance settings
    activity_cache_ttl_seconds: int = 120
    activity_max_lookback_days: int = 90
    
    # Redis cache (optional)
    redis_url: Optional[str] = None
```

## Monitoring & Alerts

### Key Metrics
- Ingestion lag by source (target: < 5 minutes)
- API response time for heatmap queries (target: < 300ms cached, < 2s uncached)
- Failed webhook deliveries
- Data freshness per project/repository

### Alerts
- Ingestion failures lasting > 30 minutes
- Heatmap query performance degradation
- Webhook signature validation failures
- Abnormal activity patterns (configurable thresholds)

## Future Enhancements

1. **Machine Learning Integration**
   - Anomaly detection for unusual activity patterns
   - Predictive modeling for team capacity
   - Automated insights generation

2. **Advanced Visualizations**
   - Activity flow diagrams
   - Team collaboration networks
   - Cross-platform activity correlation

3. **Expanded Integrations**
   - GitHub support
   - Bitbucket support
   - Slack activity correlation
   - Calendar integration for meeting correlation

4. **Enterprise Features**
   - Multi-tenant support
   - Advanced access controls
   - Audit logging
   - SLA monitoring for activity response times

This enhanced design provides a robust, scalable, and user-friendly extension to the existing Jira Dashboard application while maintaining architectural consistency and operational excellence.