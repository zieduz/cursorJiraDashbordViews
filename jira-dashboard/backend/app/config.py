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
    # Auth type: 'basic' (username + password/token) or 'bearer' (PAT)
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

    # --- GitLab settings ---
    # Base URL of your GitLab instance, e.g. https://gitlab.com or https://gitlab.company.com
    gitlab_base_url: str = ""
    # Personal Access Token (PAT) or job token for GitLab API authentication
    gitlab_token: str = ""
    # Default lookback window (in days) when syncing GitLab activity, if not provided explicitly
    gitlab_default_since_days: int = 90
    # Concurrency and paging controls
    gitlab_concurrency: int = 6
    gitlab_page_size: int = 100

    @property
    def gitlab_project_ids(self) -> list[int]:
        """Return GitLab project IDs from env var `GITLAB_PROJECT_IDS`.

        Accepts JSON array (e.g., "[123, 456]") or comma-separated integers (e.g., "123,456").
        Returns an empty list when not configured or invalid.
        """
        raw = os.getenv("GITLAB_PROJECT_IDS", "").strip()
        if not raw:
            return []
        # JSON array first
        if raw.startswith("[") and raw.endswith("]"):
            try:
                parsed = json.loads(raw)
                if isinstance(parsed, list):
                    ids: list[int] = []
                    for item in parsed:
                        try:
                            ids.append(int(str(item).strip()))
                        except Exception:
                            # skip invalid items
                            continue
                    return [i for i in ids if i is not None]
            except Exception:
                pass
        # Fallback: CSV
        ids: list[int] = []
        for part in raw.split(","):
            p = part.strip().strip('"').strip("'")
            if not p:
                continue
            try:
                ids.append(int(p))
            except Exception:
                continue
        return ids

    @property
    def gitlab_branch_customer_map(self) -> dict[str, str]:
        """Return a mapping of branch-pattern => customer name from env `GITLAB_BRANCH_CUSTOMER_MAP`.

        Supports JSON object (e.g., '{"S9.1.X": "MAIF", "master": "Build"}') or
        CSV-style pairs (e.g., 'S9.1.X=MAIF,S9.2.X=CLV,master=Build').
        Returns an empty dict when not configured or invalid.
        """
        raw = os.getenv("GITLAB_BRANCH_CUSTOMER_MAP", "").strip()
        if not raw:
            return {}
        # JSON object
        if raw.startswith("{") and raw.endswith("}"):
            try:
                parsed = json.loads(raw)
                if isinstance(parsed, dict):
                    # Coerce keys/values to strings
                    out: dict[str, str] = {}
                    for k, v in parsed.items():
                        try:
                            key = str(k).strip()
                            val = str(v).strip()
                            if key and val:
                                out[key] = val
                        except Exception:
                            continue
                    return out
            except Exception:
                pass
        # Fallback: CSV pairs 'pattern=Customer'
        out: dict[str, str] = {}
        for pair in raw.split(","):
            if "=" not in pair:
                continue
            k, v = pair.split("=", 1)
            key = k.strip().strip('"').strip("'")
            val = v.strip().strip('"').strip("'")
            if key and val:
                out[key] = val
        return out
    
    class Config:
        env_file = ".env"


settings = Settings()