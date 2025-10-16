from pydantic_settings import BaseSettings
from typing import List
import os
import json


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://user:password@localhost:5432/jira_dashboard"
    
    # Jira API
    jira_base_url: str = "https://your-domain.atlassian.net"
    jira_username: str = ""
    jira_api_token: str = ""
    # Auth type preference. Tries configured, then falls back automatically on 401.
    # Options: 'basic' (email + API token) or 'bearer' (PAT for Server/DC)
    jira_auth_type: str = "basic"
    # Personal Access Token for Jira Server/Data Center (Authorization: Bearer)
    jira_bearer_token: str = ""
    jira_api_version: int = 3
    # Story points custom field key; override per instance if different
    jira_story_points_field: str = "customfield_10016"
    # Customer custom field key; override per instance if different
    jira_customer_field: str = "customfield_12567"
    # Debug flag to enable verbose Jira request logging
    jira_debug: bool = False

    # Jira performance settings
    # Max results per page for search queries (Jira Cloud caps at 100)
    jira_page_size: int = 100
    # Global concurrency limit for parallel Jira requests
    jira_concurrency: int = 6
    # Enable including changelog in search results (heavy payload)
    jira_include_changelog: bool = True
    # Enable including description field in search results (can be large)
    jira_include_description: bool = True
    # HTTP client behavior
    jira_http2: bool = True
    jira_timeout_connect_seconds: float = 5.0
    jira_timeout_read_seconds: float = 120.0
    jira_timeout_write_seconds: float = 30.0
    jira_timeout_pool_seconds: float = 5.0
    # Retry policy for transient failures / rate limits
    jira_retry_max_attempts: int = 4
    jira_retry_backoff_base_seconds: float = 0.5
    jira_retry_backoff_max_seconds: float = 8.0
    
    # OAuth2
    jira_client_id: str = ""
    jira_client_secret: str = ""
    jira_redirect_uri: str = "http://localhost:3000/auth/callback"
    
    # App Settings
    secret_key: str = "your-secret-key-here"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # CORS
    # Note: Avoid declaring List[str] field here to prevent pydantic_settings
    # from attempting JSON parsing on empty/invalid env values.
    # Use the computed property `cors_origins` instead.

    @property
    def cors_origins(self) -> List[str]:
        """Return CORS origins parsed from env var `CORS_ORIGINS`.

        Supports JSON array (e.g., '["http://a", "http://b"]'),
        comma-separated string (e.g., 'http://a,http://b'),
        single value, or empty/undefined which falls back to sensible defaults.
        """
        default_origins: List[str] = [
            "http://localhost:3000",
            "http://localhost:5173",
        ]

        raw = os.getenv("CORS_ORIGINS", "").strip()
        if not raw:
            return default_origins

        # Try JSON array first
        if raw.startswith("[") and raw.endswith("]"):
            try:
                parsed = json.loads(raw)
                if isinstance(parsed, list):
                    return [str(item).strip() for item in parsed if str(item).strip()]
            except Exception:
                # Fall back to CSV parsing if JSON is invalid
                pass

        # Fallback: CSV or single value
        if "," in raw:
            return [part.strip().strip('"').strip("'") for part in raw.split(",") if part.strip()]
        return [raw]

    @property
    def jira_project_keys(self) -> List[str]:
        """Return Jira project keys from env var `JIRA_PROJECT_KEYS`.

        Supports JSON array (e.g., '["PROJ", "OPS"]') or comma-separated values
        (e.g., 'PROJ,OPS'). Returns empty list if not configured.
        """
        raw = os.getenv("JIRA_PROJECT_KEYS", "").strip()
        if not raw:
            return []
        if raw.startswith("[") and raw.endswith("]"):
            try:
                parsed = json.loads(raw)
                if isinstance(parsed, list):
                    return [str(item).strip() for item in parsed if str(item).strip()]
            except Exception:
                pass
        return [part.strip().strip('"').strip("'") for part in raw.split(",") if part.strip()]

    @property
    def jira_created_since(self) -> str:
        """Return the default created-since date filter for Jira sync.

        Falls back to '2025-01-01' to match the requested behavior.
        """
        return os.getenv("JIRA_CREATED_SINCE", "2025-01-01")
    
    class Config:
        env_file = ".env"


settings = Settings()