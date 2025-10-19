#!/bin/bash
# Setup script for Agentic AI Development Workflow

set -e

echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║                                                                              ║"
echo "║          🤖 Agentic AI Development Workflow - Setup Script 🤖                ║"
echo "║                                                                              ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo ""

# Check Python version
echo "📋 Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
required_version="3.11"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then 
    echo "❌ Error: Python $required_version or higher is required"
    echo "   Current version: $python_version"
    exit 1
fi
echo "✅ Python version: $python_version"
echo ""

# Create virtual environment (optional but recommended)
echo "🔧 Setting up Python virtual environment..."
if [ ! -d "venv_agentic" ]; then
    python3 -m venv venv_agentic
    echo "✅ Virtual environment created"
else
    echo "ℹ️  Virtual environment already exists"
fi
echo ""

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv_agentic/bin/activate
echo "✅ Virtual environment activated"
echo ""

# Upgrade pip
echo "📦 Upgrading pip..."
pip install --upgrade pip > /dev/null 2>&1
echo "✅ pip upgraded"
echo ""

# Install dependencies
echo "📚 Installing dependencies from requirements_agentic.txt..."
pip install -r requirements_agentic.txt
echo "✅ Dependencies installed"
echo ""

# Check for .env file
echo "🔐 Checking for API keys configuration..."
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found"
    echo "   Creating .env from .env.example..."
    cp .env.example .env
    echo "✅ .env file created"
    echo ""
    echo "⚠️  IMPORTANT: Edit .env file and add your API keys:"
    echo "   - OPENAI_API_KEY (required)"
    echo "   - ANTHROPIC_API_KEY (optional but recommended)"
    echo ""
    echo "   Edit with: nano .env"
else
    echo "✅ .env file exists"
fi
echo ""

# Check if API keys are set
echo "🔍 Verifying API keys..."
source .env

if [ -z "$OPENAI_API_KEY" ] || [ "$OPENAI_API_KEY" = "sk-your-openai-api-key-here" ]; then
    echo "❌ OPENAI_API_KEY is not set or using example value"
    echo "   Please edit .env file and add your OpenAI API key"
    echo ""
    echo "   Get your key at: https://platform.openai.com/api-keys"
    API_KEYS_SET=false
else
    echo "✅ OPENAI_API_KEY is set"
    API_KEYS_SET=true
fi

if [ -z "$ANTHROPIC_API_KEY" ] || [ "$ANTHROPIC_API_KEY" = "sk-ant-your-anthropic-api-key-here" ]; then
    echo "⚠️  ANTHROPIC_API_KEY is not set (optional)"
    echo "   For better results, add your Anthropic API key to .env"
    echo "   Get your key at: https://console.anthropic.com/"
else
    echo "✅ ANTHROPIC_API_KEY is set"
fi
echo ""

# Make script executable
echo "🔧 Making develop_jira_auth.py executable..."
chmod +x develop_jira_auth.py
echo "✅ Script is now executable"
echo ""

# Create necessary directories
echo "📁 Creating output directories..."
mkdir -p generated_code
mkdir -p development_logs
echo "✅ Directories created"
echo ""

# Setup complete
echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║                                                                              ║"
echo "║                         ✅ Setup Complete! ✅                                 ║"
echo "║                                                                              ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo ""

if [ "$API_KEYS_SET" = true ]; then
    echo "🚀 Ready to run! Execute the workflow with:"
    echo ""
    echo "   python develop_jira_auth.py"
    echo ""
    echo "   Or with virtual environment:"
    echo "   source venv_agentic/bin/activate && python develop_jira_auth.py"
else
    echo "⚠️  Before running, please:"
    echo ""
    echo "   1. Edit .env file and add your API keys:"
    echo "      nano .env"
    echo ""
    echo "   2. Then run the workflow:"
    echo "      python develop_jira_auth.py"
fi
echo ""
echo "📚 For more information, see: README_AGENTIC_WORKFLOW.md"
echo ""
