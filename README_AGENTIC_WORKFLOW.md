# 🤖 Agentic AI Development Workflow System

An advanced multi-agent AI system that uses multiple LLMs to collaboratively design, develop, review, test, and refine code for the Jira Authentication feature.

## 🎯 Overview

This system orchestrates multiple AI agents, each with specialized roles:

1. **System Architect** (GPT-4) - Analyzes requirements and creates system design
2. **Design Reviewer** (Claude-3-Opus) - Reviews and refines architectural designs
3. **Senior Developer** (GPT-4-Turbo) - Implements production-ready code
4. **Code Reviewer** (GPT-4) - Reviews code for quality and security
5. **QA Engineer** (GPT-3.5-Turbo) - Tests code and identifies issues
6. **Debug Specialist** (GPT-4) - Fixes bugs and refines code

## 🏗️ Workflow Phases

```
┌─────────────────────────────────────────────────────────────────┐
│  Phase 1: Load Requirements                                     │
│  📖 Reads user_prompt.md and system_prompt.md                   │
└─────────────────┬───────────────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────────────┐
│  Phase 2: System Design                                         │
│  🏗️  Architect creates detailed technical design                │
└─────────────────┬───────────────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────────────┐
│  Phase 3: Design Review                                         │
│  🔍 Design Reviewer analyzes and refines design (different LLM) │
└─────────────────┬───────────────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────────────┐
│  Phase 4: Code Development                                      │
│  💻 Developer generates all required files                      │
│     • Backend: models, schemas, endpoints, config               │
│     • Frontend: components, context, routing, API service       │
└─────────────────┬───────────────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────────────┐
│  Phase 5: Code Review                                           │
│  🔎 Code Reviewer checks quality, security, best practices      │
└─────────────────┬───────────────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────────────┐
│  Phase 6: Testing & Refinement (Iterative)                      │
│  🧪 QA tests code → finds issues → Debug Specialist fixes       │
│     Repeats up to 3 iterations until clean                      │
└─────────────────┬───────────────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────────────┐
│  Phase 7: Generate Final Artifacts                              │
│  📦 Creates file structure, summary, and installation guide     │
└─────────────────────────────────────────────────────────────────┘
```

## 📋 Prerequisites

### Required:
- Python 3.11 or higher
- OpenAI API key (GPT-4 access recommended)

### Optional but Recommended:
- Anthropic API key (Claude-3 access for better design review)

### Installation:

1. **Clone and navigate to workspace:**
   ```bash
   cd /workspace
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements_agentic.txt
   ```

3. **Set up API keys:**
   ```bash
   export OPENAI_API_KEY='your-openai-api-key-here'
   export ANTHROPIC_API_KEY='your-anthropic-api-key-here'  # Optional
   ```

   Or create a `.env` file:
   ```env
   OPENAI_API_KEY=your-openai-api-key-here
   ANTHROPIC_API_KEY=your-anthropic-api-key-here
   ```

## 🚀 Usage

### Basic Usage:

```bash
python develop_jira_auth.py
```

### What It Does:

1. **Reads Requirements** from `doc/prompts/user_prompt.md` and `doc/prompts/system_prompt.md`

2. **Generates Code** for:
   - **Backend Files:**
     - `app/models.py` - UserSession database model
     - `app/schemas.py` - Pydantic validation schemas
     - `app/api/auth.py` - Authentication endpoints
     - `app/config.py` - Configuration updates
   
   - **Frontend Files:**
     - `src/contexts/AuthContext.tsx` - Auth state management
     - `src/components/Login.tsx` - Login page component
     - `src/components/ProtectedRoute.tsx` - Route protection
     - `src/App.tsx` - Updated routing
     - `src/services/api.ts` - API service with auth

3. **Creates Outputs:**
   - 📁 `generated_code/` - All generated code files
   - 📋 `development_logs/` - Detailed logs of each phase
   - 📄 `generated_code/IMPLEMENTATION_SUMMARY.md` - Overview
   - 📄 `generated_code/INSTALLATION.md` - Setup instructions

## 📂 Output Structure

```
workspace/
├── develop_jira_auth.py          # Main agentic workflow script
├── requirements_agentic.txt      # Dependencies
├── generated_code/               # 🎯 Generated code output
│   ├── app/                      # Backend code
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── config.py
│   │   └── api/
│   │       └── auth.py
│   ├── src/                      # Frontend code
│   │   ├── contexts/
│   │   │   └── AuthContext.tsx
│   │   ├── components/
│   │   │   ├── Login.tsx
│   │   │   └── ProtectedRoute.tsx
│   │   ├── App.tsx
│   │   └── services/
│   │       └── api.ts
│   ├── IMPLEMENTATION_SUMMARY.md
│   └── INSTALLATION.md
└── development_logs/             # 📋 Detailed workflow logs
    ├── system_architect.log
    ├── design_reviewer.log
    ├── senior_developer.log
    ├── code_reviewer.log
    ├── qa_engineer.log
    ├── debug_specialist.log
    ├── 01_initial_design.md
    ├── 02_design_review.md
    ├── 03_code_*.txt
    ├── 04_review_*.md
    └── 05_final_*.txt
```

## 🔧 Configuration

### Agent Configuration

Edit `develop_jira_auth.py` to customize agents:

```python
# Change models
self.architect = Agent(
    name="System Architect",
    model="gpt-4",  # or "gpt-4-turbo-preview"
    provider="openai"
)

# Adjust max iterations
self.workflow_state = {
    "max_iterations": 3  # Number of refinement cycles
}
```

### Temperature Settings

Adjust creativity vs consistency:

```python
# In Agent._openai_call()
temperature=0.7,  # Lower = more consistent, Higher = more creative
```

## 📊 Expected Costs

Approximate API costs (varies by usage):

| Agent | Model | Avg Tokens | Cost per Run |
|-------|-------|------------|--------------|
| Architect | GPT-4 | ~2000 | $0.06 |
| Design Reviewer | Claude-3-Opus | ~2000 | $0.15 |
| Developer | GPT-4-Turbo | ~15000 | $0.30 |
| Code Reviewer | GPT-4 | ~10000 | $0.30 |
| QA Engineer | GPT-3.5 | ~3000 | $0.01 |
| Debugger | GPT-4 | ~5000 | $0.15 |

**Total per complete run: ~$1.00 - $1.50**

*Note: Using OpenAI for all agents (no Claude) reduces cost to ~$0.80*

## 🧪 Testing Generated Code

After generation:

1. **Review generated files:**
   ```bash
   ls -la generated_code/
   ```

2. **Check logs for any issues:**
   ```bash
   cat development_logs/code_reviewer.log
   ```

3. **Follow installation instructions:**
   ```bash
   cat generated_code/INSTALLATION.md
   ```

4. **Copy files to your project:**
   ```bash
   # Backend
   cp generated_code/app/models.py jira-dashboard/backend/app/
   cp generated_code/app/schemas.py jira-dashboard/backend/app/
   # ... etc
   
   # Frontend
   cp -r generated_code/src/* jira-dashboard/frontend/src/
   ```

## 🐛 Troubleshooting

### Issue: API Key Error
```
❌ Error: OPENAI_API_KEY environment variable not set
```

**Solution:**
```bash
export OPENAI_API_KEY='sk-...'
```

### Issue: Rate Limit Exceeded
```
❌ Error: Rate limit reached
```

**Solution:**
- Wait a few minutes
- Reduce max_tokens in Agent class
- Use GPT-3.5 for more agents

### Issue: Incomplete Code Generation
```
⚠️  Code block not found in response
```

**Solution:**
- Check logs in `development_logs/`
- Increase max_tokens
- Adjust temperature settings

### Issue: Import Errors in Generated Code
```
ImportError: No module named 'xyz'
```

**Solution:**
- Review `04_review_*.md` files for identified issues
- The debugger should catch these in Phase 6
- Increase max_iterations if needed

## 🔍 Monitoring Progress

Watch real-time progress:

```bash
# In one terminal, run the workflow
python develop_jira_auth.py

# In another terminal, watch logs
tail -f development_logs/system_architect.log
tail -f development_logs/senior_developer.log
```

## 🎨 Customization

### Add Custom Agents

```python
self.security_expert = Agent(
    name="Security Expert",
    role="Performs security audit",
    model="gpt-4",
    provider="openai"
)
```

### Add Custom Phases

```python
async def security_audit_phase(self, code: Dict) -> Dict:
    """Custom security audit phase"""
    audit_prompt = f"Perform security audit on: {code}"
    result = await self.security_expert.think(audit_prompt)
    return result
```

### Modify File Generation

Edit `development_phase()` to add/remove files:

```python
backend_files = [
    "app/models.py - UserSession model",
    "app/custom.py - Custom implementation",  # Add this
]
```

## 📈 Performance Tips

1. **Use GPT-3.5 for simple tasks** (testing, analysis)
2. **Use GPT-4 for complex tasks** (architecture, development)
3. **Use Claude for critical review** (design, security)
4. **Run in parallel** (future enhancement)
5. **Cache responses** (future enhancement)

## 🔐 Security Notes

- API keys are never logged
- Generated code includes encryption
- Review all generated code before deployment
- Test in isolated environment first

## 📚 Additional Resources

- [OpenAI API Documentation](https://platform.openai.com/docs)
- [Anthropic Claude API](https://docs.anthropic.com/)
- [Agentic AI Patterns](https://www.deeplearning.ai/short-courses/ai-agents-in-langgraph/)

## 🤝 Contributing

To improve the workflow:

1. Add more specialized agents
2. Improve code extraction logic
3. Add parallel execution
4. Add caching layer
5. Add human-in-the-loop checkpoints

## 📝 License

MIT License - Use freely for your projects

---

**Generated with ❤️ by Multi-Agent AI System**
