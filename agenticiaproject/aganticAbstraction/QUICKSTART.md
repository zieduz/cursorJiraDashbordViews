# 🚀 Quick Start Guide

Get started with legacy code analysis in 5 minutes!

## Step 1: Install Dependencies (1 minute)

```bash
cd /workspace/aganticAbstraction
pip install -r requirements.txt
```

## Step 2: Configure API Keys (1 minute)

```bash
# Copy example config
cp .env.example .env

# Edit with your keys
nano .env

# Add at minimum:
OPENAI_API_KEY=sk-your-actual-key-here
```

## Step 3: Run Analysis (3-20 minutes)

### Option A: Analyze Current Jira Dashboard (Default)

```bash
python extract_legacy_rules.py
```

### Option B: Analyze Your Repository

```bash
python extract_legacy_rules.py https://gitlab.com/your/repo.git main
```

### Option C: Analyze with Custom Iterations

```bash
# Single iteration (faster)
python extract_legacy_rules.py repo.git main 1

# Five iterations (more thorough)
python extract_legacy_rules.py repo.git main 5
```

## Step 4: Review Output

```bash
# View main agent rules
cat extracted_rules/agent.md

# View specialized rules
ls extracted_rules/

# View analysis logs
ls analysis_logs/
```

## Step 5: Use with AI Agents

### For Cursor:
```bash
# Copy to project root
cp extracted_rules/agent.md /path/to/your/project/.cursorrules
```

### For Jules:
```bash
# Load into Jules
jules load extracted_rules/agent.md
```

### For GitHub Copilot:
```bash
# Keep open while coding
code extracted_rules/agent.md
```

---

## ⚡ Quick Commands

```bash
# Full analysis
python extract_legacy_rules.py

# Quick analysis (1 iteration)
python extract_legacy_rules.py repo.git main 1

# View results
cat extracted_rules/agent.md

# Check logs
tail -100 analysis_logs/architecture_analysis.md
```

---

## 🎯 What You Get

After running, you'll have:

✅ `agent.md` - Complete development rules  
✅ `agent_design.md` - Architecture rules  
✅ `agent_coding.md` - Coding conventions  
✅ `agent_testing.md` - Testing patterns  
✅ `agent_api.md` - API design rules  

Plus detailed logs of the analysis process!

---

## 💡 Pro Tips

1. **Start with 1 iteration** for speed, increase for quality
2. **Use both OpenAI and Anthropic** for better results
3. **Review and edit** generated rules for your context
4. **Re-run periodically** to keep rules updated

---

## 🐛 Troubleshooting

### "OPENAI_API_KEY not set"
```bash
export OPENAI_API_KEY='sk-your-key'
```

### "Failed to clone repository"
```bash
# Check URL
# Add GITLAB_TOKEN if private
```

### "Out of memory"
```bash
# Edit script, reduce MAX_FILES to 25
```

---

## ✅ Next Steps

1. Read full [README.md](README.md)
2. Explore `extracted_rules/`
3. Integrate with your AI agent
4. Customize rules as needed

---

**Ready? Run it now!**

```bash
python extract_legacy_rules.py
```
