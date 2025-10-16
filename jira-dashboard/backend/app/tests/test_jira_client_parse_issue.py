import os
import sys
from pathlib import Path

# Ensure repository root (containing 'backend') is on the import path
THIS_DIR = Path(__file__).resolve().parent
REPO_ROOT = THIS_DIR.parents[3]  # /workspace/jira-dashboard
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.app.jira_client import JiraClient


def test_parse_issue_handles_none_fields():
    client = JiraClient()
    issue = {
        "key": "PROJ-1",
        "fields": None,
    }
    parsed = client.parse_issue(issue)
    assert parsed["jira_id"] == "PROJ-1"
    assert parsed["summary"] == ""
    assert parsed["description"] == ""
    assert parsed["status"] == ""
    assert parsed["priority"] == ""
    assert parsed["issue_type"] == ""
    assert parsed["labels"] == []


def _wrap_fields(status=None, priority=None, issuetype=None, **kwargs):
    f = {
        "summary": "S",
        "description": "D",
        "status": status,
        "priority": priority,
        "issuetype": issuetype,
        "labels": ["a", "b"],
        "created": "2025-01-02T03:04:05.000+0000",
        "updated": "2025-01-03T03:04:05.000+0000",
        "resolutiondate": None,
        "timeestimate": None,
        "timespent": None,
    }
    f.update(kwargs)
    return f


def test_parse_issue_extracts_name_from_dict():
    client = JiraClient()
    issue = {
        "key": "P-2",
        "fields": _wrap_fields(status={"name": "In Progress"}, priority={"name": "High"}, issuetype={"name": "Bug"}),
    }
    parsed = client.parse_issue(issue)
    assert parsed["status"] == "In Progress"
    assert parsed["priority"] == "High"
    assert parsed["issue_type"] == "Bug"


def test_parse_issue_handles_none_nested():
    client = JiraClient()
    issue = {
        "key": "P-3",
        "fields": _wrap_fields(status=None, priority=None, issuetype=None),
    }
    parsed = client.parse_issue(issue)
    assert parsed["status"] == ""
    assert parsed["priority"] == ""
    assert parsed["issue_type"] == ""


def test_parse_issue_coerces_primitives():
    client = JiraClient()
    issue = {
        "key": "P-4",
        "fields": _wrap_fields(status="Done", priority=3, issuetype=True),
    }
    parsed = client.parse_issue(issue)
    assert parsed["status"] == "Done"
    assert parsed["priority"] == "3"
    assert parsed["issue_type"] == "True"
