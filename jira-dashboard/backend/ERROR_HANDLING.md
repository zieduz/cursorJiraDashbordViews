# Error Handling Implementation

## Overview

This document describes the comprehensive error handling implementation for the Jira Performance Dashboard API. The error handling system provides structured error responses, proper logging, and graceful failure recovery throughout the application.

## Architecture

### Custom Exception Classes

Located in `app/exceptions.py`, the following custom exception classes have been implemented:

1. **JiraDashboardException** - Base exception class for all application errors
   - Includes `message`, `status_code`, and `detail` attributes
   - Provides structured error information

2. **JiraConnectionError** (503 Service Unavailable)
   - Raised when unable to connect to Jira API
   - Indicates network connectivity issues or Jira service unavailability

3. **JiraAuthenticationError** (401 Unauthorized)
   - Raised when Jira authentication fails
   - Indicates invalid credentials or expired tokens

4. **JiraAPIError** (502 Bad Gateway)
   - Raised when Jira API returns an error
   - Indicates API-level issues (rate limits, invalid requests, server errors)

5. **DatabaseError** (500 Internal Server Error)
   - Raised when database operations fail
   - Indicates issues with database connectivity or queries

6. **ValidationError** (400 Bad Request)
   - Raised when input validation fails
   - Indicates invalid user input or request parameters

### Exception Handlers

The application registers the following exception handlers in `app/main.py`:

1. **jira_dashboard_exception_handler** - Handles custom application exceptions
2. **http_exception_handler** - Handles HTTP exceptions from FastAPI/Starlette
3. **validation_exception_handler** - Handles request validation errors
4. **generic_exception_handler** - Catches all unhandled exceptions as fallback

All handlers return structured JSON responses with:
- `error`: Human-readable error message
- `detail`: Additional error details (structured data)
- `path`: Request path where error occurred

## Error Handling Flow

### Jira Client (`app/jira_client.py`)

The Jira client has been enhanced with proper error handling:

1. **Connection Errors**
   - Network timeouts and connection failures are caught
   - Retries with exponential backoff (configurable)
   - After max retries, raises `JiraConnectionError`

2. **Authentication Errors**
   - Supports multiple auth methods (Basic, Bearer)
   - Automatically tries fallback auth method
   - Raises `JiraAuthenticationError` when all methods fail

3. **API Errors**
   - Handles rate limiting (429) with Retry-After header support
   - Retries 5xx server errors with backoff
   - Raises `JiraAPIError` with detailed response information

### Jira Sync (`app/api/jira_sync.py`)

The sync endpoint implements comprehensive error handling:

1. **Validation**
   - Validates project keys and date formats
   - Raises `ValidationError` for invalid input

2. **Database Operations**
   - Wraps database commits in try-catch blocks
   - Rolls back on error
   - Raises `DatabaseError` with context

3. **Graceful Degradation**
   - If project list fetch fails, continues with provided keys
   - If one project fails, continues with remaining projects
   - Logs errors but doesn't fail entire sync

### Health Check

The `/health` endpoint has been enhanced to:
- Test database connectivity
- Return status: "healthy" or "degraded"
- Include database status in response
- Log errors without failing the check

## Logging

### Log Levels

The application uses structured logging with appropriate levels:

- **INFO**: Normal operations (startup, successful sync)
- **WARNING**: Recoverable errors (auth fallback, project list fetch failure)
- **ERROR**: Errors requiring attention (API failures, database errors)
- **EXCEPTION**: Unhandled exceptions with full stack trace

### Log Format

```
%(asctime)s - %(name)s - %(levelname)s - %(message)s
```

### Log Context

Error logs include contextual information:
- Request path and method
- Status codes
- Error details and types
- Relevant identifiers (project keys, etc.)

## Response Format

All error responses follow this structure:

```json
{
  "error": "Brief error message",
  "detail": {
    "field": "Additional context",
    "nested": {
      "data": "Structured error info"
    }
  },
  "path": "/api/endpoint"
}
```

## Configuration

Error handling behavior can be configured via environment variables:

- `JIRA_RETRY_MAX_ATTEMPTS`: Maximum retry attempts (default: 4)
- `JIRA_RETRY_BACKOFF_BASE_SECONDS`: Base backoff time (default: 0.5)
- `JIRA_RETRY_BACKOFF_MAX_SECONDS`: Maximum backoff time (default: 8.0)
- `JIRA_TIMEOUT_CONNECT_SECONDS`: Connection timeout (default: 5.0)
- `JIRA_TIMEOUT_READ_SECONDS`: Read timeout (default: 120.0)

## Best Practices

### For Developers

1. **Use Custom Exceptions**
   - Always raise custom exceptions (not generic `Exception`)
   - Provide detailed context in `detail` parameter
   - Choose appropriate exception type

2. **Log Before Raising**
   - Log errors with appropriate level
   - Include relevant context
   - Use `logger.exception()` for unexpected errors

3. **Handle Database Errors**
   - Wrap commits in try-catch
   - Always rollback on error
   - Close connections in finally blocks

4. **Graceful Degradation**
   - Continue processing when possible
   - Log errors but don't fail entire operation
   - Return partial results with warnings

### For API Consumers

1. **Check Status Codes**
   - 400: Fix request parameters
   - 401: Check authentication credentials
   - 503: Retry later (service unavailable)
   - 502: Jira API issue (check Jira status)
   - 500: Internal error (contact support)

2. **Parse Error Details**
   - Read `error` for user-friendly message
   - Check `detail` for structured error info
   - Use `path` to identify error location

3. **Implement Retries**
   - Retry on 503 (service unavailable)
   - Retry on 502 (bad gateway)
   - Use exponential backoff
   - Don't retry 4xx errors (except 429)

## Testing

To test error handling:

1. **Invalid Credentials**
   ```bash
   curl -X POST http://localhost:8000/api/jira/sync \
     -H "Content-Type: application/json"
   ```

2. **Invalid Date Format**
   ```bash
   curl -X POST http://localhost:8000/api/jira/sync \
     -H "Content-Type: application/json" \
     -d '{"created_since": "invalid-date"}'
   ```

3. **Missing Project Keys**
   ```bash
   curl -X POST http://localhost:8000/api/jira/sync \
     -H "Content-Type: application/json" \
     -d '{"project_keys": []}'
   ```

## Monitoring

### Key Metrics to Monitor

1. **Error Rates**
   - 5xx errors (server errors)
   - 4xx errors (client errors)
   - Exception handler invocations

2. **Jira API Health**
   - Connection errors
   - Authentication failures
   - API error rates

3. **Database Health**
   - Connection failures
   - Transaction rollbacks
   - Query timeouts

### Log Aggregation

Filter logs by:
- `ERROR` and `EXCEPTION` levels
- Exception types in log messages
- Specific endpoint paths
- Status codes

## Migration Notes

### Breaking Changes

None. The error handling implementation is backward compatible.

### Deprecations

- Generic `ValueError` exceptions are deprecated in favor of `ValidationError`
- Generic `Exception` raises are deprecated in favor of specific exception types

### Migration Path

Existing code will continue to work, but should be updated to:
1. Use custom exception types
2. Catch specific exceptions instead of generic `Exception`
3. Add proper logging before raising exceptions

## Future Improvements

1. **Metrics Collection**
   - Add Prometheus metrics for error rates
   - Track retry counts and success rates
   - Monitor response times

2. **Error Recovery**
   - Implement circuit breaker pattern
   - Add request queuing for rate limits
   - Automatic credential refresh

3. **Enhanced Logging**
   - Structured logging with JSON format
   - Correlation IDs for request tracing
   - Integration with log aggregation services

4. **Testing**
   - Add comprehensive error handling tests
   - Test retry logic and backoff
   - Verify error response formats
