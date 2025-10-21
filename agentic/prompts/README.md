# Jira Authentication Feature Prompts

This directory contains detailed prompts for implementing a Jira authentication page in the Jira Performance Dashboard application.

## 📁 Files

### 1. `user_prompt.md`
The user-facing prompt that describes **what** needs to be built:
- High-level requirements
- User experience expectations
- Acceptance criteria
- Security requirements
- Design guidelines

**Audience**: Product owners, stakeholders, or developers who need to understand the feature from a user perspective.

### 2. `system_prompt.md`
The technical implementation prompt that describes **how** to build it:
- Complete architecture overview
- Detailed implementation plan
- Code examples for every component
- File structure and modifications
- Security implementation details
- Testing guidelines

**Audience**: Developers and AI assistants who need to implement the feature with full technical context.

## 🎯 Purpose

These prompts serve multiple purposes:

1. **Documentation**: Comprehensive feature specification and implementation guide
2. **AI Context**: Provide context to AI coding assistants (like Claude, GPT-4, etc.)
3. **Developer Onboarding**: Help new developers understand the authentication system
4. **Code Review**: Reference for ensuring implementation meets requirements
5. **Testing**: Basis for creating test plans and acceptance criteria

## 🚀 How to Use

### For Developers:
1. Read `user_prompt.md` to understand the feature requirements
2. Study `system_prompt.md` for implementation details
3. Follow the step-by-step implementation plan
4. Use code examples as templates
5. Verify against the testing checklist

### For AI Assistants:
Provide both prompts as context:
```
User Prompt: [content from user_prompt.md]
System Prompt: [content from system_prompt.md]

Please implement the Jira authentication feature according to these specifications.
```

### For Product/Project Managers:
- Use `user_prompt.md` to understand feature scope
- Share acceptance criteria with QA team
- Verify security requirements are met
- Review design guidelines

## 📋 Implementation Phases

The system prompt organizes implementation into two main phases:

### Phase 1: Backend Authentication System (Steps 1.1-1.7)
- Database models for sessions
- Authentication endpoints
- Session management
- Security/encryption setup
- Integration with existing code

### Phase 2: Frontend Authentication UI (Steps 2.1-2.7)
- React components (Login, ProtectedRoute)
- Authentication context/state management
- Routing with React Router
- API service updates
- Dashboard modifications

## 🔐 Key Security Features

Both prompts emphasize critical security measures:
- ✅ Token encryption with Fernet
- ✅ Session management with expiration
- ✅ Rate limiting on login attempts
- ✅ CSRF protection
- ✅ Secure HTTP-only cookies
- ✅ Input validation and sanitization
- ✅ Audit logging
- ✅ No plain-text password storage

## 🧪 Testing Coverage

The prompts include comprehensive testing requirements:
- Authentication flows (success/failure)
- Session persistence
- Token expiration
- Protected routes
- Error handling
- Mobile responsiveness
- Security validation

## 📊 Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend                            │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐  │
│  │ Login Page   │  │ Auth Context │  │ Protected Routes│  │
│  └──────────────┘  └──────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
                    ┌───────▼────────┐
                    │  API Service   │
                    │  (with token)  │
                    └───────┬────────┘
                            │
┌─────────────────────────────────────────────────────────────┐
│                         Backend                             │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐  │
│  │ Auth API     │  │ JiraClient   │  │ Session Store   │  │
│  │ /api/auth/*  │  │ (validated)  │  │ (encrypted)     │  │
│  └──────────────┘  └──────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
                    ┌───────▼────────┐
                    │   Jira API     │
                    │  (validation)  │
                    └────────────────┘
```

## 🔄 Authentication Flow

1. User enters credentials on Login page
2. Frontend validates form inputs
3. API call to POST `/api/auth/login`
4. Backend validates credentials against Jira API
5. Backend creates encrypted session in database
6. Backend returns session token
7. Frontend stores token and updates auth state
8. User redirected to dashboard
9. All subsequent API calls include token
10. Backend verifies token for protected endpoints

## 📝 Notes

- **Backward Compatibility**: The implementation maintains support for environment variable configuration
- **Multi-tenant**: Supports different users with different Jira instances
- **Scalability**: Session-based auth can be replaced with JWT for stateless scaling
- **Future Enhancements**: OAuth2 flow can be added alongside basic auth

## 🤝 Contributing

When updating these prompts:
1. Keep both prompts synchronized
2. Update version numbers/dates
3. Add new sections to README if architecture changes
4. Test prompts with actual implementation
5. Include code examples that match the current codebase

## 📚 Related Documentation

- [Jira API Documentation](https://developer.atlassian.com/cloud/jira/platform/rest/v3/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [React Authentication Patterns](https://reactjs.org/docs/context.html)
- [Cryptography with Fernet](https://cryptography.io/en/latest/fernet/)

## ❓ FAQ

**Q: Why use session tokens instead of JWT?**
A: Session tokens allow server-side revocation and better security for credential storage. JWT can be added later for stateless scaling.

**Q: Why encrypt API tokens in the database?**
A: API tokens are as sensitive as passwords. Encryption ensures they're protected even if database is compromised.

**Q: Can users have multiple active sessions?**
A: Yes, but old sessions for the same user are invalidated on new login to prevent session proliferation.

**Q: What happens to existing environment variable auth?**
A: It continues to work as a fallback. The JiraClient accepts runtime credentials or uses environment variables.

**Q: How is the encryption key managed?**
A: It should be stored in environment variables and never committed to version control. Generate with `Fernet.generate_key()`.

---

**Last Updated**: 2025-10-19
**Version**: 1.0.0
**Status**: Ready for Implementation
