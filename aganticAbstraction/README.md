# 🔍 Legacy Code Analysis & Rule Extraction System

An advanced multi-agent AI system that analyzes legacy application code and extracts detailed development rules for AI coding assistants (Cursor, Jules, etc.).

## 🎯 Purpose

This system:
1. **Analyzes** legacy codebases from GitLab repositories
2. **Extracts** design patterns, coding conventions, and best practices
3. **Generates** detailed, structured rules in `agent.md` files
4. **Validates** and iteratively improves the rules
5. **Provides** code examples for each rule

The generated rules help AI agents understand and work with your legacy codebase consistently.

---

## 🤖 Multi-Agent Architecture

### 6 Specialized Agents:

1. **Code Analyzer** (GPT-4)
   - Analyzes code structure and architecture
   - Identifies technology stack and frameworks

2. **Pattern Extractor** (Claude-3-Opus)
   - Identifies design patterns
   - Extracts coding conventions

3. **Rule Synthesizer** (GPT-4-Turbo)
   - Creates detailed development rules
   - Structures rules for AI consumption

4. **Example Curator** (GPT-4)
   - Finds exemplary code samples
   - Documents best practices

5. **Rule Validator** (GPT-4)
   - Validates rule accuracy
   - Checks completeness

6. **Rule Enhancer** (GPT-4)
   - Iteratively improves rules
   - Refines based on validation

---

## 📊 Workflow Phases

```
1. Clone Repository     → Clone GitLab repo to local cache
2. Extract Samples      → Get representative code samples  
3. Analyze Architecture → Understand system design
4. Extract Patterns     → Identify patterns and conventions
5. Synthesize Rules     → Create actionable rules
6. Curate Examples      → Find best code examples
7. Validate Rules       → Check accuracy and completeness
8. Enhance Rules        → Iteratively improve (3 iterations)
9. Generate agent.md    → Create structured rule files
```

---

## 🚀 Quick Start

### Prerequisites

```bash
# Required
export OPENAI_API_KEY='sk-your-key-here'

# Optional (for better analysis)
export ANTHROPIC_API_KEY='sk-ant-your-key-here'

# For private GitLab repos
export GITLAB_TOKEN='your-gitlab-token'
export GITLAB_URL='https://gitlab.com'  # or your GitLab instance
```

### Installation

```bash
cd /workspace/aganticAbstraction
pip install -r requirements.txt
```

### Run Analysis

```bash
# Analyze specific repository
python extract_legacy_rules.py https://gitlab.com/user/repo.git main

# Analyze current jira-dashboard (default)
python extract_legacy_rules.py
```

---

## 📁 Output Structure

After running, you'll find:

```
aganticAbstraction/
├── extracted_rules/           # ⭐ Main output
│   ├── agent.md              # Comprehensive rules for all agents
│   ├── agent_design.md       # Design and architecture rules
│   ├── agent_coding.md       # Coding style and conventions
│   ├── agent_testing.md      # Testing patterns
│   └── agent_api.md          # API design rules
│
├── analysis_logs/            # Detailed analysis logs
│   ├── repository_structure.json
│   ├── code_samples.json
│   ├── architecture_analysis.md
│   ├── extracted_patterns.md
│   ├── synthesized_rules.md
│   ├── curated_examples.md
│   ├── validation_report.md
│   └── enhanced_rules_iter*.md
│
└── repo_cache/               # Cloned repositories
    └── [repo-name]/
```

---

## 📄 Generated Agent Files

### agent.md
**Comprehensive rule set** for general-purpose AI agents

Contains:
- Complete design rules
- Coding conventions
- Development workflows
- Code examples
- Usage instructions

### agent_design.md
**Architecture and design rules**

Focus:
- System architecture
- Design patterns
- Component structure
- Data flow

### agent_coding.md
**Code implementation rules**

Focus:
- Naming conventions
- Code style
- Error handling
- Best practices

### agent_testing.md
**Testing patterns and rules**

Focus:
- Test structure
- Testing patterns
- Coverage requirements

### agent_api.md
**API design and conventions**

Focus:
- Endpoint conventions
- Request/response patterns
- Error handling
- API documentation

---

## 🎓 How It Works

### 1. Repository Analysis

```python
# Clones repo and analyzes:
- File structure
- Languages used
- Project organization
- Line counts
```

### 2. Code Sampling

```python
# Extracts up to 50 representative files:
- Prioritizes main languages (.py, .js, .ts, etc.)
- Skips large files (>50KB)
- Avoids generated code
```

### 3. Multi-LLM Analysis

```python
# Each agent analyzes from different perspective:
- Code Analyzer: Architecture
- Pattern Extractor: Conventions
- Rule Synthesizer: Actionable rules
- Example Curator: Best practices
- Rule Validator: Accuracy check
- Rule Enhancer: Iterative improvement
```

### 4. Rule Structuring

```markdown
## Design Rules
- Specific, actionable guidelines
- Code examples included
- Rationale explained

## Coding Rules
- Naming conventions with examples
- Style guides
- Error handling patterns
```

---

## 💡 Usage with AI Agents

### Cursor

1. Place `agent.md` in your project root
2. Cursor will reference it when making changes
3. Use specialized agents for specific tasks

### Jules

1. Load `agent.md` into Jules context
2. Reference specific sections as needed
3. Jules will follow the extracted patterns

### GitHub Copilot

1. Keep `agent.md` open while coding
2. Copilot will learn from the patterns
3. Suggestions will match your codebase style

---

## ⚙️ Configuration

### Environment Variables

```bash
# Required
OPENAI_API_KEY=sk-xxx

# Optional
ANTHROPIC_API_KEY=sk-ant-xxx
GITLAB_TOKEN=glpat-xxx
GITLAB_URL=https://gitlab.com

# Advanced
MAX_ITERATIONS=3          # Enhancement iterations
MAX_FILES=50              # Max code samples
ANALYSIS_TEMPERATURE=0.3  # LLM temperature (0.0-1.0)
```

### Custom Configuration

Edit `extract_legacy_rules.py`:

```python
# Line 400+
max_iterations=3  # Change iteration count

# Line 350+
max_files=50  # Change sample count

# Line 150+
temperature=0.3  # Change analysis temperature
```

---

## 📊 Performance

### Typical Run:
- **Time:** 10-20 minutes
- **API Calls:** ~15-20
- **Cost:** $2-$5 (depending on codebase size)
- **Output:** 5 agent.md files + logs

### Factors:
- Repository size
- Number of files analyzed
- Enhancement iterations
- Models used

---

## 🧪 Testing

### Dry Run (No API Calls)

```bash
# Test with mock data (coming soon)
python test_extraction_dry_run.py
```

### Analyze Small Repo

```bash
# Start with small repository
python extract_legacy_rules.py https://github.com/small/repo.git
```

---

## 🔧 Troubleshooting

### Issue: GitLab Clone Fails

```bash
# Check token
echo $GITLAB_TOKEN

# Use SSH instead
git config --global url."git@gitlab.com:".insteadOf "https://gitlab.com/"
```

### Issue: API Rate Limit

```bash
# Reduce iterations
python extract_legacy_rules.py repo.git main 1

# Wait and retry
sleep 60 && python extract_legacy_rules.py repo.git
```

### Issue: Out of Memory

```bash
# Reduce sample count
# Edit line ~350 in extract_legacy_rules.py:
max_files=25  # Instead of 50
```

---

## 🎯 Best Practices

### For Best Results:

1. **Use both OpenAI and Anthropic**
   - Different perspectives improve quality
   - Claude excels at pattern extraction

2. **Analyze representative branches**
   - Use main/master for stable patterns
   - Use develop for active patterns

3. **Run multiple iterations**
   - 3 iterations recommended
   - More iterations = better rules

4. **Review and edit**
   - AI-generated rules may need tweaking
   - Add project-specific context

5. **Update regularly**
   - Re-run when patterns change
   - Keep rules synchronized with code

---

## 📚 Examples

### Design Rule Example

```markdown
## Component Architecture

**Pattern:** Feature-based organization

**Rule:** Each feature should be self-contained in its own directory

**Example:**
```
src/features/authentication/
  ├── components/
  ├── hooks/
  ├── api/
  └── types/
```

**Why:** Improves maintainability and makes features easy to locate
```

### Coding Rule Example

```markdown
## Naming Conventions

**Rule:** Use camelCase for variables and functions, PascalCase for classes

**Example:**
```python
# Good
userProfile = getUserProfile()
class UserManager:
    pass

# Bad
user_profile = get_user_profile()
class user_manager:
    pass
```

**Exceptions:** Constants use UPPER_SNAKE_CASE
```

---

## 🚀 Advanced Usage

### Analyze Multiple Branches

```bash
# Analyze different branches
python extract_legacy_rules.py repo.git main
python extract_legacy_rules.py repo.git develop
python extract_legacy_rules.py repo.git feature/new-api

# Compare outputs
diff extracted_rules/agent.md extracted_rules_develop/agent.md
```

### Custom Agent Creation

```python
# Create domain-specific agent
custom_agent = Agent(
    name="Database Agent",
    role="Database and ORM patterns",
    model="gpt-4",
    provider="openai"
)

# Use in custom analysis
db_patterns = await custom_agent.analyze(prompt)
```

---

## 🔗 Integration

### CI/CD Integration

```yaml
# .gitlab-ci.yml
extract-rules:
  script:
    - python aganticAbstraction/extract_legacy_rules.py
    - git add extracted_rules/
    - git commit -m "Update agent rules"
  only:
    - main
```

### Pre-commit Hook

```bash
# .git/hooks/pre-commit
#!/bin/bash
python aganticAbstraction/extract_legacy_rules.py --quick
```

---

## 📊 Metrics

The system tracks:
- API calls made
- Rules extracted
- Enhancement iterations
- Processing time
- Files analyzed

View in analysis logs or summary output.

---

## 🆘 Support

### Documentation
- Main README: This file
- Code comments: Inline documentation
- Example outputs: `extracted_rules/`

### Common Issues
- See Troubleshooting section
- Check logs in `analysis_logs/`
- Review error messages

---

## 🎉 Summary

This system **automatically extracts development rules** from your legacy codebase, making it easier for AI agents to work with your code consistently.

**Key Benefits:**
- ✅ Consistent AI-generated code
- ✅ Faster onboarding for AI agents
- ✅ Preserved coding standards
- ✅ Documented patterns and conventions
- ✅ Actionable, example-rich rules

---

**Ready to extract rules from your legacy codebase?**

```bash
python extract_legacy_rules.py your-repo-url.git
```

---

*Built with ❤️ using Multi-Agent AI Architecture*
