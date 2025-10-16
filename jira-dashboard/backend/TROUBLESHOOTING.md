# Jira Backend Troubleshooting

## 401 Unauthorized from Jira API

If you see logs like:

```
Jira API GET https://<your-jira>/rest/api/... returned 401 Unauthorized (auth_mode=basic)
```

Follow these steps:

- Verify `JIRA_BASE_URL` is correct and reachable.
- For Jira Cloud (`*.atlassian.net`):
  - Use `JIRA_AUTH_TYPE=basic`
  - Set `JIRA_USERNAME` to your Atlassian account email
  - Set `JIRA_API_TOKEN` to an API token from https://id.atlassian.com/manage-profile/security/api-tokens
  - Keep `JIRA_API_VERSION=3`
- For Jira Server/Data Center (non-Cloud domains, e.g., on-prem like `jira.company.com`):
  - Prefer `JIRA_AUTH_TYPE=bearer` with `JIRA_BEARER_TOKEN` (Personal Access Token)
  - Set `JIRA_API_VERSION=2`
- Enable debug logging to see non-sensitive request context:
  - `JIRA_DEBUG=true`

The client will automatically try alternative auth modes on a 401 (e.g., switch from basic to bearer, or vice versa) when credentials for the other mode are present.

## Common Misconfigurations

- Wrong API version for Server/DC (should be v2)
- Using password instead of API token for Jira Cloud
- Missing `JIRA_BEARER_TOKEN` when selecting `bearer` auth

