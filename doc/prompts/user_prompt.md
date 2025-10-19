# User Prompt: Jira Authentication Page

## 🎯 Objective

Add an authentication page where users can authenticate with their Jira username and password (API token) to access the Jira Performance Dashboard.

## 📋 Requirements

### Core Functionality

1. **Login Page**
   - Create a dedicated authentication page with a clean, professional UI
   - Input fields for:
     - Jira Base URL (e.g., `https://your-domain.atlassian.net`)
     - Username/Email
     - API Token (password field with toggle visibility)
   - "Remember me" checkbox option
   - Submit button with loading state
   - Clear validation messages

2. **Authentication Flow**
   - Verify credentials against Jira API before granting access
   - Make a test API call (e.g., fetch user profile or projects) to validate credentials
   - Store authentication state securely
   - Redirect to dashboard upon successful authentication
   - Show specific error messages for different failure scenarios:
     - Invalid credentials
     - Network errors
     - Invalid Jira URL format
     - Timeout errors

3. **Session Management**
   - Maintain user session across page refreshes
   - Implement secure token storage (HTTP-only cookies or encrypted session storage)
   - Add session expiration handling
   - Auto-logout after inactivity period (optional)
   - Persist Jira configuration per user

4. **Protected Routes**
   - Prevent unauthenticated access to dashboard
   - Redirect to login page when session expires
   - Show loading spinner while verifying authentication status
   - Handle deep links (redirect to intended page after login)

5. **Logout Functionality**
   - Add logout button in dashboard header
   - Clear all stored credentials and session data
   - Redirect to login page
   - Show confirmation message

6. **User Experience**
   - Show helpful error messages
   - Add "Get API Token" link to Atlassian documentation
   - Display loading states during authentication
   - Add form validation (required fields, URL format)
   - Implement keyboard navigation (Enter to submit)
   - Mobile-responsive design

## 🔒 Security Requirements

1. **Never store passwords in plain text**
2. **Use HTTPS in production**
3. **Implement rate limiting on login attempts** (max 5 attempts per 15 minutes)
4. **Add CSRF protection** for state-changing operations
5. **Set secure, HTTP-only cookies** for session tokens
6. **Validate and sanitize all inputs**
7. **Log authentication attempts** for security auditing
8. **Clear credentials from memory** after authentication

## 🎨 Design Guidelines

- Match the existing dashboard design aesthetic
- Use Tailwind CSS for consistent styling
- Ensure accessibility (ARIA labels, keyboard navigation)
- Add smooth transitions and animations
- Display branding (logo, app name)
- Include helpful instructions or tooltips

## ✅ Acceptance Criteria

- [ ] Login page displays with all required fields
- [ ] Form validation works correctly
- [ ] Valid credentials successfully authenticate and redirect to dashboard
- [ ] Invalid credentials show appropriate error messages
- [ ] Session persists across page refreshes
- [ ] Logout clears session and redirects to login
- [ ] Protected routes are inaccessible without authentication
- [ ] Mobile responsive design works on all screen sizes
- [ ] Loading states are displayed during async operations
- [ ] Error handling covers all edge cases
- [ ] Security best practices are implemented

## 📚 Additional Context

Currently, the application uses environment variables for Jira authentication. This change will enable:
- **Multi-user support**: Different users can authenticate with their own Jira credentials
- **Improved security**: No need to store credentials in environment files
- **Better UX**: Users can change their Jira instance without redeploying
- **Tenant isolation**: Support for multiple Jira instances

## 🔗 Helpful Resources

- Jira API Token Generation: https://id.atlassian.com/manage-profile/security/api-tokens
- Jira REST API Authentication: https://developer.atlassian.com/cloud/jira/platform/basic-auth-for-rest-apis/
