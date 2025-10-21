# 🚀 Quick Start: Agentic AI Development Workflow

Get started in 5 minutes!

## ⚡ TL;DR - Quick Commands

```bash
# 1. Run setup script
./setup_agentic_workflow.sh

# 2. Edit .env with your API keys
nano .env

# 3. Test setup
python test_agentic_setup.py

# 4. Run the workflow
python develop_jira_auth.py
```

## 📋 Step-by-Step Guide

### Step 1: Setup Environment

Run the automated setup script:

```bash
chmod +x setup_agentic_workflow.sh
./setup_agentic_workflow.sh
```

This will:
- ✅ Check Python version (3.11+ required)
- ✅ Create virtual environment
- ✅ Install all dependencies
- ✅ Create .env file from template
- ✅ Create output directories

### Step 2: Configure API Keys

Edit the `.env` file with your API keys:

```bash
nano .env
```

Add your keys:

```env
# Required
OPENAI_API_KEY=sk-your-actual-openai-key-here

# Optional but recommended for better results
ANTHROPIC_API_KEY=sk-ant-your-actual-anthropic-key-here
```

**Where to get API keys:**
- OpenAI: https://platform.openai.com/api-keys
- Anthropic: https://console.anthropic.com/

### Step 3: Verify Setup

Test that everything is configured correctly:

```bash
python test_agentic_setup.py
```

Expected output:
```
✅ All tests passed! Ready to run the workflow.
```

### Step 4: Run the Workflow

Execute the agentic development workflow:

```bash
python develop_jira_auth.py
```

The workflow will:
1. 📖 Load requirements from `prompts/`
2. 🏗️  Design the system architecture
3. 🔍 Review and refine the design
4. 💻 Generate code for all components
5. 🔎 Review code for quality and security
6. 🧪 Test and refine code iteratively
7. 📦 Output final code and documentation

**Runtime:** ~5-10 minutes (depending on API speed)

### Step 5: Review Output

Check generated files:

```bash
# View generated code
ls -la generated_code/

# View implementation summary
cat generated_code/IMPLEMENTATION_SUMMARY.md

# View installation instructions
cat generated_code/INSTALLATION.md

# Check logs for details
ls development_logs/
```

## 📁 Output Structure

```
workspace/
├── generated_code/              # ⭐ Your generated code
│   ├── app/                     # Backend files
│   ├── src/                     # Frontend files
│   ├── IMPLEMENTATION_SUMMARY.md
│   └── INSTALLATION.md
└── development_logs/            # Detailed logs
    ├── 01_initial_design.md
    ├── 02_design_review.md
    ├── 03_code_*.txt
    ├── 04_review_*.md
    └── 05_final_*.txt
```

## 🎯 What Gets Generated

### Backend Code (Python/FastAPI):
- ✅ `app/models.py` - UserSession database model
- ✅ `app/schemas.py` - Pydantic validation schemas
- ✅ `app/api/auth.py` - Authentication endpoints (/login, /logout, /verify)
- ✅ `app/config.py` - Configuration updates

### Frontend Code (React/TypeScript):
- ✅ `src/contexts/AuthContext.tsx` - Authentication state management
- ✅ `src/components/Login.tsx` - Login page UI
- ✅ `src/components/ProtectedRoute.tsx` - Route protection wrapper
- ✅ `src/App.tsx` - Updated routing with React Router
- ✅ `src/services/api.ts` - API service with auth interceptors

## 🔧 Troubleshooting

### Problem: "OPENAI_API_KEY not set"

**Solution:**
```bash
# Make sure .env exists and has your key
cat .env

# Export manually if needed
export OPENAI_API_KEY='sk-...'
```

### Problem: "Import error: openai"

**Solution:**
```bash
# Install dependencies
pip install -r requirements_agentic.txt

# Or activate venv first
source venv_agentic/bin/activate
pip install -r requirements_agentic.txt
```

### Problem: "Rate limit exceeded"

**Solution:**
- Wait 1-2 minutes
- Check your OpenAI usage limits
- Consider using GPT-3.5 for some agents (edit script)

### Problem: "Prompt files not found"

**Solution:**
```bash
# Make sure prompts exist
ls prompts/

# Should see:
# - user_prompt.md
# - system_prompt.md
```

## 💡 Pro Tips

### 1. Start with Test Run
Test the setup before full run:
```bash
python test_agentic_setup.py
```

### 2. Monitor Progress
Watch logs in real-time:
```bash
tail -f development_logs/senior_developer.log
```

### 3. Save Costs
Use GPT-3.5 for simpler agents:
```python
# Edit develop_jira_auth.py
self.tester = Agent(
    name="QA Engineer",
    model="gpt-3.5-turbo",  # Cheaper than GPT-4
    provider="openai"
)
```

### 4. Increase Quality
Use Claude for critical reviews:
```bash
# Set in .env
ANTHROPIC_API_KEY=sk-ant-...
```

### 5. Adjust Iterations
Change refinement cycles:
```bash
# In .env
MAX_ITERATIONS=5  # More iterations = better quality
```

## 📊 Expected Costs

Per complete workflow run:
- **With Claude**: ~$1.00 - $1.50
- **OpenAI only**: ~$0.60 - $0.80

*Costs vary based on:*
- Code complexity
- Number of iterations
- Model choices
- Token usage

## ⏱️ Expected Timeline

| Phase | Duration | What Happens |
|-------|----------|--------------|
| Setup | 2-3 min | Install deps, configure |
| Phase 1-3 | 2-3 min | Requirements & Design |
| Phase 4 | 3-5 min | Code Generation |
| Phase 5-6 | 2-4 min | Review & Testing |
| Phase 7 | 1 min | Output Generation |
| **Total** | **~10-15 min** | Complete workflow |

## 🎓 Understanding the Workflow

### Agent Roles:

1. **System Architect** (GPT-4)
   - Analyzes requirements
   - Creates system design
   - Plans architecture

2. **Design Reviewer** (Claude-3-Opus)
   - Reviews design quality
   - Identifies gaps
   - Refines architecture

3. **Senior Developer** (GPT-4-Turbo)
   - Writes production code
   - Implements all components
   - Handles integrations

4. **Code Reviewer** (GPT-4)
   - Checks code quality
   - Finds security issues
   - Suggests improvements

5. **QA Engineer** (GPT-3.5-Turbo)
   - Tests functionality
   - Finds bugs
   - Validates requirements

6. **Debug Specialist** (GPT-4)
   - Fixes identified issues
   - Refines code
   - Ensures quality

### Workflow Phases:

```
Requirements → Design → Review → Develop → Review → Test → Refine → Output
    📖          🏗️        🔍        💻         🔎       🧪       🔧       📦
```

## 🎯 Next Steps After Generation

1. **Review Code**
   ```bash
   cat generated_code/IMPLEMENTATION_SUMMARY.md
   ```

2. **Follow Installation Guide**
   ```bash
   cat generated_code/INSTALLATION.md
   ```

3. **Copy to Project**
   ```bash
   # Backend
   cp generated_code/app/* jira-dashboard/backend/app/
   
   # Frontend
   cp -r generated_code/src/* jira-dashboard/frontend/src/
   ```

4. **Test Integration**
   - Run backend tests
   - Run frontend tests
   - Test authentication flow

5. **Deploy**
   - Review security settings
   - Update environment variables
   - Deploy to staging

## 📚 Learn More

- Full documentation: `README_AGENTIC_WORKFLOW.md`
- User requirements: `prompts/user_prompt.md`
- Technical details: `prompts/system_prompt.md`

## ❓ Common Questions

**Q: Do I need both OpenAI and Anthropic?**
A: No, OpenAI is sufficient. Anthropic improves design review quality.

**Q: How long does it take?**
A: ~10-15 minutes for complete workflow.

**Q: How much does it cost?**
A: ~$0.60-$1.50 per run depending on configuration.

**Q: Can I customize the agents?**
A: Yes! Edit `develop_jira_auth.py` to change models, roles, or add new agents.

**Q: What if generation fails?**
A: Check logs in `development_logs/` for errors. Most issues are API key or rate limit related.

## 🆘 Need Help?

1. Check test results: `python test_agentic_setup.py`
2. Review logs: `ls development_logs/`
3. Check API status: https://status.openai.com/
4. Verify API keys: `cat .env`

---

**Ready? Let's build! 🚀**

```bash
python develop_jira_auth.py
```
