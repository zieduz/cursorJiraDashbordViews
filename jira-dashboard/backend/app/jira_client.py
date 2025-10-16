import httpx
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import asyncio
from .config import settings


class JiraClient:
    def __init__(self):
        self.base_url = settings.jira_base_url
        self.username = settings.jira_username
        self.api_token = settings.jira_api_token
        self.client_id = settings.jira_client_id
        self.client_secret = settings.jira_client_secret
        
    async def _make_request(self, endpoint: str, params: Dict = None) -> Dict:
        """Make authenticated request to Jira API"""
        url = f"{self.base_url}/rest/api/3/{endpoint}"
        auth = (self.username, self.api_token)
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, auth=auth, params=params or {})
            response.raise_for_status()
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
        params = {
            "jql": jql,
            "startAt": start_at,
            "maxResults": max_results,
            "fields": "summary,description,status,priority,issuetype,assignee,created,updated,resolutiondate,timeestimate,timespent,customfield_10016"  # story points field
        }
        
        try:
            return await self._make_request("search", params)
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
            data = await self._make_request("users/search", {"maxResults": 1000})
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
            "story_points": fields.get("customfield_10016"),  # Story points field
            "time_estimate": fields.get("timeestimate"),
            "time_spent": fields.get("timespent")
        }


# OAuth2 implementation for Jira
class JiraOAuth:
    def __init__(self):
        self.client_id = settings.jira_client_id
        self.client_secret = settings.jira_client_secret
        self.redirect_uri = settings.jira_redirect_uri
        self.base_url = settings.jira_base_url
    
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