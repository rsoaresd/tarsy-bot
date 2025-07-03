#!/bin/bash

# SRE AI Agent - Quick Setup Script
# This script helps you get started with the SRE AI Agent

set -e

echo "🚀 SRE AI Agent - Quick Setup"
echo "================================"

# Check if we're in the correct directory
if [ ! -f "README.md" ] || [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    echo "❌ Error: Please run this script from the root of the SRE AI Agent project"
    echo "   The script expects to find backend/, frontend/, and README.md"
    exit 1
fi

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to print colored output
print_status() {
    if [ "$1" = "success" ]; then
        echo -e "${GREEN}✓ $2${NC}"
    elif [ "$1" = "error" ]; then
        echo -e "${RED}✗ $2${NC}"
    elif [ "$1" = "warning" ]; then
        echo -e "${YELLOW}⚠ $2${NC}"
    else
        echo "$2"
    fi
}

echo "📋 Checking prerequisites..."

if ! command_exists python3; then
    print_status "error" "Python 3 is not installed. Please install Python 3.11 or higher."
    exit 1
else
    print_status "success" "Python 3 found"
fi

if ! command_exists node; then
    print_status "error" "Node.js is not installed. Please install Node.js 18 or higher."
    exit 1
else
    print_status "success" "Node.js found"
fi

if ! command_exists npx; then
    print_status "error" "npx is not installed. Please install npm/npx."
    exit 1
else
    print_status "success" "npx found (needed for Kubernetes MCP server)"
fi

# Check Python version
python_version=$(python3 --version | cut -d' ' -f2)
python_major=$(echo $python_version | cut -d'.' -f1)
python_minor=$(echo $python_version | cut -d'.' -f2)
if [ $python_major -lt 3 ] || [ $python_major -eq 3 -a $python_minor -lt 11 ]; then
    echo "❌ Error: Python 3.11+ is required. Found: $python_version"
    exit 1
fi

# Check Node version
node_version=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
if [ $node_version -lt 18 ]; then
    echo "❌ Error: Node.js 18+ is required. Found: v$node_version"
    exit 1
fi

print_status "success" "Prerequisites check passed!"

# Setup backend
echo ""
echo "🔧 Setting up backend..."
cd backend

# Check if uv is installed, if not try to install it
if ! command -v uv &> /dev/null; then
    echo "📦 Installing uv package manager..."
    if curl -LsSf https://astral.sh/uv/install.sh | sh; then
        source $HOME/.cargo/env
        if ! command -v uv &> /dev/null; then
            print_status "error" "uv installation failed. Please install uv manually from https://docs.astral.sh/uv/"
            exit 1
        fi
        print_status "success" "uv installed successfully"
    else
        print_status "error" "Failed to install uv. Please install manually from https://docs.astral.sh/uv/"
        exit 1
    fi
else
    print_status "success" "uv package manager found"
fi

# Create virtual environment and install dependencies
echo "📦 Setting up Python environment and dependencies..."
uv sync

# Verify virtual environment was created
if [ ! -d ".venv" ]; then
    print_status "error" "Virtual environment was not created. Please check uv installation."
    exit 1
else
    print_status "success" "Virtual environment and dependencies installed"
fi

# Setup environment file
if [ ! -f ".env" ]; then
    echo "📝 Creating environment configuration..."
    cp env.template .env
    echo ""
    echo "⚠️  IMPORTANT: Edit backend/.env with your API keys!"
    echo "   You need at least one LLM API key (Google/OpenAI/xAI) and a GitHub token."
    echo ""
else
    print_status "success" ".env file already exists"
fi

cd ..

# Setup frontend
echo ""
echo "🔧 Setting up frontend..."
cd frontend

echo "📦 Installing Node.js dependencies..."
npm install

# Verify node_modules was created
if [ ! -d "node_modules" ]; then
    print_status "error" "Node.js dependencies installation failed."
    exit 1
else
    print_status "success" "Node.js dependencies installed"
fi

cd ..

echo ""
echo "🎉 Setup completed successfully!"
echo ""
echo "📋 Next steps:"
echo "1. Edit backend/.env with your API keys:"
echo "   - Get Google (Gemini) API key: https://aistudio.google.com/app/apikey"
echo "   - Get OpenAI API key: https://platform.openai.com/api-keys"
echo "   - Get xAI (Grok) API key: https://console.x.ai/"
echo "   - Get GitHub token: https://github.com/settings/tokens"
echo ""
echo "2. Start the Kubernetes MCP Server:"
echo "   For testing: The MCP server is automatically started using npx"
echo "   For production: Set up your own Kubernetes MCP server"
echo "   Alternative: Use the mock server script in DEPLOYMENT.md"
echo ""
echo "3. Start the backend (in a new terminal):"
echo "   cd backend"
echo "   source .venv/bin/activate"
echo "   uvicorn app.main:app --reload --port 8000"
echo ""
echo "4. Start the frontend (in another terminal):"
echo "   cd frontend"
echo "   PORT=3001 npm start"
echo ""
echo "5. Open your browser to: http://localhost:3001"
echo ""
echo "🔗 Useful links:"
echo "   - Frontend: http://localhost:3001"
echo "   - Backend API: http://localhost:8000"
echo "   - API Docs: http://localhost:8000/docs"
echo ""
echo "📚 For more information, see README.md and DEPLOYMENT.md"

# Test MCP integration (optional)
echo -e "\n❓ Would you like to test the MCP integration? (y/n)"
read -r response
if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    cd backend
    source .venv/bin/activate || . .venv/Scripts/activate
    echo "🧪 Running MCP integration test..."
    if python test_mcp_integration.py; then
        print_status "success" "MCP integration test passed"
    else
        print_status "warning" "MCP integration test failed - check your environment configuration"
    fi
fi 