#!/usr/bin/env python3
"""
Test script to verify the agentic workflow setup
"""

import os
import sys
from pathlib import Path

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ python-dotenv loaded successfully")
except ImportError:
    print("❌ python-dotenv not installed")
    print("   Install with: pip install python-dotenv")
    sys.exit(1)

print("\n" + "="*80)
print("🧪 Testing Agentic AI Workflow Setup")
print("="*80 + "\n")

# Test 1: Check Python version
print("1️⃣  Checking Python version...")
import sys
version = sys.version_info
if version.major >= 3 and version.minor >= 11:
    print(f"   ✅ Python {version.major}.{version.minor}.{version.micro}")
else:
    print(f"   ❌ Python {version.major}.{version.minor}.{version.micro} (need 3.11+)")
    sys.exit(1)

# Test 2: Check OpenAI
print("\n2️⃣  Checking OpenAI setup...")
try:
    import openai
    print("   ✅ openai package installed")
    
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key and api_key.startswith("sk-") and len(api_key) > 20:
        print(f"   ✅ OPENAI_API_KEY is set (length: {len(api_key)})")
    else:
        print("   ❌ OPENAI_API_KEY not properly set")
        print("      Please set it in .env file")
except ImportError:
    print("   ❌ openai package not installed")
    print("      Install with: pip install openai")

# Test 3: Check Anthropic
print("\n3️⃣  Checking Anthropic setup...")
try:
    from anthropic import Anthropic
    print("   ✅ anthropic package installed")
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if api_key and api_key.startswith("sk-ant-") and len(api_key) > 20:
        print(f"   ✅ ANTHROPIC_API_KEY is set (length: {len(api_key)})")
    else:
        print("   ⚠️  ANTHROPIC_API_KEY not set (optional)")
        print("      Will use OpenAI for all agents")
except ImportError:
    print("   ⚠️  anthropic package not installed (optional)")
    print("      Install with: pip install anthropic")

# Test 4: Check required directories
print("\n4️⃣  Checking directory structure...")
workspace = Path("/workspace")
prompts_dir = workspace / "doc" / "prompts"
output_dir = workspace / "agentic" / "generated_code"
logs_dir = workspace / "agentic" / "development_logs"

dirs_ok = True
if prompts_dir.exists():
    print(f"   ✅ {prompts_dir}")
else:
    print(f"   ❌ {prompts_dir} not found")
    dirs_ok = False

if output_dir.exists():
    print(f"   ✅ {output_dir}")
else:
    print(f"   ℹ️  {output_dir} will be created")
    output_dir.mkdir(parents=True, exist_ok=True)

if logs_dir.exists():
    print(f"   ✅ {logs_dir}")
else:
    print(f"   ℹ️  {logs_dir} will be created")
    logs_dir.mkdir(parents=True, exist_ok=True)

# Test 5: Check prompt files
print("\n5️⃣  Checking prompt files...")
user_prompt = prompts_dir / "user_prompt.md"
system_prompt = prompts_dir / "system_prompt.md"

files_ok = True
if user_prompt.exists():
    size = user_prompt.stat().st_size
    print(f"   ✅ user_prompt.md ({size} bytes)")
else:
    print(f"   ❌ user_prompt.md not found")
    files_ok = False

if system_prompt.exists():
    size = system_prompt.stat().st_size
    print(f"   ✅ system_prompt.md ({size} bytes)")
else:
    print(f"   ❌ system_prompt.md not found")
    files_ok = False

# Test 6: Test OpenAI connection (optional)
print("\n6️⃣  Testing OpenAI API connection...")
api_key = os.getenv("OPENAI_API_KEY")
if api_key and api_key.startswith("sk-") and len(api_key) > 20:
    try:
        import openai
        openai.api_key = api_key
        
        # Simple test - list models
        response = openai.Model.list()
        print("   ✅ OpenAI API connection successful")
        print(f"      Available models: {len(response['data'])} models found")
    except Exception as e:
        print(f"   ❌ OpenAI API connection failed: {e}")
        print("      Check your API key and internet connection")
else:
    print("   ⏭️  Skipping (API key not set)")

# Test 7: Check other dependencies
print("\n7️⃣  Checking other dependencies...")
deps_ok = True

try:
    import aiohttp
    print("   ✅ aiohttp")
except ImportError:
    print("   ❌ aiohttp not installed")
    deps_ok = False

try:
    import asyncio
    print("   ✅ asyncio")
except ImportError:
    print("   ❌ asyncio not installed")
    deps_ok = False

# Final summary
print("\n" + "="*80)
print("📊 Setup Summary")
print("="*80 + "\n")

all_ok = True

if version.major >= 3 and version.minor >= 11:
    print("✅ Python version")
else:
    print("❌ Python version")
    all_ok = False

try:
    import openai
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key and api_key.startswith("sk-") and len(api_key) > 20:
        print("✅ OpenAI setup")
    else:
        print("❌ OpenAI API key")
        all_ok = False
except:
    print("❌ OpenAI setup")
    all_ok = False

if dirs_ok:
    print("✅ Directory structure")
else:
    print("❌ Directory structure")
    all_ok = False

if files_ok:
    print("✅ Prompt files")
else:
    print("❌ Prompt files")
    all_ok = False

print("\n" + "="*80)
if all_ok:
    print("✅ All tests passed! Ready to run the workflow.")
    print("\nRun with:")
    print("   python develop_jira_auth.py")
else:
    print("❌ Some tests failed. Please fix the issues above.")
    print("\nCommon fixes:")
    print("   • Install dependencies: pip install -r requirements_agentic.txt")
    print("   • Set API keys in .env file")
    print("   • Create prompt files in doc/prompts/")
print("="*80 + "\n")

sys.exit(0 if all_ok else 1)
