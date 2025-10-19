#!/usr/bin/env python3
"""
Legacy Code Analysis and Rule Extraction System

Multi-agent workflow that analyzes legacy application code from GitLab,
extracts design patterns, development rules, and code examples, then
structures them into agent.md files for use by AI coding assistants.

Agents:
1. Code Analyzer - Analyzes code structure and patterns
2. Pattern Extractor - Identifies design patterns and conventions
3. Rule Synthesizer - Creates detailed development rules
4. Example Curator - Finds and documents code examples
5. Rule Validator - Validates accuracy and completeness
6. Rule Enhancer - Iteratively improves rules
"""

import asyncio
import os
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import subprocess
import re

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️  python-dotenv not installed, using system environment variables")

try:
    import openai
except ImportError:
    print("❌ openai package required: pip install openai")
    
try:
    from anthropic import Anthropic
except ImportError:
    print("⚠️  anthropic package optional: pip install anthropic")
    Anthropic = None

# Configuration
WORKSPACE_ROOT = Path("/workspace")
ABSTRACTION_DIR = WORKSPACE_ROOT / "aganticAbstraction"
OUTPUT_DIR = ABSTRACTION_DIR / "extracted_rules"
LOGS_DIR = ABSTRACTION_DIR / "analysis_logs"
REPO_CACHE_DIR = ABSTRACTION_DIR / "repo_cache"

# Create directories
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)
REPO_CACHE_DIR.mkdir(parents=True, exist_ok=True)

# API Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
GITLAB_TOKEN = os.getenv("GITLAB_TOKEN")
GITLAB_URL = os.getenv("GITLAB_URL", "https://gitlab.com")

openai.api_key = OPENAI_API_KEY
anthropic_client = Anthropic(api_key=ANTHROPIC_API_KEY) if ANTHROPIC_API_KEY and Anthropic else None


class Colors:
    """ANSI color codes for terminal output"""
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    MAGENTA = '\033[95m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_header(text: str):
    """Print formatted header"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text.center(80)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.END}\n")


def print_phase(phase_num: int, phase_name: str):
    """Print phase information"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}Phase {phase_num}: {phase_name}{Colors.END}")
    print(f"{Colors.BLUE}{'-'*80}{Colors.END}")


def print_agent(agent_name: str, action: str):
    """Print agent action"""
    print(f"{Colors.MAGENTA}🤖 {agent_name}{Colors.END}: {action}")


def print_success(message: str):
    """Print success message"""
    print(f"{Colors.GREEN}✅ {message}{Colors.END}")


def print_info(message: str):
    """Print info message"""
    print(f"{Colors.CYAN}ℹ️  {message}{Colors.END}")


def print_warning(message: str):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.END}")


def print_error(message: str):
    """Print error message"""
    print(f"{Colors.RED}❌ {message}{Colors.END}")


class Agent:
    """Base agent class for legacy code analysis"""
    
    def __init__(self, name: str, role: str, model: str, provider: str = "openai"):
        self.name = name
        self.role = role
        self.model = model
        self.provider = provider
        self.call_count = 0
        
    async def analyze(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Send analysis request to LLM"""
        self.call_count += 1
        print_agent(self.name, f"Analyzing with {self.model}...")
        
        try:
            if self.provider == "openai":
                return await self._openai_call(prompt, system_prompt)
            elif self.provider == "anthropic":
                return await self._anthropic_call(prompt, system_prompt)
            else:
                raise ValueError(f"Unknown provider: {self.provider}")
        except Exception as e:
            print_error(f"Error in {self.name}: {e}")
            return f"Error: {str(e)}"
    
    async def _openai_call(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Call OpenAI API"""
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        else:
            messages.append({"role": "system", "content": f"You are {self.name}, {self.role}."})
        
        messages.append({"role": "user", "content": prompt})
        
        response = await asyncio.to_thread(
            openai.ChatCompletion.create,
            model=self.model,
            messages=messages,
            temperature=0.3,  # Lower for more consistent analysis
            max_tokens=4000
        )
        
        return response.choices[0].message.content
    
    async def _anthropic_call(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Call Anthropic Claude API"""
        if not anthropic_client:
            raise ValueError("Anthropic client not initialized")
        
        system = system_prompt or f"You are {self.name}, {self.role}."
        
        response = await asyncio.to_thread(
            anthropic_client.messages.create,
            model=self.model,
            max_tokens=4000,
            system=system,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return response.content[0].text


class GitLabIntegration:
    """Handle GitLab repository operations"""
    
    def __init__(self, gitlab_url: str, token: Optional[str] = None):
        self.gitlab_url = gitlab_url
        self.token = token
    
    def clone_repository(self, repo_url: str, branch: str = "main") -> Path:
        """Clone GitLab repository to local cache"""
        print_info(f"Cloning repository: {repo_url} (branch: {branch})")
        
        # Extract repo name
        repo_name = repo_url.split('/')[-1].replace('.git', '')
        repo_path = REPO_CACHE_DIR / repo_name
        
        # Remove existing directory
        if repo_path.exists():
            print_info("Repository already cached, pulling latest changes...")
            try:
                subprocess.run(
                    ["git", "-C", str(repo_path), "pull"],
                    check=True,
                    capture_output=True
                )
                print_success("Repository updated")
                return repo_path
            except subprocess.CalledProcessError:
                print_warning("Pull failed, re-cloning...")
                subprocess.run(["rm", "-rf", str(repo_path)], check=True)
        
        # Clone with authentication if token provided
        if self.token:
            # Inject token into URL
            auth_url = repo_url.replace("https://", f"https://oauth2:{self.token}@")
        else:
            auth_url = repo_url
        
        try:
            subprocess.run(
                ["git", "clone", "-b", branch, auth_url, str(repo_path)],
                check=True,
                capture_output=True
            )
            print_success(f"Repository cloned to {repo_path}")
            return repo_path
        except subprocess.CalledProcessError as e:
            print_error(f"Failed to clone repository: {e}")
            raise
    
    def analyze_repository_structure(self, repo_path: Path) -> Dict:
        """Analyze repository structure and file organization"""
        print_info("Analyzing repository structure...")
        
        structure = {
            "languages": {},
            "directories": [],
            "file_types": {},
            "total_files": 0,
            "total_lines": 0
        }
        
        for root, dirs, files in os.walk(repo_path):
            # Skip git directory
            if '.git' in root:
                continue
            
            rel_path = Path(root).relative_to(repo_path)
            if rel_path != Path('.'):
                structure["directories"].append(str(rel_path))
            
            for file in files:
                structure["total_files"] += 1
                file_path = Path(root) / file
                
                # Count file types
                ext = file_path.suffix
                structure["file_types"][ext] = structure["file_types"].get(ext, 0) + 1
                
                # Count lines
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = len(f.readlines())
                        structure["total_lines"] += lines
                        
                        # Language detection
                        if ext in ['.py', '.js', '.ts', '.java', '.go', '.rs', '.cpp', '.c']:
                            structure["languages"][ext] = structure["languages"].get(ext, 0) + lines
                except:
                    pass
        
        print_success(f"Found {structure['total_files']} files, {structure['total_lines']} lines")
        return structure
    
    def get_code_samples(self, repo_path: Path, max_files: int = 50) -> List[Dict]:
        """Extract code samples from repository"""
        print_info(f"Extracting code samples (max {max_files} files)...")
        
        samples = []
        file_count = 0
        
        # Prioritize certain file types
        priority_extensions = ['.py', '.js', '.ts', '.tsx', '.java', '.go', '.rs']
        
        for ext in priority_extensions:
            if file_count >= max_files:
                break
                
            for file_path in repo_path.rglob(f"*{ext}"):
                if file_count >= max_files:
                    break
                
                if '.git' in str(file_path) or 'node_modules' in str(file_path):
                    continue
                
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        
                        if len(content) < 50000:  # Skip very large files
                            samples.append({
                                "path": str(file_path.relative_to(repo_path)),
                                "content": content,
                                "language": ext[1:],
                                "lines": len(content.split('\n'))
                            })
                            file_count += 1
                except:
                    continue
        
        print_success(f"Extracted {len(samples)} code samples")
        return samples


class LegacyCodeOrchestrator:
    """Orchestrates the legacy code analysis workflow"""
    
    def __init__(self):
        # Initialize agents with different models for diverse perspectives
        self.code_analyzer = Agent(
            name="Code Analyzer",
            role="Analyzes code structure, patterns, and architecture",
            model="gpt-4",
            provider="openai"
        )
        
        self.pattern_extractor = Agent(
            name="Pattern Extractor",
            role="Identifies design patterns and coding conventions",
            model="claude-3-opus-20240229",
            provider="anthropic"
        ) if anthropic_client else Agent(
            name="Pattern Extractor",
            role="Identifies design patterns and coding conventions",
            model="gpt-4",
            provider="openai"
        )
        
        self.rule_synthesizer = Agent(
            name="Rule Synthesizer",
            role="Creates detailed development rules from patterns",
            model="gpt-4-turbo-preview",
            provider="openai"
        )
        
        self.example_curator = Agent(
            name="Example Curator",
            role="Finds and documents exemplary code samples",
            model="gpt-4",
            provider="openai"
        )
        
        self.rule_validator = Agent(
            name="Rule Validator",
            role="Validates accuracy and completeness of rules",
            model="gpt-4",
            provider="openai"
        )
        
        self.rule_enhancer = Agent(
            name="Rule Enhancer",
            role="Iteratively improves and refines rules",
            model="gpt-4",
            provider="openai"
        )
        
        self.gitlab = GitLabIntegration(GITLAB_URL, GITLAB_TOKEN)
        
        self.stats = {
            "start_time": None,
            "end_time": None,
            "api_calls": 0,
            "rules_extracted": 0,
            "iterations": 0
        }
    
    async def run(self, repo_url: str, branch: str = "main", max_iterations: int = 3):
        """Run the complete analysis workflow"""
        print_header("🔍 LEGACY CODE ANALYSIS & RULE EXTRACTION")
        print_info(f"Repository: {repo_url}")
        print_info(f"Branch: {branch}")
        print_info(f"Max iterations: {max_iterations}\n")
        
        self.stats['start_time'] = datetime.now()
        
        try:
            # Phase 1: Clone and analyze repository
            repo_path = await self.clone_and_analyze(repo_url, branch)
            
            # Phase 2: Extract code samples
            code_samples = await self.extract_code_samples(repo_path)
            
            # Phase 3: Analyze code architecture
            architecture = await self.analyze_architecture(code_samples)
            
            # Phase 4: Extract patterns and conventions
            patterns = await self.extract_patterns(code_samples, architecture)
            
            # Phase 5: Synthesize development rules
            rules = await self.synthesize_rules(patterns, code_samples)
            
            # Phase 6: Curate code examples
            examples = await self.curate_examples(code_samples, rules)
            
            # Phase 7: Validate rules
            validation = await self.validate_rules(rules, examples, code_samples)
            
            # Phase 8: Iterative enhancement
            enhanced_rules = await self.enhance_rules(rules, validation, max_iterations)
            
            # Phase 9: Generate agent.md files
            await self.generate_agent_files(enhanced_rules, examples)
            
            # Summary
            self.print_summary()
            
        except Exception as e:
            print_error(f"Workflow failed: {e}")
            raise
    
    async def clone_and_analyze(self, repo_url: str, branch: str) -> Path:
        """Phase 1: Clone repository and analyze structure"""
        print_phase(1, "Clone Repository and Analyze Structure")
        
        repo_path = self.gitlab.clone_repository(repo_url, branch)
        structure = self.gitlab.analyze_repository_structure(repo_path)
        
        # Save structure analysis
        structure_file = LOGS_DIR / "repository_structure.json"
        with open(structure_file, 'w') as f:
            json.dump(structure, f, indent=2)
        
        print_success("Repository structure analyzed")
        return repo_path
    
    async def extract_code_samples(self, repo_path: Path) -> List[Dict]:
        """Phase 2: Extract representative code samples"""
        print_phase(2, "Extract Code Samples")
        
        samples = self.gitlab.get_code_samples(repo_path, max_files=50)
        
        # Save samples metadata
        samples_meta = [{"path": s["path"], "language": s["language"], "lines": s["lines"]} 
                       for s in samples]
        with open(LOGS_DIR / "code_samples.json", 'w') as f:
            json.dump(samples_meta, f, indent=2)
        
        return samples
    
    async def analyze_architecture(self, code_samples: List[Dict]) -> Dict:
        """Phase 3: Analyze code architecture"""
        print_phase(3, "Analyze Code Architecture")
        
        # Prepare analysis prompt
        sample_overview = "\n".join([
            f"- {s['path']} ({s['language']}, {s['lines']} lines)"
            for s in code_samples[:20]
        ])
        
        prompt = f"""Analyze this codebase architecture based on these files:

{sample_overview}

Sample code from key files:
{self._format_code_samples(code_samples[:5])}

Analyze and describe:
1. Overall architecture pattern (MVC, microservices, layered, etc.)
2. Project structure and organization
3. Key modules and their responsibilities
4. Technology stack and frameworks used
5. Data flow and component interactions
6. API design patterns
7. Error handling approaches

Provide a detailed architectural analysis."""

        analysis = await self.code_analyzer.analyze(prompt)
        self.stats['api_calls'] += 1
        
        # Save analysis
        with open(LOGS_DIR / "architecture_analysis.md", 'w') as f:
            f.write(analysis)
        
        print_success("Architecture analyzed")
        return {"analysis": analysis, "samples_count": len(code_samples)}
    
    async def extract_patterns(self, code_samples: List[Dict], architecture: Dict) -> Dict:
        """Phase 4: Extract design patterns and conventions"""
        print_phase(4, "Extract Patterns and Conventions")
        
        prompt = f"""Based on this codebase analysis:

{architecture['analysis']}

And these code samples:
{self._format_code_samples(code_samples[:10])}

Identify and document:
1. Design patterns used (with specific examples)
2. Code organization conventions
3. Naming conventions (variables, functions, classes, files)
4. Code style and formatting rules
5. Common idioms and best practices
6. Error handling patterns
7. Testing patterns (if visible)
8. Documentation standards
9. API conventions
10. Database/data access patterns

For each pattern, provide:
- Pattern name
- Where it's used
- Why it's used
- Specific code examples
"""

        patterns_raw = await self.pattern_extractor.analyze(prompt)
        self.stats['api_calls'] += 1
        
        # Save patterns
        with open(LOGS_DIR / "extracted_patterns.md", 'w') as f:
            f.write(patterns_raw)
        
        print_success("Patterns extracted")
        return {"patterns": patterns_raw}
    
    async def synthesize_rules(self, patterns: Dict, code_samples: List[Dict]) -> Dict:
        """Phase 5: Synthesize development rules"""
        print_phase(5, "Synthesize Development Rules")
        
        prompt = f"""Based on these extracted patterns:

{patterns['patterns']}

Create detailed, actionable development rules for AI agents (Cursor, Jules) to follow when:
1. Adding new features to this codebase
2. Fixing bugs
3. Refactoring code
4. Writing tests

Structure the rules as:

## Design Rules
- Architecture principles to follow
- Component interaction rules
- Data flow patterns

## Coding Rules
- Naming conventions (be specific with examples)
- Code organization rules
- Style and formatting rules
- Error handling rules

## Development Rules  
- How to add new features
- How to modify existing code
- Testing requirements
- Documentation requirements

## API Rules
- Endpoint naming conventions
- Request/response patterns
- Error response formats

For each rule:
- Be specific and actionable
- Include code examples
- Explain the "why" behind the rule
- Note exceptions or special cases
"""

        rules_raw = await self.rule_synthesizer.analyze(prompt)
        self.stats['api_calls'] += 1
        self.stats['rules_extracted'] += rules_raw.count('\n## ')
        
        # Save rules
        with open(LOGS_DIR / "synthesized_rules.md", 'w') as f:
            f.write(rules_raw)
        
        print_success(f"Rules synthesized ({self.stats['rules_extracted']} sections)")
        return {"rules": rules_raw}
    
    async def curate_examples(self, code_samples: List[Dict], rules: Dict) -> Dict:
        """Phase 6: Curate exemplary code examples"""
        print_phase(6, "Curate Code Examples")
        
        prompt = f"""Given these development rules:

{rules['rules']}

And these code samples:
{self._format_code_samples(code_samples[:15])}

Curate the BEST code examples that demonstrate:
1. Correct implementation of each design pattern
2. Good naming conventions
3. Proper error handling
4. Well-structured code
5. Good documentation

For each example:
- Explain what makes it good
- Reference which rules it demonstrates
- Highlight key aspects

Format as:
### Example: [Description]
**Demonstrates:** [Rules]
**File:** [path]
```[language]
[code]
```
**Why this is good:** [Explanation]
"""

        examples_raw = await self.example_curator.analyze(prompt)
        self.stats['api_calls'] += 1
        
        # Save examples
        with open(LOGS_DIR / "curated_examples.md", 'w') as f:
            f.write(examples_raw)
        
        print_success("Examples curated")
        return {"examples": examples_raw}
    
    async def validate_rules(self, rules: Dict, examples: Dict, code_samples: List[Dict]) -> Dict:
        """Phase 7: Validate rules accuracy"""
        print_phase(7, "Validate Rules")
        
        prompt = f"""Validate these development rules:

{rules['rules']}

Against these examples:
{examples['examples']}

And actual code samples:
{self._format_code_samples(code_samples[10:15])}

Check:
1. Are rules accurate? (do they match actual code?)
2. Are rules complete? (any missing patterns?)
3. Are rules clear? (actionable for AI agents?)
4. Are examples good? (do they demonstrate rules?)
5. Any contradictions?
6. Any ambiguities?

Provide:
- Accuracy score (1-10)
- Completeness score (1-10)
- Clarity score (1-10)
- List of issues found
- Suggestions for improvement
"""

        validation_raw = await self.rule_validator.analyze(prompt)
        self.stats['api_calls'] += 1
        
        # Save validation
        with open(LOGS_DIR / "validation_report.md", 'w') as f:
            f.write(validation_raw)
        
        print_success("Rules validated")
        return {"validation": validation_raw}
    
    async def enhance_rules(self, rules: Dict, validation: Dict, max_iterations: int) -> Dict:
        """Phase 8: Iteratively enhance rules"""
        print_phase(8, "Iterative Rule Enhancement")
        
        current_rules = rules['rules']
        
        for iteration in range(max_iterations):
            self.stats['iterations'] += 1
            print_info(f"Enhancement iteration {iteration + 1}/{max_iterations}")
            
            prompt = f"""Improve these rules based on validation feedback:

CURRENT RULES:
{current_rules}

VALIDATION FEEDBACK:
{validation['validation']}

Enhance by:
1. Fixing inaccuracies
2. Adding missing patterns
3. Clarifying ambiguous rules
4. Adding more specific examples
5. Improving structure and organization

Output the IMPROVED complete rule set."""

            enhanced = await self.rule_enhancer.analyze(prompt)
            self.stats['api_calls'] += 1
            
            # Save iteration
            with open(LOGS_DIR / f"enhanced_rules_iter{iteration + 1}.md", 'w') as f:
                f.write(enhanced)
            
            current_rules = enhanced
            print_success(f"Iteration {iteration + 1} complete")
        
        print_success(f"Rules enhanced through {max_iterations} iterations")
        return {"enhanced_rules": current_rules}
    
    async def generate_agent_files(self, enhanced_rules: Dict, examples: Dict):
        """Phase 9: Generate agent.md files"""
        print_phase(9, "Generate Agent Configuration Files")
        
        # Parse rules into sections
        rules_text = enhanced_rules['enhanced_rules']
        
        # Generate comprehensive agent.md
        agent_md_content = f"""# Development Agent Rules for Legacy Codebase

**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

---

{rules_text}

---

## Code Examples

{examples['examples']}

---

## Usage Instructions for AI Agents

### When Adding New Features:
1. Review the Design Rules section
2. Follow the Coding Rules for implementation
3. Refer to Code Examples for patterns
4. Ensure consistency with existing code structure

### When Fixing Bugs:
1. Identify the affected component using Architecture section
2. Follow error handling patterns
3. Maintain coding style consistency
4. Add tests following testing patterns

### When Refactoring:
1. Preserve existing design patterns
2. Maintain API compatibility
3. Follow naming conventions
4. Update documentation

---

## Key Principles

1. **Consistency**: Match existing code style and patterns
2. **Clarity**: Write self-documenting code
3. **Completeness**: Include error handling and tests
4. **Context**: Understand the broader architecture

---

*These rules were extracted through multi-agent analysis of the legacy codebase.*
"""
        
        # Save main agent.md
        agent_file = OUTPUT_DIR / "agent.md"
        with open(agent_file, 'w') as f:
            f.write(agent_md_content)
        
        print_success(f"Generated: {agent_file}")
        
        # Generate specialized agent files
        await self._generate_specialized_agents(rules_text, examples['examples'])
    
    async def _generate_specialized_agents(self, rules: str, examples: str):
        """Generate specialized agent.md files for different purposes"""
        
        # Design agent
        design_agent = f"""# Design Agent Rules

## Focus: Architecture and Design Patterns

{self._extract_section(rules, "Design Rules")}

## Relevant Examples
{self._extract_design_examples(examples)}

## Key Responsibilities
- Ensure architectural consistency
- Apply appropriate design patterns
- Maintain component boundaries
- Follow data flow patterns
"""
        with open(OUTPUT_DIR / "agent_design.md", 'w') as f:
            f.write(design_agent)
        print_success("Generated: agent_design.md")
        
        # Coding agent
        coding_agent = f"""# Coding Agent Rules

## Focus: Code Implementation and Style

{self._extract_section(rules, "Coding Rules")}

## Code Examples
{examples}

## Key Responsibilities
- Follow naming conventions
- Maintain code style
- Handle errors properly
- Write clean, readable code
"""
        with open(OUTPUT_DIR / "agent_coding.md", 'w') as f:
            f.write(coding_agent)
        print_success("Generated: agent_coding.md")
        
        # Testing agent
        testing_agent = f"""# Testing Agent Rules

## Focus: Test Writing and Quality

{self._extract_section(rules, "Testing") or "# Testing Patterns\n\nExtracted from codebase analysis."}

## Key Responsibilities
- Write comprehensive tests
- Follow testing patterns
- Ensure code coverage
- Test edge cases
"""
        with open(OUTPUT_DIR / "agent_testing.md", 'w') as f:
            f.write(testing_agent)
        print_success("Generated: agent_testing.md")
        
        # API agent
        api_agent = f"""# API Agent Rules

## Focus: API Design and Implementation

{self._extract_section(rules, "API Rules")}

## Key Responsibilities
- Follow API conventions
- Maintain consistent endpoints
- Handle errors properly
- Document APIs clearly
"""
        with open(OUTPUT_DIR / "agent_api.md", 'w') as f:
            f.write(api_agent)
        print_success("Generated: agent_api.md")
    
    def _extract_section(self, text: str, section_name: str) -> str:
        """Extract a specific section from markdown text"""
        pattern = f"## {section_name}(.*?)(?=\n## |$)"
        match = re.search(pattern, text, re.DOTALL)
        return match.group(0) if match else f"## {section_name}\n\n(Section not found)"
    
    def _extract_design_examples(self, examples: str) -> str:
        """Extract design-related examples"""
        # Simple extraction - take first few examples
        lines = examples.split('\n')
        return '\n'.join(lines[:50])
    
    def _format_code_samples(self, samples: List[Dict], max_lines: int = 50) -> str:
        """Format code samples for prompts"""
        formatted = []
        for sample in samples[:5]:  # Limit to avoid token overload
            content_lines = sample['content'].split('\n')[:max_lines]
            content_preview = '\n'.join(content_lines)
            formatted.append(f"""
### {sample['path']} ({sample['language']})
```{sample['language']}
{content_preview}
```
""")
        return '\n'.join(formatted)
    
    def print_summary(self):
        """Print workflow summary"""
        self.stats['end_time'] = datetime.now()
        duration = (self.stats['end_time'] - self.stats['start_time']).total_seconds()
        
        print_header("📊 ANALYSIS SUMMARY")
        
        print(f"{Colors.BOLD}Results:{Colors.END}")
        print(f"  ⏱️  Duration: {duration:.2f} seconds")
        print(f"  🤖 API calls: {self.stats['api_calls']}")
        print(f"  📋 Rules extracted: {self.stats['rules_extracted']} sections")
        print(f"  🔄 Enhancement iterations: {self.stats['iterations']}")
        
        print(f"\n{Colors.BOLD}Generated Files:{Colors.END}")
        print(f"  📄 agent.md - Main agent rules")
        print(f"  📄 agent_design.md - Design rules")
        print(f"  📄 agent_coding.md - Coding rules")
        print(f"  📄 agent_testing.md - Testing rules")
        print(f"  📄 agent_api.md - API rules")
        
        print(f"\n{Colors.BOLD}Output Location:{Colors.END}")
        print(f"  📁 {OUTPUT_DIR}")
        print(f"  📋 {LOGS_DIR}")
        
        print(f"\n{Colors.GREEN}{Colors.BOLD}{'='*80}{Colors.END}")
        print(f"{Colors.GREEN}{Colors.BOLD}✅ Analysis complete! Agent rules ready for use.{Colors.END}")
        print(f"{Colors.GREEN}{Colors.BOLD}{'='*80}{Colors.END}\n")


async def main():
    """Main entry point"""
    import sys
    
    print_header("🔍 LEGACY CODE RULE EXTRACTION SYSTEM")
    
    # Check API keys
    if not OPENAI_API_KEY:
        print_error("OPENAI_API_KEY not set")
        print_info("Set it with: export OPENAI_API_KEY='your-key'")
        return 1
    
    # Get repository URL from arguments or use default
    if len(sys.argv) > 1:
        repo_url = sys.argv[1]
        branch = sys.argv[2] if len(sys.argv) > 2 else "main"
    else:
        # Default to current jira-dashboard repo for testing
        repo_url = "https://github.com/zieduz/cursorJiraDashbordViews.git"
        branch = "main"
        print_warning(f"No repository specified, using: {repo_url}")
    
    print_info(f"Repository: {repo_url}")
    print_info(f"Branch: {branch}\n")
    
    # Create orchestrator and run
    orchestrator = LegacyCodeOrchestrator()
    
    try:
        await orchestrator.run(repo_url, branch, max_iterations=3)
        return 0
    except Exception as e:
        print_error(f"Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
