"""Forecast generation based on historical velocity time series."""
from sqlalchemy.orm import Session
from sqlalchemy import func, not_
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score
from ..models import Ticket
from .metrics_service import NON_RESOLVED_STATUSES


class ForecastService:
    """Generate velocity and sprint forecasts from historical ticket data."""
    def __init__(self, db: Session):
        self.db = db
    
    def get_forecast(self, days_ahead: int = 30, project_id: Optional[int] = None, 
                    user_id: Optional[int] = None) -> Dict:
        """Generate velocity forecast using linear regression"""
        
        # Get historical data
        historical_data = self._get_historical_velocity(days_back=90, project_id=project_id, user_id=user_id)
        
        if len(historical_data) < 7:  # Need at least a week of data
            return self._get_default_forecast(days_ahead)
        
        # Prepare data for regression
        df = pd.DataFrame(historical_data)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        
        # Create features (day of week, trend)
        df['day_of_week'] = df['date'].dt.dayofweek
        df['day_number'] = (df['date'] - df['date'].min()).dt.days
        
        # Use linear regression for velocity prediction
        X = df[['day_of_week', 'day_number']].values
        y = df['velocity'].values
        
        model = LinearRegression()
        model.fit(X, y)
        
        # Calculate R² score for confidence
        y_pred = model.predict(X)
        r2 = r2_score(y, y_pred)
        
        # Generate future predictions
        future_dates = []
        future_velocity = []
        confidence_intervals = []
        
        last_date = df['date'].max()
        
        for i in range(1, days_ahead + 1):
            future_date = last_date + timedelta(days=i)
            future_dates.append(future_date.strftime("%Y-%m-%d"))
            
            # Predict velocity
            day_of_week = future_date.weekday()
            day_number = (future_date - df['date'].min()).days
            
            predicted_velocity = model.predict([[day_of_week, day_number]])[0]
            future_velocity.append(max(0, predicted_velocity))  # Ensure non-negative
            
            # Calculate confidence interval (simplified)
            std_error = np.std(y - y_pred)
            confidence_interval = 1.96 * std_error  # 95% confidence
            confidence_intervals.append({
                "lower": max(0, predicted_velocity - confidence_interval),
                "upper": predicted_velocity + confidence_interval
            })
        
        # Determine trend
        recent_velocity = df['velocity'].tail(7).mean()
        older_velocity = df['velocity'].head(7).mean()
        
        if recent_velocity > older_velocity * 1.1:
            trend = "increasing"
        elif recent_velocity < older_velocity * 0.9:
            trend = "decreasing"
        else:
            trend = "stable"
        
        # Next sprint prediction (assuming 2-week sprints)
        next_sprint_days = min(14, days_ahead)
        next_sprint_velocity = sum(future_velocity[:next_sprint_days])
        
        return {
            "predicted_velocity": [
                {"date": date, "velocity": velocity} 
                for date, velocity in zip(future_dates, future_velocity)
            ],
            "confidence_interval": [
                {"date": date, "lower": ci["lower"], "upper": ci["upper"]}
                for date, ci in zip(future_dates, confidence_intervals)
            ],
            "trend": trend,
            "next_sprint_prediction": {
                "velocity": next_sprint_velocity,
                "confidence": r2,
                "days": next_sprint_days
            },
            "model_accuracy": r2
        }
    
    def _get_historical_velocity(self, days_back: int, project_id: Optional[int] = None, 
                               user_id: Optional[int] = None) -> List[Dict]:
        """Get historical velocity data (story points completed per day)"""
        
        # Base filters: consider done only when resolved_at is set AND
        # the current status is not in NON_RESOLVED_STATUSES
        filters = [
            Ticket.resolved_at.isnot(None),
            ~func.lower(Ticket.status).in_(list(NON_RESOLVED_STATUSES)),
        ]
        if project_id:
            filters.append(Ticket.project_id == project_id)
        if user_id:
            filters.append(Ticket.assignee_id == user_id)
        
        # Get daily velocity
        daily_velocity = []
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days_back)
        
        current_date = start_date
        while current_date <= end_date:
            next_date = current_date + timedelta(days=1)
            
            # Prefer sum of story points when present; otherwise fallback to ticket count
            sum_and_count = (
                self.db.query(
                    func.coalesce(func.sum(Ticket.story_points), 0).label("sp_sum"),
                    func.count(Ticket.id).label("resolved_count"),
                )
                .filter(
                    *filters,
                    Ticket.resolved_at >= current_date,
                    Ticket.resolved_at < next_date,
                )
                .first()
            )
            sp_sum = float(sum_and_count.sp_sum if sum_and_count and sum_and_count.sp_sum is not None else 0)
            resolved_count = int(sum_and_count.resolved_count if sum_and_count and sum_and_count.resolved_count is not None else 0)

            daily_value = sp_sum if sp_sum > 0 else float(resolved_count)
            
            daily_velocity.append({
                "date": current_date.strftime("%Y-%m-%d"),
                "velocity": daily_value,
            })
            
            current_date = next_date
        
        return daily_velocity
    
    def _get_default_forecast(self, days_ahead: int) -> Dict:
        """Return default forecast when insufficient historical data"""
        future_dates = []
        for i in range(1, days_ahead + 1):
            future_date = datetime.now(timezone.utc) + timedelta(days=i)
            future_dates.append(future_date.strftime("%Y-%m-%d"))
        
        return {
            "predicted_velocity": [
                {"date": date, "velocity": 0} for date in future_dates
            ],
            "confidence_interval": [
                {"date": date, "lower": 0, "upper": 0} for date in future_dates
            ],
            "trend": "unknown",
            "next_sprint_prediction": {
                "velocity": 0,
                "confidence": 0,
                "days": min(14, days_ahead)
            },
            "model_accuracy": 0
        }
    
    def get_sprint_forecast(self, sprint_length_days: int = 14, 
                          project_id: Optional[int] = None) -> Dict:
        """Get forecast for next sprint specifically"""
        forecast = self.get_forecast(sprint_length_days, project_id)
        
        return {
            "sprint_length_days": sprint_length_days,
            "predicted_story_points": forecast["next_sprint_prediction"]["velocity"],
            "confidence": forecast["next_sprint_prediction"]["confidence"],
            "trend": forecast["trend"],
            "daily_breakdown": forecast["predicted_velocity"][:sprint_length_days]
        }