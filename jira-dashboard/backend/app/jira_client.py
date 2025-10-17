import httpx
import random
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import asyncio
import os
from .config import settings


class JiraClient:
    def __init__(self):
        # Ensure no trailing slash to avoid double slashes in URLs
        # Normalize and trim potentially messy env-provided values
        self.base_url = (self._clean_str(settings.jira_base_url)).rstrip("/")
        self.username = self._clean_str(settings.jira_username)
        self.api_token = self._clean_str(settings.jira_api_token)
        # Auth configuration
        self.auth_type = (self._clean_str(getattr(settings, "jira_auth_type", "basic")) or "basic").lower()
        self.bearer_token = self._clean_str(getattr(settings, "jira_bearer_token", ""))
        self.client_id = self._clean_str(settings.jira_client_id)
        self.client_secret = self._clean_str(settings.jira_client_secret)
        # Allow API version to be configured (e.g., 2 for Jira Server/DC)
        self.api_version = str(getattr(settings, "jira_api_version", 3))
        # Auto-detect Jira Data Center/Server and default to API v2 when not explicitly set
        try:
            api_version_env = (os.getenv("JIRA_API_VERSION") or "").strip()
        except Exception:
            api_version_env = ""
        if (
            not api_version_env
            and self.api_version == "3"
            and self.base_url
            and ("atlassian.net" not in self.base_url.lower())
        ):
            # Most Jira DC/Server instances require v2 endpoints
            self.api_version = "2"
            self._debug("Auto-selected Jira API v2 for Data Center/Server instance")
        # Instance-specific story points field (may differ from 10016)
        self.story_points_field = self._clean_str(getattr(settings, "jira_story_points_field", "customfield_10016")) or None
        # Instance-specific customer field (e.g., customfield_12567)
        self.customer_field = self._clean_str(getattr(settings, "jira_customer_field", "customfield_12567")) or None
        # Enable verbose debug logging via env (JIRA_DEBUG=true)
        self._debug_enabled = bool(getattr(settings, "jira_debug", False))
        # Shared HTTP client (lazy)
        self._client: Optional[httpx.AsyncClient] = None

    def _clean_str(self, value: Optional[str]) -> str:
        """Return a safely trimmed string without surrounding quotes.

        This prevents subtle 401s caused by pasted tokens/usernames that
        contain trailing spaces or accidental quote characters.
        """
        if value is None:
            return ""
        try:
            s = str(value).strip()
        except Exception:
            return ""
        if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
            s = s[1:-1].strip()
        return s

    async def __aenter__(self):
        if self._client is None:
            timeout = httpx.Timeout(
                connect=getattr(settings, "jira_timeout_connect_seconds", 5.0),
                read=getattr(settings, "jira_timeout_read_seconds", 120.0),
                write=getattr(settings, "jira_timeout_write_seconds", 30.0),
                pool=getattr(settings, "jira_timeout_pool_seconds", 5.0),
            )
            http2_enabled = bool(getattr(settings, "jira_http2", True))
            try:
                self._client = httpx.AsyncClient(timeout=timeout, http2=http2_enabled)
            except ImportError:
                # Gracefully fall back if HTTP/2 dependencies (h2) are missing
                self._debug("HTTP/2 dependencies missing; falling back to HTTP/1.1")
                self._client = httpx.AsyncClient(timeout=timeout, http2=False)
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if self._client is not None:
            try:
                await self._client.aclose()
            finally:
                self._client = None

    def _mask_value(self, value: Optional[str], show_start: int = 2, show_end: int = 2) -> str:
        """Return a masked representation of a potentially sensitive value."""
        if not value:
            return "<empty>"
        if len(value) <= show_start + show_end:
            return "*" * len(value)
        return f"{value[:show_start]}***{value[-show_end:]}"

    def _debug(self, message: str) -> None:
        if self._debug_enabled:
            print(f"[JiraDebug] {message}")
    
    def _extract_name(self, raw) -> str:
        """Return a readable name from Jira field values.

        Handles dicts with common keys (name/value/id) as well as primitives.
        Ensures a string is always returned even when the input is None.
        """
        if raw is None:
            return ""
        if isinstance(raw, dict):
            for key in ("name", "value", "id"):
                if key in raw and raw[key] is not None:
                    try:
                        s = str(raw[key]).strip()
                    except Exception:
                        s = ""
                    if s:
                        return s
            return ""
        try:
            return str(raw).strip()
        except Exception:
            return ""

    def _extract_customer_value(self, raw):
        """Return a string customer value from Jira custom field.

        Handles Jira option objects (dicts with 'value' or 'name'), plain
        strings, numeric IDs, or lists (uses the first non-empty value).
        """
        if raw is None:
            return None
        # Single select option returned as an object
        if isinstance(raw, dict):
            candidate = raw.get("value") or raw.get("name") or raw.get("id") or ""
            val = str(candidate).strip()
            return val or None
        # Multi-select could return a list of option objects; pick the first meaningful value
        if isinstance(raw, list):
            for item in raw:
                v = None
                if isinstance(item, dict):
                    candidate = item.get("value") or item.get("name") or item.get("id") or ""
                    v = str(candidate).strip()
                elif isinstance(item, str):
                    v = item.strip()
                else:
                    v = str(item).strip()
                if v:
                    return v
            return None
        if isinstance(raw, str):
            return raw.strip() or None
        # Fallback for numeric IDs or unexpected primitives
        try:
            return str(raw).strip() or None
        except Exception:
            return None
        
    async def _make_request(self, endpoint: str, params: Dict = None) -> Dict:
        """Make authenticated request to Jira API with retries, timeouts, and 401 auth fallback."""
        url = f"{self.base_url}/rest/api/{self.api_version}/{endpoint.lstrip('/')}"

        # Build auth candidates: try configured mode first, then fallback mode if available
        def build_auth_candidates() -> List[Tuple[str, Optional[Tuple[str, str]], Dict[str, str]]]:
            candidates: List[Tuple[str, Optional[Tuple[str, str]], Dict[str, str]]] = []
            # Some proxies/plugins behave better with an explicit UA and Atlassian header
            base_headers = {
                "Accept": "application/json",
                "User-Agent": "jira-dashboard-backend/1.0",
                # No harm for GET; avoids CSRF checks on some DC setups
                "X-Atlassian-Token": "no-check",
            }
            # Preferred (configured) mode first
            if self.auth_type == "bearer":
                if self.bearer_token:
                    headers = dict(base_headers)
                    headers["Authorization"] = f"Bearer {self.bearer_token}"
                    candidates.append(("bearer", None, headers))
                if self.username and self.api_token:
                    candidates.append(("basic", (self.username, self.api_token), dict(base_headers)))
            else:
                if self.username and self.api_token:
                    candidates.append(("basic", (self.username, self.api_token), dict(base_headers)))
                if self.bearer_token:
                    headers = dict(base_headers)
                    headers["Authorization"] = f"Bearer {self.bearer_token}"
                    candidates.append(("bearer", None, headers))
            # Ensure we try at least one candidate (even if misconfigured) to surface clear error
            if not candidates:
                candidates.append((self.auth_type or "basic", None, dict(base_headers)))
            return candidates

        auth_candidates = build_auth_candidates()

        # Pre-request debug logging (without exposing secrets)
        self._debug(
            "Config: base_url="
            + (self.base_url or "<unset>")
            + f", api_version={self.api_version}, story_points_field={self.story_points_field or '<none>'}"
        )
        self._debug(
            "Auth: candidates="
            + ", ".join([
                f"{mode}(configured={'yes' if ((mode=='bearer' and 'Authorization' in headers) or (mode=='basic' and auth is not None)) else 'no'})"
                for (mode, auth, headers) in auth_candidates
            ])
            + f", username_present={'yes' if bool(self.username) else 'no'}"
            + f", basic_token_present={'yes' if bool(self.api_token) else 'no'}"
            + f", bearer_present={'yes' if bool(self.bearer_token) else 'no'}"
            + (f", username_masked={self._mask_value(self.username)}" if self.username else "")
        )

        # Warn for likely misconfiguration: Jira DC often uses api v2
        if self.api_version == "3" and ("atlassian.net" not in (self.base_url or "")):
            self._debug("Warning: Using API v3 with non-Cloud base URL; Jira DC often requires v2")
        if params is not None:
            # Keep JQL visible for troubleshooting; truncate if extremely long
            jql_val = params.get("jql")
            if isinstance(jql_val, str) and len(jql_val) > 300:
                jql_preview = jql_val[:300] + "..."
            else:
                jql_preview = jql_val
            self._debug(
                f"Request: endpoint={endpoint}, url={url}, params_keys={list(params.keys())}, startAt={params.get('startAt')}, maxResults={params.get('maxResults')}, fields_len={len((params.get('fields') or '').split(',')) if params.get('fields') else 0}, jql={jql_preview}"
            )
        else:
            self._debug(f"Request: endpoint={endpoint}, url={url}, no params")

        # Ensure we have a client available
        client = self._client
        ephemeral_client: Optional[httpx.AsyncClient] = None
        if client is None:
            timeout = httpx.Timeout(
                connect=getattr(settings, "jira_timeout_connect_seconds", 5.0),
                read=getattr(settings, "jira_timeout_read_seconds", 120.0),
                write=getattr(settings, "jira_timeout_write_seconds", 30.0),
                pool=getattr(settings, "jira_timeout_pool_seconds", 5.0),
            )
            http2_enabled = bool(getattr(settings, "jira_http2", True))
            try:
                ephemeral_client = httpx.AsyncClient(timeout=timeout, http2=http2_enabled)
            except ImportError:
                self._debug("HTTP/2 dependencies missing; falling back to HTTP/1.1")
                ephemeral_client = httpx.AsyncClient(timeout=timeout, http2=False)
            client = ephemeral_client

        max_attempts = max(1, int(getattr(settings, "jira_retry_max_attempts", 4)))
        base_backoff = max(0.0, float(getattr(settings, "jira_retry_backoff_base_seconds", 0.5)))
        max_backoff = max(base_backoff, float(getattr(settings, "jira_retry_backoff_max_seconds", 8.0)))
        last_error: Optional[Exception] = None
        try:
            for idx, (mode, basic_auth, headers) in enumerate(auth_candidates, start=1):
                attempt = 0
                self._debug(f"Using auth candidate {idx}/{len(auth_candidates)}: mode={mode}")
                while attempt < max_attempts:
                    try:
                        response = await client.get(url, auth=basic_auth, params=params or {}, headers=headers)
                        response.raise_for_status()
                        self._debug(
                            f"Response: status={response.status_code}, url={str(response.request.url)}"
                        )
                        return response.json()
                    except httpx.HTTPStatusError as e:
                        status_code = e.response.status_code if e.response is not None else None
                        # If unauthorized/forbidden, try next auth candidate (single immediate fallback)
                        if status_code in (401, 403):
                            resp = e.response
                            req = resp.request if resp is not None else None
                            method = req.method if req is not None else "GET"
                            req_url = str(req.url) if req is not None else url
                            body_preview = (resp.text or "")[:500] if resp is not None else ""
                            logger.warning(
                                f"Jira API {method} {req_url} failed with {status_code}: {body_preview}"
                            )
                            self._debug(
                                f"Auth failure with mode={mode}; trying next candidate if available"
                            )
                            # Move to next auth candidate
                            last_error = e
                            break
                        # Retry on 429 (rate limit) and 5xx
                        should_retry = status_code in (429,) or (status_code is not None and 500 <= status_code < 600)
                        if not should_retry or attempt >= max_attempts - 1:
                            resp = e.response
                            req = resp.request if resp is not None else None
                            method = req.method if req is not None else "GET"
                            req_url = str(req.url) if req is not None else url
                            status = resp.status_code if resp is not None else "unknown"
                            body_preview = (resp.text or "")[:500] if resp is not None else ""
                            logger.error(f"Jira API {method} {req_url} failed with {status}: {body_preview}")
                            self._debug(
                                f"Failure details: base_url={self.base_url}, api_version={self.api_version}, auth_mode={mode}, auth_header={'yes' if 'Authorization' in headers else 'no'}"
                            )
                            raise JiraAPIError(
                                message=f"Jira API request failed with status {status}",
                                status_code=status if isinstance(status, int) else 502,
                                detail={
                                    "method": method,
                                    "url": req_url,
                                    "status": status,
                                    "response": body_preview,
                                }
                            )
                        # Compute backoff (respect Retry-After when present)
                        retry_after = 0.0
                        try:
                            header_val = e.response.headers.get("Retry-After") if e.response is not None else None
                            if header_val:
                                retry_after = float(header_val)
                        except Exception:
                            retry_after = 0.0
                        backoff = min(max_backoff, retry_after or (base_backoff * (2 ** attempt)))
                        backoff *= (0.5 + random.random())
                        self._debug(
                            f"Retrying {url} after {backoff:.2f}s (attempt {attempt+1}/{max_attempts})"
                        )
                        await asyncio.sleep(backoff)
                        attempt += 1
                        last_error = e
                    except (httpx.TimeoutException, httpx.RequestError) as e:
                        if attempt >= max_attempts - 1:
                            logger.error(f"Jira API GET {url} failed after {max_attempts} attempts: {e}")
                            raise JiraConnectionError(
                                message=f"Failed to connect to Jira API after {max_attempts} attempts",
                                detail={
                                    "url": url,
                                    "error": str(e),
                                    "error_type": type(e).__name__,
                                }
                            )
                        backoff = min(max_backoff, base_backoff * (2 ** attempt))
                        backoff *= (0.5 + random.random())
                        self._debug(
                            f"Network error, retrying {url} after {backoff:.2f}s (attempt {attempt+1}/{max_attempts})"
                        )
                        await asyncio.sleep(backoff)
                        attempt += 1
                        last_error = e
            # No candidate succeeded
            if last_error:
                # Check if it's an authentication error (401/403)
                if isinstance(last_error, httpx.HTTPStatusError):
                    status_code = last_error.response.status_code if last_error.response else None
                    if status_code in (401, 403):
                        raise JiraAuthenticationError(
                            message="All authentication methods failed for Jira API",
                            detail={
                                "url": url,
                                "auth_candidates_tried": len(auth_candidates),
                                "status_code": status_code,
                            }
                        )
                raise last_error
            raise JiraAuthenticationError(
                message="All authentication candidates failed for Jira request",
                detail={"url": url, "auth_candidates_tried": len(auth_candidates)}
            )
        finally:
            if ephemeral_client is not None:
                try:
                    await ephemeral_client.aclose()
                except Exception:
                    pass
    
    async def get_projects(self) -> List[Dict]:
        """Fetch all projects"""
        try:
            data = await self._make_request("project")
            return data
        except (JiraConnectionError, JiraAuthenticationError, JiraAPIError):
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            logger.error(f"Error fetching projects: {e}")
            raise JiraAPIError(
                message="Failed to fetch projects from Jira",
                detail={"error": str(e), "error_type": type(e).__name__}
            )
    
    async def get_project_issues(
        self,
        project_key: str,
        start_at: int = 0,
        max_results: int = None,
        created_since: Optional[str] = None,
    ) -> Dict:
        """Fetch issues for a specific project.

        created_since: Optional date string in format YYYY-MM-DD to filter issues
        created on or after the provided date.
        """
        if max_results is None:
            try:
                max_results = int(getattr(settings, "jira_page_size", 100))
            except Exception:
                max_results = 100
        jql_parts = [f"project = {project_key}"]
        if created_since:
            # Jira JQL expects dates quoted in YYYY-MM-DD format
            jql_parts.append(f'created >= "{created_since}"')
        # Add explicit ordering to stabilize pagination across pages
        jql = " AND ".join(jql_parts) + " ORDER BY created ASC"
        fields_list = [
            "summary",
            # Description can be large; include based on config
            "status",
            "priority",
            "issuetype",
            "assignee",
            "labels",
            "created",
            "updated",
            "resolutiondate",
            "timeestimate",
            "timespent",
        ]
        if bool(getattr(settings, "jira_include_description", True)):
            fields_list.insert(1, "description")
        # Include story points field if configured
        if self.story_points_field:
            fields_list.append(self.story_points_field)
        # Include customer field if configured
        if self.customer_field:
            fields_list.append(self.customer_field)

        fields_param = ",".join(fields_list)
        params = {
            "jql": jql,
            "startAt": start_at,
            "maxResults": max_results,
            "fields": fields_param,
        }
        # Include changelog so we can compute the first transition to a
        # resolved/done status (earliest exit from NON_RESOLVED_STATUSES)
        if bool(getattr(settings, "jira_include_changelog", True)):
            params["expand"] = "changelog"
        
        try:
            self._debug(
                f"Searching issues: project={project_key}, created_since={created_since}, startAt={start_at}, maxResults={max_results}, fields={fields_param}"
            )
            return await self._make_request("search", params)
        except JiraAPIError as e:
            # Retry without story points field if Jira rejects unknown/invalid field on this instance
            resp_text = str(e.detail.get("response", "")) if e.detail else ""
            if self.story_points_field and self.story_points_field in resp_text:
                try:
                    fields_without_sp = ",".join([f for f in fields_list if f != self.story_points_field])
                    retry_params = dict(params, fields=fields_without_sp)
                    logger.warning(
                        f"Retrying search for project {project_key} without story points field '{self.story_points_field}'"
                    )
                    return await self._make_request("search", retry_params)
                except Exception as retry_e:
                    logger.error(f"Error fetching issues for project {project_key} after retry: {retry_e}")
                    return {"issues": []}
            logger.error(f"Error fetching issues for project {project_key}: {e}")
            return {"issues": []}
        except httpx.HTTPStatusError as e:
            # Handle legacy HTTPStatusError for backwards compatibility
            resp_text = e.response.text if e.response is not None else ""
            if self.story_points_field and self.story_points_field in resp_text:
                try:
                    fields_without_sp = ",".join([f for f in fields_list if f != self.story_points_field])
                    retry_params = dict(params, fields=fields_without_sp)
                    logger.warning(
                        f"Retrying search for project {project_key} without story points field '{self.story_points_field}'"
                    )
                    return await self._make_request("search", retry_params)
                except Exception as retry_e:
                    logger.error(f"Error fetching issues for project {project_key} after retry: {retry_e}")
                    return {"issues": []}
            logger.error(f"Error fetching issues for project {project_key}: {e}")
            return {"issues": []}
        except (JiraConnectionError, JiraAuthenticationError):
            # Re-raise connection and auth errors
            raise
        except Exception as e:
            logger.error(f"Error fetching issues for project {project_key}: {e}")
            return {"issues": []}
    
    async def get_all_issues(self, project_keys: List[str] = None) -> List[Dict]:
        """Fetch all issues across projects"""
        all_issues = []
        
        if not project_keys:
            projects = await self.get_projects()
            project_keys = [p["key"] for p in projects]
        
        for project_key in project_keys:
            start_at = 0
            max_results = 100
            
            while True:
                data = await self.get_project_issues(project_key, start_at, max_results)
                issues = data.get("issues", [])
                
                if not issues:
                    break
                
                all_issues.extend(issues)
                start_at += max_results
                
                if len(issues) < max_results:
                    break
        
        return all_issues
    
    async def get_users(self) -> List[Dict]:
        """Fetch all users"""
        try:
            if self.api_version == "3":
                endpoint = "users/search"
                params = {"maxResults": 1000}
            else:
                # Jira Server/DC (v2) uses singular 'user' path and 'username' param
                endpoint = "user/search"
                params = {"username": "", "maxResults": 1000}
            data = await self._make_request(endpoint, params)
            return data
        except (JiraConnectionError, JiraAuthenticationError, JiraAPIError):
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            logger.error(f"Error fetching users: {e}")
            raise JiraAPIError(
                message="Failed to fetch users from Jira",
                detail={"error": str(e), "error_type": type(e).__name__}
            )
    
    def parse_issue(self, issue: Dict) -> Dict:
        """Parse Jira issue into our format"""
        # Guard against Jira returning fields: null
        fields = issue.get("fields") or {}
        
        return {
            "jira_id": issue.get("key"),
            "summary": fields.get("summary", ""),
            "description": fields.get("description", ""),
            "status": self._extract_name(fields.get("status")),
            "priority": self._extract_name(fields.get("priority")),
            "issue_type": self._extract_name(fields.get("issuetype")),
            "assignee": fields.get("assignee"),
            "labels": fields.get("labels") or [],
            "created_at": fields.get("created"),
            "updated_at": fields.get("updated"),
            "resolved_at": fields.get("resolutiondate"),
            "story_points": fields.get(self.story_points_field) if self.story_points_field else None,
            "customer": self._extract_customer_value(fields.get(self.customer_field)) if self.customer_field else None,
            "time_estimate": fields.get("timeestimate"),
            "time_spent": fields.get("timespent")
        }


# OAuth2 implementation for Jira
class JiraOAuth:
    def __init__(self):
        self.client_id = settings.jira_client_id
        self.client_secret = settings.jira_client_secret
        self.redirect_uri = settings.jira_redirect_uri
        # Ensure no trailing slash to avoid double slashes
        self.base_url = (settings.jira_base_url or "").rstrip("/")
    
    def get_authorization_url(self) -> str:
        """Generate OAuth2 authorization URL"""
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": "read:jira-work"
        }
        
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{self.base_url}/oauth/authorize?{query_string}"
    
    async def exchange_code_for_token(self, code: str) -> Dict:
        """Exchange authorization code for access token"""
        url = f"{self.base_url}/oauth/token"
        data = {
            "grant_type": "authorization_code",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": self.redirect_uri,
            "code": code
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, data=data)
            response.raise_for_status()
            return response.json()