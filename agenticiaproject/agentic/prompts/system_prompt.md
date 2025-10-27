# System Prompt: Jira Authentication Implementation

## 🏗️ Project Architecture

### Frontend Structure

**Technology Stack:**
- React 18.x with TypeScript
- Tailwind CSS for styling
- Axios for HTTP requests
- No existing routing solution (need to add React Router)

**Directory Structure:**
```
jira-dashboard/frontend/src/
├── App.tsx                 # Main app component (currently shows Dashboard directly)
├── components/
│   ├── Dashboard.tsx       # Main dashboard component
│   ├── Filters.tsx        # Filter controls
│   ├── KPICard.tsx        # KPI display cards
│   └── Charts/            # Various chart components
├── services/
│   └── api.ts             # API service layer using axios
├── types/
│   └── index.ts           # TypeScript type definitions
└── index.tsx              # React entry point
```

**Current State:**
- No authentication system exists
- App.tsx directly renders Dashboard component
- No routing implemented
- API calls use `http://localhost:8000` as base URL
- No state management library (uses React hooks)

### Backend Structure

**Technology Stack:**
- FastAPI (Python 3.11+)
- SQLAlchemy ORM with PostgreSQL
- Pydantic for data validation
- HTTPX for async HTTP requests

**Directory Structure:**
```
jira-dashboard/backend/app/
├── main.py                # FastAPI application entry point
├── config.py              # Configuration settings
├── database.py            # Database connection and session management
├── models.py              # SQLAlchemy ORM models
├── schemas.py             # Pydantic schemas for validation
├── jira_client.py         # Jira API client implementation
├── exceptions.py          # Custom exception classes
├── api/
│   ├── __init__.py        # API router aggregation
│   ├── projects.py        # Projects endpoints
│   ├── tickets.py         # Tickets endpoints
│   ├── metrics.py         # Metrics endpoints
│   ├── forecast.py        # Forecast endpoints
│   ├── filters.py         # Filter options endpoints
│   └── jira_sync.py       # Jira synchronization endpoints
└── services/
    ├── forecast_service.py
    └── metrics_service.py
```

**Current Authentication:**
```python
# app/config.py
class Settings(BaseSettings):
    jira_base_url: str
    jira_username: str
    jira_api_token: str
    # ... other settings
```

**JiraClient Class** (`app/jira_client.py`):
- Initialized with credentials from environment variables
- Supports basic auth (username + API token)
- Supports bearer token authentication
- Has built-in retry logic and error handling
- Methods: `_make_request()`, `get_projects()`, `get_project_issues()`, etc.

## 📝 Implementation Plan

### Phase 1: Backend Authentication System

#### 1.1 Create Authentication Models

**File: `app/models.py`** (add to existing models)

```python
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from datetime import datetime

class UserSession(Base):
    __tablename__ = "user_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_token = Column(String, unique=True, index=True, nullable=False)
    jira_base_url = Column(String, nullable=False)
    jira_username = Column(String, nullable=False)
    jira_api_token_encrypted = Column(String, nullable=False)  # Encrypted token
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    last_activity = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    user_agent = Column(String, nullable=True)
    ip_address = Column(String, nullable=True)
```

#### 1.2 Create Authentication Schemas

**File: `app/schemas.py`** (add to existing schemas)

```python
from pydantic import BaseModel, Field, validator
from datetime import datetime

class LoginRequest(BaseModel):
    jira_base_url: str = Field(..., description="Jira instance base URL")
    username: str = Field(..., description="Jira username or email")
    api_token: str = Field(..., description="Jira API token")
    remember_me: bool = Field(default=False)
    
    @validator('jira_base_url')
    def validate_url(cls, v):
        if not v.startswith(('http://', 'https://')):
            raise ValueError('URL must start with http:// or https://')
        return v.rstrip('/')
    
    @validator('username')
    def validate_username(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Username cannot be empty')
        return v.strip()

class LoginResponse(BaseModel):
    success: bool
    session_token: str
    expires_at: datetime
    user_info: dict
    message: str = "Authentication successful"

class AuthError(BaseModel):
    success: bool = False
    error: str
    error_type: str  # 'invalid_credentials', 'network_error', 'invalid_url', etc.
    detail: Optional[dict] = None

class SessionVerifyResponse(BaseModel):
    valid: bool
    user_info: Optional[dict] = None
    expires_at: Optional[datetime] = None
```

#### 1.3 Create Authentication Endpoints

**File: `app/api/auth.py`** (new file)

```python
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import secrets
from cryptography.fernet import Fernet
import httpx
from ..database import get_db
from ..models import UserSession
from ..schemas import LoginRequest, LoginResponse, AuthError, SessionVerifyResponse
from ..jira_client import JiraClient
from ..config import settings
import logging

router = APIRouter(prefix="/api/auth", tags=["authentication"])
logger = logging.getLogger(__name__)

# Encryption key for storing API tokens (should be in environment)
ENCRYPTION_KEY = settings.encryption_key.encode()  # Add to config
cipher_suite = Fernet(ENCRYPTION_KEY)

def encrypt_token(token: str) -> str:
    """Encrypt API token for storage"""
    return cipher_suite.encrypt(token.encode()).decode()

def decrypt_token(encrypted_token: str) -> str:
    """Decrypt API token"""
    return cipher_suite.decrypt(encrypted_token.encode()).decode()

@router.post("/login", response_model=LoginResponse)
async def login(
    login_data: LoginRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Authenticate user with Jira credentials.
    Validates credentials by making a test API call.
    """
    try:
        # Create temporary JiraClient to verify credentials
        # Note: JiraClient needs to be modified to accept runtime credentials
        test_client = JiraClient(
            base_url=login_data.jira_base_url,
            username=login_data.username,
            api_token=login_data.api_token
        )
        
        # Verify credentials by fetching user info
        async with test_client:
            try:
                # Test API call - fetch current user or projects
                user_info = await test_client._make_request("myself")
            except Exception as e:
                logger.warning(f"Authentication failed for {login_data.username}: {e}")
                raise HTTPException(
                    status_code=401,
                    detail={
                        "error": "Invalid credentials or Jira URL",
                        "error_type": "invalid_credentials"
                    }
                )
        
        # Generate session token
        session_token = secrets.token_urlsafe(32)
        
        # Encrypt API token
        encrypted_token = encrypt_token(login_data.api_token)
        
        # Calculate expiration
        expiration_hours = 24 if not login_data.remember_me else 720  # 30 days
        expires_at = datetime.utcnow() + timedelta(hours=expiration_hours)
        
        # Invalidate old sessions for this user
        db.query(UserSession).filter(
            UserSession.jira_username == login_data.username,
            UserSession.jira_base_url == login_data.jira_base_url
        ).update({"is_active": False})
        
        # Create new session
        session = UserSession(
            session_token=session_token,
            jira_base_url=login_data.jira_base_url,
            jira_username=login_data.username,
            jira_api_token_encrypted=encrypted_token,
            expires_at=expires_at,
            user_agent=request.headers.get("user-agent"),
            ip_address=request.client.host
        )
        db.add(session)
        db.commit()
        
        logger.info(f"User authenticated successfully: {login_data.username}")
        
        return LoginResponse(
            success=True,
            session_token=session_token,
            expires_at=expires_at,
            user_info={
                "username": login_data.username,
                "display_name": user_info.get("displayName", login_data.username),
                "email": user_info.get("emailAddress"),
                "avatar_url": user_info.get("avatarUrls", {}).get("48x48")
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Authentication service error",
                "error_type": "server_error"
            }
        )

@router.post("/logout")
async def logout(
    request: Request,
    db: Session = Depends(get_db)
):
    """Invalidate current session"""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    session_token = auth_header.replace("Bearer ", "")
    
    # Invalidate session
    session = db.query(UserSession).filter(
        UserSession.session_token == session_token,
        UserSession.is_active == True
    ).first()
    
    if session:
        session.is_active = False
        db.commit()
    
    return {"success": True, "message": "Logged out successfully"}

@router.get("/verify", response_model=SessionVerifyResponse)
async def verify_session(
    request: Request,
    db: Session = Depends(get_db)
):
    """Verify if current session is valid"""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return SessionVerifyResponse(valid=False)
    
    session_token = auth_header.replace("Bearer ", "")
    
    session = db.query(UserSession).filter(
        UserSession.session_token == session_token,
        UserSession.is_active == True,
        UserSession.expires_at > datetime.utcnow()
    ).first()
    
    if not session:
        return SessionVerifyResponse(valid=False)
    
    # Update last activity
    session.last_activity = datetime.utcnow()
    db.commit()
    
    return SessionVerifyResponse(
        valid=True,
        user_info={
            "username": session.jira_username,
            "jira_url": session.jira_base_url
        },
        expires_at=session.expires_at
    )

# Dependency to get current session
async def get_current_session(
    request: Request,
    db: Session = Depends(get_db)
) -> UserSession:
    """Dependency to verify and get current user session"""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    session_token = auth_header.replace("Bearer ", "")
    
    session = db.query(UserSession).filter(
        UserSession.session_token == session_token,
        UserSession.is_active == True,
        UserSession.expires_at > datetime.utcnow()
    ).first()
    
    if not session:
        raise HTTPException(status_code=401, detail="Session expired or invalid")
    
    # Update last activity
    session.last_activity = datetime.utcnow()
    db.commit()
    
    return session

def get_jira_client_for_session(session: UserSession) -> JiraClient:
    """Create JiraClient instance for a specific session"""
    decrypted_token = decrypt_token(session.jira_api_token_encrypted)
    return JiraClient(
        base_url=session.jira_base_url,
        username=session.jira_username,
        api_token=decrypted_token
    )
```

#### 1.4 Modify JiraClient

**File: `app/jira_client.py`** (modify `__init__`)

```python
class JiraClient:
    def __init__(self, base_url: str = None, username: str = None, api_token: str = None):
        """
        Initialize JiraClient with credentials.
        If not provided, falls back to settings (for backward compatibility).
        """
        # Use provided credentials or fall back to environment
        self.base_url = (self._clean_str(base_url or settings.jira_base_url)).rstrip("/")
        self.username = self._clean_str(username or settings.jira_username)
        self.api_token = self._clean_str(api_token or settings.jira_api_token)
        # ... rest of initialization
```

#### 1.5 Register Auth Router

**File: `app/api/__init__.py`** (modify)

```python
from fastapi import APIRouter
from .projects import router as projects_router
from .tickets import router as tickets_router
from .metrics import router as metrics_router
from .forecast import router as forecast_router
from .filters import router as filters_router
from .jira_sync import router as jira_sync_router
from .auth import router as auth_router  # Add this

api_router = APIRouter()

api_router.include_router(auth_router)  # Add this
api_router.include_router(projects_router)
api_router.include_router(tickets_router)
api_router.include_router(metrics_router)
api_router.include_router(forecast_router)
api_router.include_router(filters_router)
api_router.include_router(jira_sync_router)
```

#### 1.6 Protect Existing Endpoints

**Example: `app/api/projects.py`** (add authentication dependency)

```python
from fastapi import APIRouter, Depends
from ..api.auth import get_current_session, get_jira_client_for_session
from ..models import UserSession

router = APIRouter(prefix="/api/projects", tags=["projects"])

@router.get("/")
async def get_projects(
    session: UserSession = Depends(get_current_session)
):
    """Get all projects for authenticated user"""
    jira_client = get_jira_client_for_session(session)
    async with jira_client:
        projects = await jira_client.get_projects()
    return projects
```

#### 1.7 Update Configuration

**File: `app/config.py`** (add encryption key)

```python
class Settings(BaseSettings):
    # ... existing settings
    
    # Authentication encryption key (generate with: Fernet.generate_key())
    encryption_key: str = Field(
        default="",
        env="ENCRYPTION_KEY",
        description="Fernet encryption key for storing API tokens"
    )
    
    # Session settings
    session_expiry_hours: int = Field(default=24, env="SESSION_EXPIRY_HOURS")
    session_remember_me_hours: int = Field(default=720, env="SESSION_REMEMBER_ME_HOURS")
```

### Phase 2: Frontend Authentication UI

#### 2.1 Install Dependencies

**File: `package.json`** (add dependencies)

```bash
npm install react-router-dom @types/react-router-dom
```

#### 2.2 Create Authentication Context

**File: `src/contexts/AuthContext.tsx`** (new file)

```typescript
import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { apiService } from '../services/api';

interface User {
  username: string;
  display_name?: string;
  email?: string;
  avatar_url?: string;
}

interface AuthContextType {
  isAuthenticated: boolean;
  isLoading: boolean;
  user: User | null;
  sessionToken: string | null;
  login: (baseUrl: string, username: string, apiToken: string, rememberMe: boolean) => Promise<void>;
  logout: () => Promise<void>;
  error: string | null;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [user, setUser] = useState<User | null>(null);
  const [sessionToken, setSessionToken] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Check existing session on mount
  useEffect(() => {
    const checkSession = async () => {
      const storedToken = localStorage.getItem('jira_session_token');
      if (storedToken) {
        try {
          const response = await apiService.verifySession(storedToken);
          if (response.valid) {
            setIsAuthenticated(true);
            setSessionToken(storedToken);
            setUser(response.user_info);
          } else {
            localStorage.removeItem('jira_session_token');
          }
        } catch (err) {
          console.error('Session verification failed:', err);
          localStorage.removeItem('jira_session_token');
        }
      }
      setIsLoading(false);
    };

    checkSession();
  }, []);

  const login = async (
    baseUrl: string,
    username: string,
    apiToken: string,
    rememberMe: boolean
  ) => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await apiService.login({
        jira_base_url: baseUrl,
        username,
        api_token: apiToken,
        remember_me: rememberMe,
      });

      setSessionToken(response.session_token);
      setUser(response.user_info);
      setIsAuthenticated(true);
      
      // Store token
      localStorage.setItem('jira_session_token', response.session_token);
      
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail?.error || 
                          err.response?.data?.message ||
                          'Authentication failed. Please check your credentials.';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    try {
      if (sessionToken) {
        await apiService.logout(sessionToken);
      }
    } catch (err) {
      console.error('Logout error:', err);
    } finally {
      setIsAuthenticated(false);
      setUser(null);
      setSessionToken(null);
      localStorage.removeItem('jira_session_token');
    }
  };

  return (
    <AuthContext.Provider
      value={{
        isAuthenticated,
        isLoading,
        user,
        sessionToken,
        login,
        logout,
        error,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};
```

#### 2.3 Create Login Component

**File: `src/components/Login.tsx`** (new file)

```typescript
import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const Login: React.FC = () => {
  const [jiraUrl, setJiraUrl] = useState('https://');
  const [username, setUsername] = useState('');
  const [apiToken, setApiToken] = useState('');
  const [rememberMe, setRememberMe] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [errors, setErrors] = useState<{ [key: string]: string }>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  const { login, error: authError } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const from = (location.state as any)?.from?.pathname || '/dashboard';

  const validateForm = (): boolean => {
    const newErrors: { [key: string]: string } = {};

    if (!jiraUrl || jiraUrl === 'https://') {
      newErrors.jiraUrl = 'Jira URL is required';
    } else if (!jiraUrl.match(/^https?:\/\/.+/)) {
      newErrors.jiraUrl = 'Invalid URL format';
    }

    if (!username.trim()) {
      newErrors.username = 'Username/Email is required';
    }

    if (!apiToken.trim()) {
      newErrors.apiToken = 'API Token is required';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) return;

    setIsSubmitting(true);
    setErrors({});

    try {
      await login(jiraUrl, username, apiToken, rememberMe);
      navigate(from, { replace: true });
    } catch (err: any) {
      setErrors({ submit: err.message });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <div className="max-w-md w-full bg-white rounded-lg shadow-xl p-8">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-800 mb-2">
            Jira Performance Dashboard
          </h1>
          <p className="text-gray-600">Sign in with your Jira credentials</p>
        </div>

        {/* Error Message */}
        {(errors.submit || authError) && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md">
            <p className="text-sm text-red-600">{errors.submit || authError}</p>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Jira URL */}
          <div>
            <label htmlFor="jiraUrl" className="block text-sm font-medium text-gray-700 mb-1">
              Jira Base URL
            </label>
            <input
              type="text"
              id="jiraUrl"
              value={jiraUrl}
              onChange={(e) => setJiraUrl(e.target.value)}
              className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                errors.jiraUrl ? 'border-red-500' : 'border-gray-300'
              }`}
              placeholder="https://your-domain.atlassian.net"
            />
            {errors.jiraUrl && (
              <p className="mt-1 text-sm text-red-600">{errors.jiraUrl}</p>
            )}
          </div>

          {/* Username */}
          <div>
            <label htmlFor="username" className="block text-sm font-medium text-gray-700 mb-1">
              Username / Email
            </label>
            <input
              type="text"
              id="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                errors.username ? 'border-red-500' : 'border-gray-300'
              }`}
              placeholder="your-email@example.com"
              autoComplete="username"
            />
            {errors.username && (
              <p className="mt-1 text-sm text-red-600">{errors.username}</p>
            )}
          </div>

          {/* API Token */}
          <div>
            <label htmlFor="apiToken" className="block text-sm font-medium text-gray-700 mb-1">
              API Token
            </label>
            <div className="relative">
              <input
                type={showPassword ? 'text' : 'password'}
                id="apiToken"
                value={apiToken}
                onChange={(e) => setApiToken(e.target.value)}
                className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 pr-10 ${
                  errors.apiToken ? 'border-red-500' : 'border-gray-300'
                }`}
                placeholder="Enter your Jira API token"
                autoComplete="current-password"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700"
              >
                {showPassword ? '👁️' : '👁️‍🗨️'}
              </button>
            </div>
            {errors.apiToken && (
              <p className="mt-1 text-sm text-red-600">{errors.apiToken}</p>
            )}
            <p className="mt-1 text-xs text-gray-500">
              <a
                href="https://id.atlassian.com/manage-profile/security/api-tokens"
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 hover:underline"
              >
                Generate an API token
              </a>
            </p>
          </div>

          {/* Remember Me */}
          <div className="flex items-center">
            <input
              type="checkbox"
              id="rememberMe"
              checked={rememberMe}
              onChange={(e) => setRememberMe(e.target.checked)}
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            />
            <label htmlFor="rememberMe" className="ml-2 block text-sm text-gray-700">
              Remember me for 30 days
            </label>
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isSubmitting ? (
              <span className="flex items-center justify-center">
                <svg
                  className="animate-spin -ml-1 mr-3 h-5 w-5 text-white"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  ></circle>
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  ></path>
                </svg>
                Authenticating...
              </span>
            ) : (
              'Sign In'
            )}
          </button>
        </form>

        {/* Help Text */}
        <div className="mt-6 text-center">
          <p className="text-xs text-gray-500">
            Your credentials are securely encrypted and never stored in plain text.
          </p>
        </div>
      </div>
    </div>
  );
};

export default Login;
```

#### 2.4 Create Protected Route Component

**File: `src/components/ProtectedRoute.tsx`** (new file)

```typescript
import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

interface ProtectedRouteProps {
  children: React.ReactElement;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return children;
};

export default ProtectedRoute;
```

#### 2.5 Update App.tsx with Routing

**File: `src/App.tsx`** (replace entire file)

```typescript
import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import Login from './components/Login';
import Dashboard from './components/Dashboard';
import ProtectedRoute from './components/ProtectedRoute';
import './App.css';

function App() {
  return (
    <Router>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            }
          />
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </AuthProvider>
    </Router>
  );
}

export default App;
```

#### 2.6 Update API Service

**File: `src/services/api.ts`** (add authentication methods and interceptor)

```typescript
import axios, { AxiosError } from 'axios';
// ... existing imports

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 120000,
});

// Add request interceptor to include auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('jira_session_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Add response interceptor to handle 401 errors
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      // Clear token and redirect to login
      localStorage.removeItem('jira_session_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Add authentication methods to apiService
export const apiService = {
  // Authentication
  login: async (credentials: {
    jira_base_url: string;
    username: string;
    api_token: string;
    remember_me: boolean;
  }) => {
    const response = await api.post('/api/auth/login', credentials);
    return response.data;
  },

  logout: async (token: string) => {
    const response = await api.post('/api/auth/logout', null, {
      headers: { Authorization: `Bearer ${token}` },
    });
    return response.data;
  },

  verifySession: async (token: string) => {
    const response = await api.get('/api/auth/verify', {
      headers: { Authorization: `Bearer ${token}` },
    });
    return response.data;
  },

  // ... rest of existing methods
};
```

#### 2.7 Add Logout Button to Dashboard

**File: `src/components/Dashboard.tsx`** (add header with logout)

```typescript
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';

// At the beginning of Dashboard component:
const Dashboard: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header with logout */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-900">
            Jira Performance Dashboard
          </h1>
          <div className="flex items-center gap-4">
            {user && (
              <span className="text-sm text-gray-600">
                {user.display_name || user.username}
              </span>
            )}
            <button
              onClick={handleLogout}
              className="px-4 py-2 text-sm font-medium text-gray-700 hover:text-gray-900 hover:bg-gray-100 rounded-md transition-colors"
            >
              Logout
            </button>
          </div>
        </div>
      </header>

      {/* Rest of dashboard content */}
      {/* ... */}
    </div>
  );
};
```

## 🔒 Security Considerations

1. **Encryption**: Use Fernet (symmetric encryption) for storing API tokens
2. **Generate encryption key**: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`
3. **HTTPS**: Always use HTTPS in production
4. **HTTP-only cookies**: Consider using HTTP-only cookies instead of localStorage for extra security
5. **CSRF tokens**: Add CSRF protection for state-changing operations
6. **Rate limiting**: Implement rate limiting on login endpoint (use slowapi or similar)
7. **Session cleanup**: Add background task to cleanup expired sessions
8. **Input validation**: Validate and sanitize all inputs
9. **Logging**: Log authentication attempts without exposing credentials

## 📦 Additional Dependencies

**Backend:**
```bash
pip install cryptography python-jose[cryptography] passlib[bcrypt]
```

**Frontend:**
```bash
npm install react-router-dom @types/react-router-dom
```

## ✅ Testing Checklist

- [ ] Valid credentials authenticate successfully
- [ ] Invalid credentials show appropriate error
- [ ] Invalid Jira URL shows error
- [ ] Session persists after page refresh
- [ ] Session expires after timeout
- [ ] Logout clears session properly
- [ ] Protected routes redirect to login
- [ ] Deep links work after authentication
- [ ] Remember me extends session
- [ ] Token encryption/decryption works
- [ ] Multiple user sessions work independently
- [ ] Session cleanup removes old sessions
- [ ] API calls include authentication token
- [ ] 401 errors redirect to login
- [ ] Mobile responsive design works

## 🎯 Migration Notes

- Existing environment variable authentication still works (backward compatible)
- JiraClient accepts runtime credentials or falls back to environment
- Protected endpoints require session token
- Public endpoints (if any) should remain unprotected
- Database migration needed for UserSession table
