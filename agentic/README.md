# 🤖 Agentic AI Development Workflow System

Welcome to the Agentic AI Development Workflow! This system uses multiple AI agents (LLMs) working together to automatically develop code from requirements.

## 📁 Files in this Directory

### 🚀 Executable Scripts
- **`develop_jira_auth.py`** - Main workflow orchestrator with 6 AI agents
- **`test_agentic_setup.py`** - Setup verification script
- **`setup_agentic_workflow.sh`** - Automated environment setup

### ⚙️ Configuration
- **`requirements_agentic.txt`** - Python dependencies
- **`.env.example`** - API keys template
- **`.env`** - Your API keys (create from .env.example)

### 📚 Documentation
- **`README_START_HERE.md`** - 👈 **START HERE** - Complete overview
- **`QUICKSTART_AGENTIC.md`** - 5-minute quick start guide
- **`AGENTIC_WORKFLOW_SUMMARY.md`** - Complete system overview
- **`README_AGENTIC_WORKFLOW.md`** - Technical deep dive
- **`INDEX_AGENTIC_SYSTEM.md`** - File index and reference
- **`SETUP_COMPLETE.txt`** - Setup summary

### 📦 Output (Generated)
- **`generated_code/`** - Generated code files (created after running)
- **`development_logs/`** - Detailed workflow logs (created after running)

---

## 🚀 Quick Start

### From the `agentic/` directory:

```bash
# 1. Setup environment
./setup_agentic_workflow.sh

# 2. Add your API keys
nano .env

# 3. Test setup
python test_agentic_setup.py

# 4. Run the workflow
python develop_jira_auth.py

# 5. Check results
cat generated_code/IMPLEMENTATION_SUMMARY.md
```

### From the workspace root:

```bash
cd agentic

# Then follow steps above
./setup_agentic_workflow.sh
nano .env
python test_agentic_setup.py
python develop_jira_auth.py
```

---

## 🎯 What This Does

This system orchestrates **6 specialized AI agents** to:

1. 📖 Read requirements from `./prompts/`
2. 🏗️  Design system architecture
3. 🔍 Review and refine design (different LLM)
4. 💻 Generate production-ready code (9 files)
5. 🔎 Review code for quality & security
6. 🧪 Test and refine iteratively
7. 📦 Output final code + documentation

---

## 🤖 The AI Team

| Agent | Model | Role |
|-------|-------|------|
| 👨‍💼 System Architect | GPT-4 | Designs architecture |
| 🔍 Design Reviewer | Claude-3-Opus | Reviews & refines |
| 👨‍💻 Senior Developer | GPT-4-Turbo | Writes code |
| 🕵️ Code Reviewer | GPT-4 | Quality & security |
| 🧪 QA Engineer | GPT-3.5-Turbo | Tests functionality |
| 🔧 Debug Specialist | GPT-4 | Fixes issues |

---

## 📊 Output

After running, you'll have:

**Generated Code** (`generated_code/`):
- Backend: 4 Python/FastAPI files
- Frontend: 5 React/TypeScript files
- Documentation: Installation guide + summary

**Development Logs** (`development_logs/`):
- Design documents
- Code reviews
- Test results
- 15+ detailed log files

---

## 💰 Cost & Time

- **Time:** 10-15 minutes per complete run
- **Cost:** $0.60 - $1.50 per run
- **Output:** 9 production-ready files + docs

---

## 🔑 Requirements

**Required:**
- Python 3.11+
- OpenAI API key (GPT-4 access)

**Optional:**
- Anthropic API key (Claude-3 for better reviews)

**Get API Keys:**
- OpenAI: https://platform.openai.com/api-keys
- Anthropic: https://console.anthropic.com/

---

## 📚 Documentation

Read in this order:

1. **`README_START_HERE.md`** - Complete overview (START HERE!)
2. **`QUICKSTART_AGENTIC.md`** - 5-minute quick start
3. **`AGENTIC_WORKFLOW_SUMMARY.md`** - System details
4. **`README_AGENTIC_WORKFLOW.md`** - Technical deep dive
5. **`INDEX_AGENTIC_SYSTEM.md`** - Reference

---

## 🌟 Key Features

✅ Multi-agent AI collaboration (6 specialized agents)
✅ Iterative refinement (automatic bug fixing)
✅ Multiple LLM providers (OpenAI + Anthropic)
✅ Production-ready code output
✅ Security best practices built-in
✅ Complete documentation
✅ Full workflow logging

---

## 🔧 Troubleshooting

**Issue: Can't find files**
```bash
# Make sure you're in the agentic directory
cd /workspace/agentic
ls -la
```

**Issue: API key errors**
```bash
# Check .env file exists and has keys
cat .env
```

**Issue: Import errors**
```bash
# Reinstall dependencies
pip install -r requirements_agentic.txt
```

**More help:** See `QUICKSTART_AGENTIC.md` or `README_AGENTIC_WORKFLOW.md`

---

## 📞 Support

- Quick Start: `QUICKSTART_AGENTIC.md`
- Full Guide: `README_AGENTIC_WORKFLOW.md`
- Test Setup: `python test_agentic_setup.py`
- Check Logs: `ls development_logs/`

---

**Ready to start? Run: `./setup_agentic_workflow.sh`**

Built with ❤️ using Multi-Agent AI Architecture
