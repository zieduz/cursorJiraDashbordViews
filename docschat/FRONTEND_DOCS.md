# Frontend Documentation

This document describes the React components and visualization tools used in the Jira Dashboard.

## 1. Dashboards

### `Dashboard.tsx`
The main entry point for the application.
- **State**: Manages global filters (`projects`, `users`, `dates`), metrics data, and panel configuration.
- **Features**:
  - Displays KPI Cards (Total Tickets, Resolved, SLA).
  - Renders the main grid of charts.
  - Allows dynamic addition/removal of "Throughput Panels".
  - Triggering Jira Resync manually.

### `ActivityDashboard.tsx`
A dedicated view for the **GitLab Activity Heatmap**.
- **Visual**: 7x24 Grid (Days x Hours).
- **Filters**: Project, Assignee, Date Range.
- **Normalization**: Option to normalize values to 0-1 range relative to the max value.

### `PAPIndicatorsDashboard.tsx`
A dashboard for **Process & Performance Indicators**.
- **Visuals**:
  - Comments & Status Changes (Bar/Area charts).
  - MRs by Author.
  - Radar Chart for multi-dimensional comparison.
- **Purpose**: Compare "Individual Contributor" activity across Jira and GitLab.

---

## 2. Filters Component (`Filters.tsx`)
A reusable component for controlling dashboard data scope.
- **Inputs**:
  - **Projects** (Multi-select)
  - **Users** (Dropdown)
  - **Customers** (Multi-select)
  - **Labels** (Multi-select)
  - **Status** (Dropdown)
  - **Date Range** (Start/End)
  - **Granularity** (Day/Week/Month/Year)

---

## 3. Chart Components (Recharts Wrappers)

### `BurnChart.tsx`
- **Modes**:
  - **Burn-up**: Shows cumulative `Scope` (Created) vs `Completed` (Resolved) with an ideal trend line.
  - **Burn-down**: Shows `Remaining` work vs ideal path to zero.
- **Props**: `data`, `mode` ('burnup'|'burndown'), `totalScope`.

### `CFDChart.tsx`
- **Visual**: Stacked Area Chart.
- **Data**: Cumulative "Open" (WIP) and "Done".
- **Purpose**: Visualize flow stability and bottlenecks (widening gap = growing backlog).

### `ControlChart.tsx`
- **Visual**: Scatter Plot + Reference Lines (Avg, P85, P95).
- **Modes**: `cycle` (Started → Resolved) or `lead` (Created → Resolved).
- **Purpose**: Analyze process stability and outliers.

### `ThroughputChart.tsx`
- **Visual**: Line Chart.
- **Metrics**: Created vs Resolved counts over time.
- **Features**:
  - Optional Moving Average (SMA/EMA).
  - Overlay mode to compare multiple series.

### `VelocityChart.tsx`
- **Visual**: Line/Area Chart.
- **Data**: Predicted velocity with optional Confidence Interval shading.

### `ProductivityChart.tsx`
- **Visual**: Bar Chart.
- **Data**: Created vs Resolved tickets per User or Project.

### `HeatmapChart.tsx`
- **Visual**: Custom CSS Grid (7 rows x 24 cols).
- **Data**: 2D array of counts.
- **Style**: Cells colored by intensity (opacity based on value).
