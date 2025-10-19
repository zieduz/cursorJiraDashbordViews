#!/usr/bin/env python3
"""
Agentic AI Development Workflow for Jira Authentication
Uses multiple LLMs to analyze, design, develop, review, and refine code.
"""

import os
import json
import asyncio
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️  python-dotenv not installed, using system environment variables")

import openai
from anthropic import Anthropic

# Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
MAX_ITERATIONS = int(os.getenv("MAX_ITERATIONS", "3"))
AGENT_TEMPERATURE = float(os.getenv("AGENT_TEMPERATURE", "0.7"))
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "4000"))

# Initialize clients
openai.api_key = OPENAI_API_KEY
anthropic_client = Anthropic(api_key=ANTHROPIC_API_KEY) if ANTHROPIC_API_KEY else None

# Workspace paths
WORKSPACE_ROOT = Path("/workspace")
PROMPTS_DIR = WORKSPACE_ROOT / "doc" / "prompts"
OUTPUT_DIR = WORKSPACE_ROOT / "generated_code"
LOGS_DIR = WORKSPACE_ROOT / "development_logs"

# Create directories
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)


class Agent:
    """Base agent class for different roles in the development workflow"""
    
    def __init__(self, name: str, role: str, model: str, provider: str = "openai"):
        self.name = name
        self.role = role
        self.model = model
        self.provider = provider
        self.conversation_history = []
    
    async def think(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Send a prompt to the LLM and get response"""
        print(f"\n{'='*80}")
        print(f"🤖 {self.name} ({self.role}) is thinking...")
        print(f"{'='*80}\n")
        
        try:
            if self.provider == "openai":
                return await self._openai_call(prompt, system_prompt)
            elif self.provider == "anthropic":
                return await self._anthropic_call(prompt, system_prompt)
            else:
                raise ValueError(f"Unknown provider: {self.provider}")
        except Exception as e:
            print(f"❌ Error in {self.name}: {e}")
            return f"Error: {str(e)}"
    
    async def _openai_call(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Call OpenAI API"""
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        response = await asyncio.to_thread(
            openai.ChatCompletion.create,
            model=self.model,
            messages=messages,
            temperature=AGENT_TEMPERATURE,
            max_tokens=MAX_TOKENS
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
            max_tokens=MAX_TOKENS,
            system=system,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return response.content[0].text
    
    def log(self, message: str, level: str = "INFO"):
        """Log agent activity"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] [{level}] {self.name}: {message}"
        print(log_message)
        
        # Write to log file
        log_file = LOGS_DIR / f"{self.name.lower().replace(' ', '_')}.log"
        with open(log_file, "a") as f:
            f.write(log_message + "\n")


class WorkflowOrchestrator:
    """Orchestrates the multi-agent development workflow"""
    
    def __init__(self):
        # Create agents with different roles and models
        self.architect = Agent(
            name="System Architect",
            role="Analyzes requirements and creates system design",
            model="gpt-4",
            provider="openai"
        )
        
        self.design_reviewer = Agent(
            name="Design Reviewer",
            role="Reviews and refines architectural designs",
            model="claude-3-opus-20240229",
            provider="anthropic"
        ) if ANTHROPIC_API_KEY else Agent(
            name="Design Reviewer",
            role="Reviews and refines architectural designs",
            model="gpt-4",
            provider="openai"
        )
        
        self.developer = Agent(
            name="Senior Developer",
            role="Implements code based on designs",
            model="gpt-4-turbo-preview",
            provider="openai"
        )
        
        self.code_reviewer = Agent(
            name="Code Reviewer",
            role="Reviews code for quality, security, and best practices",
            model="gpt-4",
            provider="openai"
        )
        
        self.tester = Agent(
            name="QA Engineer",
            role="Tests code and identifies issues",
            model="gpt-3.5-turbo",
            provider="openai"
        )
        
        self.debugger = Agent(
            name="Debug Specialist",
            role="Fixes bugs and refines code",
            model="gpt-4",
            provider="openai"
        )
        
        self.workflow_state = {
            "phase": "initialization",
            "iteration": 0,
            "max_iterations": MAX_ITERATIONS,
            "artifacts": {}
        }
    
    async def run(self):
        """Execute the complete development workflow"""
        print("\n" + "="*80)
        print("🚀 Starting Agentic AI Development Workflow")
        print("="*80 + "\n")
        
        try:
            # Phase 1: Load and analyze requirements
            requirements = await self.load_requirements()
            
            # Phase 2: Design
            design = await self.design_phase(requirements)
            
            # Phase 3: Review and refine design
            refined_design = await self.design_review_phase(design, requirements)
            
            # Phase 4: Development
            code_artifacts = await self.development_phase(refined_design, requirements)
            
            # Phase 5: Code review
            reviewed_code = await self.code_review_phase(code_artifacts, refined_design)
            
            # Phase 6: Testing and refinement loop
            final_code = await self.test_and_refine_phase(reviewed_code, refined_design)
            
            # Phase 7: Generate final artifacts
            await self.generate_final_artifacts(final_code)
            
            print("\n" + "="*80)
            print("✅ Development workflow completed successfully!")
            print(f"📁 Generated code location: {OUTPUT_DIR}")
            print(f"📋 Logs location: {LOGS_DIR}")
            print("="*80 + "\n")
            
        except Exception as e:
            print(f"\n❌ Workflow failed: {e}")
            raise
    
    async def load_requirements(self) -> Dict:
        """Load and parse requirements from markdown files"""
        print("\n📖 Phase 1: Loading Requirements\n")
        
        user_prompt_path = PROMPTS_DIR / "user_prompt.md"
        system_prompt_path = PROMPTS_DIR / "system_prompt.md"
        
        user_prompt = user_prompt_path.read_text()
        system_prompt = system_prompt_path.read_text()
        
        # Use architect to analyze requirements
        analysis_prompt = f"""
        Analyze these requirements and extract key information:
        
        USER REQUIREMENTS:
        {user_prompt}
        
        SYSTEM IMPLEMENTATION GUIDE:
        {system_prompt}
        
        Please provide a structured analysis covering:
        1. Core functionality required
        2. Key components to build (backend and frontend)
        3. Security requirements
        4. Dependencies needed
        5. Integration points
        6. Priority order for implementation
        
        Format as JSON.
        """
        
        analysis = await self.architect.think(analysis_prompt)
        
        return {
            "user_prompt": user_prompt,
            "system_prompt": system_prompt,
            "analysis": analysis
        }
    
    async def design_phase(self, requirements: Dict) -> Dict:
        """Create system design"""
        print("\n🏗️  Phase 2: System Design\n")
        
        design_prompt = f"""
        Based on these requirements, create a detailed technical design:
        
        {requirements['analysis']}
        
        Create a design document that includes:
        1. Architecture overview
        2. Database schema (UserSession table)
        3. API endpoints specification
        4. Component structure (React components)
        5. Data flow diagrams
        6. Security implementation plan
        7. File structure and organization
        
        Be specific and actionable. Include actual model definitions, schemas, and component structures.
        """
        
        design = await self.architect.think(design_prompt)
        
        # Save design
        design_file = LOGS_DIR / "01_initial_design.md"
        design_file.write_text(design)
        
        return {
            "design": design,
            "requirements": requirements
        }
    
    async def design_review_phase(self, design: Dict, requirements: Dict) -> Dict:
        """Review and refine the design using a different LLM"""
        print("\n🔍 Phase 3: Design Review and Refinement\n")
        
        review_prompt = f"""
        Review this system design for the Jira authentication feature:
        
        ORIGINAL DESIGN:
        {design['design']}
        
        REQUIREMENTS:
        {requirements['analysis']}
        
        Please review for:
        1. Completeness - are all requirements covered?
        2. Security - are security best practices followed?
        3. Scalability - will this scale well?
        4. Code quality - is the design maintainable?
        5. Missing pieces - what's missing?
        6. Improvements - what can be better?
        
        Provide:
        - Issues found
        - Recommendations
        - Refined design incorporating improvements
        """
        
        review = await self.design_reviewer.think(review_prompt)
        
        # Save review
        review_file = LOGS_DIR / "02_design_review.md"
        review_file.write_text(review)
        
        return {
            "original_design": design['design'],
            "review": review,
            "requirements": requirements
        }
    
    async def development_phase(self, design: Dict, requirements: Dict) -> Dict:
        """Develop the actual code"""
        print("\n💻 Phase 4: Code Development\n")
        
        code_artifacts = {}
        
        # Backend files to generate
        backend_files = [
            "app/models.py - UserSession model",
            "app/schemas.py - Auth schemas",
            "app/api/auth.py - Authentication endpoints",
            "app/config.py - Add encryption key config"
        ]
        
        # Frontend files to generate
        frontend_files = [
            "src/contexts/AuthContext.tsx - Authentication context",
            "src/components/Login.tsx - Login component",
            "src/components/ProtectedRoute.tsx - Protected route wrapper",
            "src/App.tsx - Updated with routing",
            "src/services/api.ts - Updated with auth methods"
        ]
        
        all_files = backend_files + frontend_files
        
        for file_spec in all_files:
            file_path, description = file_spec.split(" - ", 1)
            
            print(f"  📝 Generating: {file_path}")
            
            dev_prompt = f"""
            Generate production-ready code for: {file_path}
            Description: {description}
            
            DESIGN CONTEXT:
            {design['review']}
            
            REQUIREMENTS:
            {requirements['system_prompt'][:3000]}
            
            Generate ONLY the code for this specific file.
            Include:
            - All necessary imports
            - Complete implementation
            - Error handling
            - Comments for complex logic
            - Type hints (Python) or TypeScript types
            
            Output format:
            ```[language]
            [complete code]
            ```
            """
            
            code = await self.developer.think(dev_prompt)
            
            # Extract code from markdown
            code_content = self.extract_code_from_markdown(code)
            
            code_artifacts[file_path] = {
                "code": code_content,
                "description": description,
                "raw_response": code
            }
            
            # Save individual file
            artifact_file = LOGS_DIR / f"03_code_{file_path.replace('/', '_')}.txt"
            artifact_file.write_text(code_content)
        
        return code_artifacts
    
    async def code_review_phase(self, code_artifacts: Dict, design: Dict) -> Dict:
        """Review generated code"""
        print("\n🔎 Phase 5: Code Review\n")
        
        reviewed_artifacts = {}
        
        for file_path, artifact in code_artifacts.items():
            print(f"  🔍 Reviewing: {file_path}")
            
            review_prompt = f"""
            Review this code for quality, security, and best practices:
            
            FILE: {file_path}
            DESCRIPTION: {artifact['description']}
            
            CODE:
            ```
            {artifact['code']}
            ```
            
            Check for:
            1. Security vulnerabilities
            2. Error handling
            3. Code quality and readability
            4. Best practices
            5. Type safety
            6. Performance issues
            7. Missing imports or dependencies
            
            Provide:
            - Issues found (with severity: critical, major, minor)
            - Specific recommendations
            - Improved code if critical issues found
            """
            
            review = await self.code_reviewer.think(review_prompt)
            
            reviewed_artifacts[file_path] = {
                **artifact,
                "review": review,
                "needs_revision": "critical" in review.lower() or "major" in review.lower()
            }
            
            # Save review
            review_file = LOGS_DIR / f"04_review_{file_path.replace('/', '_')}.md"
            review_file.write_text(review)
        
        return reviewed_artifacts
    
    async def test_and_refine_phase(self, reviewed_code: Dict, design: Dict) -> Dict:
        """Test code and refine based on errors"""
        print("\n🧪 Phase 6: Testing and Refinement\n")
        
        final_code = {}
        
        for file_path, artifact in reviewed_code.items():
            print(f"  🧪 Testing: {file_path}")
            
            current_code = artifact['code']
            iteration = 0
            
            while iteration < self.workflow_state['max_iterations']:
                # Static analysis
                issues = await self.analyze_code(file_path, current_code)
                
                if not issues or len(issues) == 0:
                    print(f"    ✅ No issues found for {file_path}")
                    break
                
                print(f"    ⚠️  Found {len(issues)} issues, refining... (iteration {iteration + 1})")
                
                # Refine code
                refine_prompt = f"""
                Fix these issues in the code:
                
                FILE: {file_path}
                
                CURRENT CODE:
                ```
                {current_code}
                ```
                
                ISSUES FOUND:
                {json.dumps(issues, indent=2)}
                
                REVIEW FEEDBACK:
                {artifact.get('review', 'No review feedback')}
                
                Provide corrected code that fixes all issues.
                Output only the corrected code in a code block.
                """
                
                refined = await self.debugger.think(refine_prompt)
                current_code = self.extract_code_from_markdown(refined)
                
                iteration += 1
            
            final_code[file_path] = {
                "code": current_code,
                "description": artifact['description'],
                "iterations": iteration
            }
            
            # Save final version
            final_file = LOGS_DIR / f"05_final_{file_path.replace('/', '_')}.txt"
            final_file.write_text(current_code)
        
        return final_code
    
    async def analyze_code(self, file_path: str, code: str) -> List[Dict]:
        """Analyze code for issues"""
        issues = []
        
        # Check for common issues
        if "password" in code.lower() and "plain" in code.lower():
            issues.append({
                "severity": "critical",
                "message": "Possible plain text password storage",
                "line": "unknown"
            })
        
        if file_path.endswith(".py"):
            # Check Python syntax
            try:
                compile(code, file_path, 'exec')
            except SyntaxError as e:
                issues.append({
                    "severity": "critical",
                    "message": f"Syntax error: {e}",
                    "line": e.lineno
                })
        
        # Check for missing imports (simple heuristic)
        if file_path.endswith(".py"):
            if "FastAPI" in code and "from fastapi import" not in code:
                issues.append({
                    "severity": "major",
                    "message": "Missing FastAPI import",
                    "line": "unknown"
                })
        
        if file_path.endswith((".tsx", ".ts")):
            # Check TypeScript/React issues
            if "React" in code and "import React" not in code:
                issues.append({
                    "severity": "major",
                    "message": "Missing React import",
                    "line": "unknown"
                })
        
        return issues
    
    async def generate_final_artifacts(self, final_code: Dict):
        """Generate final code files in proper structure"""
        print("\n📦 Phase 7: Generating Final Artifacts\n")
        
        for file_path, artifact in final_code.items():
            full_path = OUTPUT_DIR / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write code
            full_path.write_text(artifact['code'])
            print(f"  ✅ Generated: {full_path}")
        
        # Generate summary document
        summary = self.generate_summary(final_code)
        summary_file = OUTPUT_DIR / "IMPLEMENTATION_SUMMARY.md"
        summary_file.write_text(summary)
        
        # Generate installation instructions
        instructions = self.generate_instructions(final_code)
        instructions_file = OUTPUT_DIR / "INSTALLATION.md"
        instructions_file.write_text(instructions)
        
        print(f"\n  📄 Generated summary: {summary_file}")
        print(f"  📄 Generated instructions: {instructions_file}")
    
    def extract_code_from_markdown(self, text: str) -> str:
        """Extract code from markdown code blocks"""
        import re
        
        # Try to find code blocks
        pattern = r"```(?:\w+)?\n(.*?)```"
        matches = re.findall(pattern, text, re.DOTALL)
        
        if matches:
            # Return the first (or largest) code block
            return max(matches, key=len).strip()
        
        # If no code blocks, return as is
        return text.strip()
    
    def generate_summary(self, final_code: Dict) -> str:
        """Generate implementation summary"""
        summary = f"""# Jira Authentication Implementation Summary

Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Files Generated

"""
        for file_path, artifact in final_code.items():
            summary += f"### {file_path}\n"
            summary += f"- **Description**: {artifact['description']}\n"
            summary += f"- **Iterations**: {artifact['iterations']}\n"
            summary += f"- **Lines of code**: {len(artifact['code'].split(chr(10)))}\n\n"
        
        summary += """
## Next Steps

1. Review generated code
2. Install dependencies
3. Run database migrations
4. Test authentication flow
5. Deploy to staging environment

## Architecture

The implementation follows a multi-layered architecture:
- **Backend**: FastAPI with SQLAlchemy ORM
- **Frontend**: React with TypeScript
- **Authentication**: Session-based with encrypted token storage
- **Security**: Fernet encryption, CSRF protection, rate limiting

## Testing

Test the following scenarios:
- ✓ Valid login
- ✓ Invalid credentials
- ✓ Session persistence
- ✓ Logout functionality
- ✓ Protected route access
- ✓ Token expiration

"""
        return summary
    
    def generate_instructions(self, final_code: Dict) -> str:
        """Generate installation instructions"""
        return """# Installation Instructions

## Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL database
- OpenSSL

## Backend Setup

1. **Generate encryption key:**
   ```bash
   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   ```

2. **Add to .env file:**
   ```env
   ENCRYPTION_KEY=your_generated_key_here
   SESSION_EXPIRY_HOURS=24
   SESSION_REMEMBER_ME_HOURS=720
   ```

3. **Install dependencies:**
   ```bash
   cd backend
   pip install cryptography python-jose[cryptography]
   ```

4. **Run database migration:**
   ```bash
   alembic revision --autogenerate -m "Add user sessions"
   alembic upgrade head
   ```

5. **Copy generated files to backend:**
   ```bash
   cp generated_code/app/models.py backend/app/models.py
   cp generated_code/app/schemas.py backend/app/schemas.py
   cp generated_code/app/api/auth.py backend/app/api/auth.py
   ```

## Frontend Setup

1. **Install dependencies:**
   ```bash
   cd frontend
   npm install react-router-dom @types/react-router-dom
   ```

2. **Copy generated files:**
   ```bash
   cp -r generated_code/src/* frontend/src/
   ```

3. **Start development server:**
   ```bash
   npm start
   ```

## Testing

1. **Start backend:**
   ```bash
   cd backend
   uvicorn app.main:app --reload
   ```

2. **Start frontend:**
   ```bash
   cd frontend
   npm start
   ```

3. **Test login:**
   - Navigate to http://localhost:3000
   - Enter Jira credentials
   - Verify redirect to dashboard

## Security Checklist

- [ ] HTTPS enabled in production
- [ ] Encryption key stored securely
- [ ] Rate limiting configured
- [ ] CSRF protection enabled
- [ ] Session timeout configured
- [ ] Audit logging enabled

## Troubleshooting

**Issue**: Cannot connect to Jira API
- Verify Jira URL format
- Check API token validity
- Ensure network connectivity

**Issue**: Session not persisting
- Check browser localStorage
- Verify token not expired
- Check backend session table

**Issue**: Import errors
- Run `pip install -r requirements.txt`
- Run `npm install`
- Check Python/Node versions

"""


async def main():
    """Main entry point"""
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║             🤖 AGENTIC AI DEVELOPMENT WORKFLOW SYSTEM 🤖                     ║
║                                                                              ║
║                   Multi-LLM Collaborative Development                        ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
""")
    
    # Check API keys
    if not OPENAI_API_KEY:
        print("❌ Error: OPENAI_API_KEY environment variable not set")
        print("   Set it with: export OPENAI_API_KEY='your-key-here'")
        return
    
    if not ANTHROPIC_API_KEY:
        print("⚠️  Warning: ANTHROPIC_API_KEY not set, will use OpenAI for all agents")
    
    # Create and run orchestrator
    orchestrator = WorkflowOrchestrator()
    await orchestrator.run()


if __name__ == "__main__":
    asyncio.run(main())
