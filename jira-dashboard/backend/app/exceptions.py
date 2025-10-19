"""Custom exception classes for the Jira Dashboard API."""

from typing import Optional, Dict, Any
from fastapi import status


class JiraDashboardException(Exception):
    """Base exception for Jira Dashboard application errors."""
    
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.detail = detail or {}
        super().__init__(self.message)


class JiraConnectionError(JiraDashboardException):
    """Raised when unable to connect to Jira API."""
    
    def __init__(self, message: str = "Unable to connect to Jira API", detail: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail,
        )


class JiraAuthenticationError(JiraDashboardException):
    """Raised when Jira authentication fails."""
    
    def __init__(self, message: str = "Jira authentication failed", detail: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
        )


class JiraAPIError(JiraDashboardException):
    """Raised when Jira API returns an error."""
    
    def __init__(
        self,
        message: str = "Jira API error",
        status_code: int = status.HTTP_502_BAD_GATEWAY,
        detail: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            status_code=status_code,
            detail=detail,
        )


class DatabaseError(JiraDashboardException):
    """Raised when database operation fails."""
    
    def __init__(self, message: str = "Database operation failed", detail: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
        )


class ValidationError(JiraDashboardException):
    """Raised when input validation fails."""
    
    def __init__(self, message: str = "Validation error", detail: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
        )
