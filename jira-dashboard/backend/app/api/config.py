from fastapi import APIRouter

from ..config import settings


router = APIRouter(prefix="/api/config", tags=["config"])


@router.get("/")
async def get_config():
    """Expose non-sensitive runtime configuration for the frontend.

    Returns:
    - jira_project_keys: List[str]
    - jira_created_since: str (YYYY-MM-DD)
    """
    return {
        "jira_project_keys": settings.jira_project_keys,
        "jira_created_since": settings.jira_created_since,
    }
