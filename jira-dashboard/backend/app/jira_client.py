import httpx
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import asyncio
from .config import settings


class JiraClient:
    def __init__(self):
        # Ensure no trailing slash to avoid double slashes in URLs
        self.base_url = (settings.jira_base_url or "").rstrip("/")
        self.username = settings.jira_username
        self.api_token = settings.jira_api_token
        # Auth configuration
        self.auth_type = (getattr(settings, "jira_auth_type", "basic") or "basic").lower()
        self.bearer_token = getattr(settings, "jira_bearer_token", "")
        self.client_id = settings.jira_client_id
        self.client_secret = settings.jira_client_secret
        # Allow API version to be configured (e.g., 2 for Jira Server/DC)
        self.api_version = str(getattr(settings, "jira_api_version", 3))
        # Instance-specific story points field (may differ from 10016)
        self.story_points_field = getattr(settings, "jira_story_points_field", "customfield_10016") or None
        # Enable verbose debug logging via env (JIRA_DEBUG=true)
        self._debug_enabled = bool(getattr(settings, "jira_debug", False))

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
        
    async def _make_request(self, endpoint: str, params: Dict = None) -> Dict:
        """Make authenticated request to Jira API"""
        url = f"{self.base_url}/rest/api/{self.api_version}/{endpoint.lstrip('/')}"
        auth = None
        headers = {"Accept": "application/json"}

        # Determine auth strategy
        if self.auth_type == "bearer":
            if self.bearer_token:
                headers["Authorization"] = f"Bearer {self.bearer_token}"
            else:
                # Fall back to basic if bearer is selected but missing
                if self.username and self.api_token:
                    auth = (self.username, self.api_token)
        else:
            if self.username and self.api_token:
                auth = (self.username, self.api_token)
        
        # Pre-request debug logging (without exposing secrets)
        self._debug(
            "Config: base_url="
            + (self.base_url or "<unset>")
            + f", api_version={self.api_version}, story_points_field={self.story_points_field or '<none>'}"
        )
        auth_mode = self.auth_type
        auth_configured = (
            (auth_mode == "bearer" and bool(headers.get("Authorization")))
            or (auth_mode != "bearer" and bool(auth))
        )
        self._debug(
            "Auth: configured="
            + ("yes" if auth_configured else "no")
            + f", mode={auth_mode}"
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

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, auth=auth, params=params or {}, headers=headers)
                response.raise_for_status()
                self._debug(
                    f"Response: status={response.status_code}, url={str(response.request.url)}"
                )
            except httpx.HTTPStatusError as e:
                resp = e.response
                req = resp.request if resp is not None else None
                method = req.method if req is not None else "GET"
                req_url = str(req.url) if req is not None else url
                status = resp.status_code if resp is not None else "unknown"
                body_preview = (resp.text or "")[:500] if resp is not None else ""
                print(f"Jira API {method} {req_url} failed with {status}: {body_preview}")
                self._debug(
                    f"Failure details: base_url={self.base_url}, api_version={self.api_version}, auth_mode={auth_mode}, auth_header={'yes' if 'Authorization' in headers else 'no'}"
                )
                raise
            return response.json()
    
    async def get_projects(self) -> List[Dict]:
        """Fetch all projects"""
        try:
            data = await self._make_request("project")
            return data
        except Exception as e:
            print(f"Error fetching projects: {e}")
            return []
    
    async def get_project_issues(
        self,
        project_key: str,
        start_at: int = 0,
        max_results: int = 100,
        created_since: Optional[str] = None,
    ) -> Dict:
        """Fetch issues for a specific project.

        created_since: Optional date string in format YYYY-MM-DD to filter issues
        created on or after the provided date.
        """
        jql_parts = [f"project = {project_key}"]
        if created_since:
            # Jira JQL expects dates quoted in YYYY-MM-DD format
            jql_parts.append(f'created >= "{created_since}"')
        jql = " AND ".join(jql_parts)
        fields_list = [
            "summary",
            "description",
            "status",
            "priority",
            "issuetype",
            "assignee",
            "created",
            "updated",
            "resolutiondate",
            "timeestimate",
            "timespent",
        ]
        # Include story points field if configured
        if self.story_points_field:
            fields_list.append(self.story_points_field)

        fields_param = ",".join(fields_list)
        params = {
            "jql": jql,
            "startAt": start_at,
            "maxResults": max_results,
            "fields": fields_param,
        }
        
        try:
            self._debug(
                f"Searching issues: project={project_key}, created_since={created_since}, startAt={start_at}, maxResults={max_results}, fields={fields_param}"
            )
            return await self._make_request("search", params)
        except httpx.HTTPStatusError as e:
            # Retry without story points field if Jira rejects unknown/invalid field on this instance
            resp_text = e.response.text if e.response is not None else ""
            if self.story_points_field and self.story_points_field in resp_text:
                try:
                    fields_without_sp = ",".join([f for f in fields_list if f != self.story_points_field])
                    retry_params = dict(params, fields=fields_without_sp)
                    print(
                        f"Retrying search for project {project_key} without story points field '{self.story_points_field}'"
                    )
                    return await self._make_request("search", retry_params)
                except Exception as retry_e:
                    print(f"Error fetching issues for project {project_key} after retry: {retry_e}")
                    return {"issues": []}
            print(f"Error fetching issues for project {project_key}: {e}")
            return {"issues": []}
        except Exception as e:
            print(f"Error fetching issues for project {project_key}: {e}")
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
        except Exception as e:
            print(f"Error fetching users: {e}")
            return []
    
    def parse_issue(self, issue: Dict) -> Dict:
        """Parse Jira issue into our format"""
        fields = issue.get("fields", {})
        
        return {
            "jira_id": issue.get("key"),
            "summary": fields.get("summary", ""),
            "description": fields.get("description", ""),
            "status": fields.get("status", {}).get("name", ""),
            "priority": fields.get("priority", {}).get("name", ""),
            "issue_type": fields.get("issuetype", {}).get("name", ""),
            "assignee": fields.get("assignee"),
            "created_at": fields.get("created"),
            "updated_at": fields.get("updated"),
            "resolved_at": fields.get("resolutiondate"),
            "story_points": fields.get(self.story_points_field) if self.story_points_field else None,
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