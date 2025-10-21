import httpx
from typing import List, Dict, Optional, Any
from datetime import datetime
import logging

from .config import settings
from .exceptions import GitLabAPIError, GitLabAuthenticationError, GitLabConnectionError


logger = logging.getLogger(__name__)


def _clean(value: Optional[str]) -> str:
    if value is None:
        return ""
    try:
        s = str(value).strip()
        if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
            s = s[1:-1].strip()
        return s
    except Exception:
        return ""


def parse_iso_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    v = value.strip()
    try:
        if v.endswith("Z"):
            v = v[:-1] + "+00:00"
        return datetime.fromisoformat(v)
    except Exception:
        return None


class GitLabClient:
    """Minimal async GitLab client for repository activity.

    Uses Private-Token header primarily and falls back to Bearer token when configured.
    """

    def __init__(self):
        self.base_url = _clean(getattr(settings, "gitlab_base_url", "")).rstrip("/")
        self.token = _clean(getattr(settings, "gitlab_token", ""))
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        if self._client is None:
            # GitLab can be a bit slow on large repos; allow decent timeouts
            timeout = httpx.Timeout(connect=5.0, read=120.0, write=30.0, pool=5.0)
            try:
                self._client = httpx.AsyncClient(timeout=timeout)
            except Exception:
                self._client = httpx.AsyncClient()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if self._client is not None:
            try:
                await self._client.aclose()
            finally:
                self._client = None

    def _headers(self) -> Dict[str, str]:
        # Prefer Private-Token header; some instances require Bearer
        headers: Dict[str, str] = {"Accept": "application/json", "User-Agent": "jira-dashboard-gitlab/1.0"}
        if self.token:
            headers["Private-Token"] = self.token
            headers.setdefault("Authorization", f"Bearer {self.token}")
        return headers

    async def _get(self, endpoint: str, params: Dict[str, Any] | None = None) -> httpx.Response:
        if not self.base_url:
            raise GitLabAPIError(message="GitLab base URL is not configured")
        url = f"{self.base_url}/api/v4/{endpoint.lstrip('/')}"
        try:
            resp = await self._client.get(url, headers=self._headers(), params=params or {})
            if resp.status_code in (401, 403):
                raise GitLabAuthenticationError(
                    message="GitLab API authentication failed",
                    detail={"status": resp.status_code, "url": str(resp.request.url), "body": (resp.text or "")[:500]},
                )
            resp.raise_for_status()
            return resp
        except httpx.HTTPStatusError as e:
            raise GitLabAPIError(
                message=f"GitLab API request failed with status {e.response.status_code if e.response else 'unknown'}",
                detail={
                    "url": str(e.request.url) if e.request else url,
                    "status": e.response.status_code if e.response else None,
                    "body": (e.response.text if e.response else "")[:500],
                },
            )
        except (httpx.TimeoutException, httpx.RequestError) as e:
            raise GitLabConnectionError(
                message="Failed to connect to GitLab API",
                detail={"url": url, "error": str(e), "type": type(e).__name__},
            )

    async def get_project(self, project_id: int) -> Dict[str, Any]:
        resp = await self._get(f"projects/{project_id}")
        return resp.json()

    async def list_branches(self, project_id: int, per_page: int = 100) -> List[Dict[str, Any]]:
        branches: List[Dict[str, Any]] = []
        page = 1
        while True:
            resp = await self._get(
                f"projects/{project_id}/repository/branches",
                params={"per_page": per_page, "page": page},
            )
            batch = resp.json() or []
            branches.extend(batch)
            total_pages = int(resp.headers.get("X-Total-Pages" , "0") or "0")
            if total_pages and page >= total_pages:
                break
            if not batch or len(batch) < per_page:
                break
            page += 1
        return branches

    async def list_commits(
        self,
        project_id: int,
        ref_name: str,
        since: Optional[str] = None,
        until: Optional[str] = None,
        per_page: int = 100,
    ) -> List[Dict[str, Any]]:
        commits: List[Dict[str, Any]] = []
        page = 1
        params: Dict[str, Any] = {"ref_name": ref_name, "per_page": per_page, "page": page}
        if since:
            params["since"] = since
        if until:
            params["until"] = until
        while True:
            params["page"] = page
            resp = await self._get(f"projects/{project_id}/repository/commits", params=params)
            batch = resp.json() or []
            commits.extend(batch)
            total_pages = int(resp.headers.get("X-Total-Pages", "0") or "0")
            if total_pages and page >= total_pages:
                break
            if not batch or len(batch) < per_page:
                break
            page += 1
        return commits

    async def list_merge_requests(
        self,
        project_id: int,
        created_after: Optional[str] = None,
        updated_after: Optional[str] = None,
        per_page: int = 100,
    ) -> List[Dict[str, Any]]:
        """List merge requests for a project (state=all), optionally filtered by created/updated."""
        mrs: List[Dict[str, Any]] = []
        page = 1
        params: Dict[str, Any] = {
            "per_page": per_page,
            "page": page,
            "scope": "all",
            "state": "all",
            # Sorting by updated_at DESC helps to bound pages when using updated_after
            "order_by": "updated_at",
            "sort": "desc",
        }
        if created_after:
            params["created_after"] = created_after
        if updated_after:
            params["updated_after"] = updated_after
        while True:
            params["page"] = page
            resp = await self._get(f"projects/{project_id}/merge_requests", params=params)
            batch = resp.json() or []
            mrs.extend(batch)
            total_pages = int(resp.headers.get("X-Total-Pages", "0") or "0")
            if total_pages and page >= total_pages:
                break
            if not batch or len(batch) < per_page:
                break
            page += 1
        return mrs
