#!/bin/bash

# SRE AI Agent - Quick Setup Script
# This script helps you get started with the SRE AI Agent

set -e

echo "🚀 SRE AI Agent - Quick Setup"
echo "================================"

# Check if required commands exist
check_command() {
    if ! command -v $1 &> /dev/null; then
        echo "❌ Error: $1 is not installed. Please install it first."
        exit 1
    fi
}

echo "📋 Checking prerequisites..."
check_command "python3"
check_command "node"
check_command "npm"

# Check Python version
python_version=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
if [ $(echo "$python_version >= 3.11" | bc -l) -eq 0 ]; then
    echo "❌ Error: Python 3.11+ is required. Found: $python_version"
    exit 1
fi

# Check Node version
node_version=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
if [ $node_version -lt 18 ]; then
    echo "❌ Error: Node.js 18+ is required. Found: v$node_version"
    exit 1
fi

echo "✅ Prerequisites check passed!"

# Setup backend
echo ""
echo "🔧 Setting up backend..."
cd backend

# Check if uv is installed, if not try to install it
if ! command -v uv &> /dev/null; then
    echo "📦 Installing uv package manager..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    source $HOME/.cargo/env
fi

# Create virtual environment and install dependencies
echo "📦 Creating Python virtual environment..."
uv venv

echo "📦 Installing Python dependencies..."
source .venv/bin/activate
uv pip install -r requirements.txt

# Setup environment file
if [ ! -f ".env" ]; then
    echo "📝 Creating environment configuration..."
    cp env.template .env
    echo ""
    echo "⚠️  IMPORTANT: Edit backend/.env with your API keys!"
    echo "   You need at least one LLM API key and a GitHub token."
    echo ""
else
    echo "✅ Environment file already exists"
fi

cd ..

# Setup frontend
echo ""
echo "🔧 Setting up frontend..."
cd frontend

echo "📦 Installing Node.js dependencies..."
npm install

cd ..

echo ""
echo "🎉 Setup completed successfully!"
echo ""
echo "📋 Next steps:"
echo "1. Edit backend/.env with your API keys:"
echo "   - Get Gemini API key: https://aistudio.google.com/app/apikey"
echo "   - Get OpenAI API key: https://platform.openai.com/api-keys"
echo "   - Get GitHub token: https://github.com/settings/tokens"
echo ""
echo "2. Start the Kubernetes MCP Server (or use mock server):"
echo "   python3 -c \"
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class MockMCPHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'healthy'}).encode())
        elif self.path == '/tools':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            tools = {'tools': [{'name': 'get_namespace', 'description': 'Get namespace info'}]}
            self.wfile.write(json.dumps(tools).encode())
    
    def do_POST(self):
        if self.path == '/tools/call':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            result = {'status': 'success', 'data': 'Mock MCP response'}
            self.wfile.write(json.dumps(result).encode())

server = HTTPServer(('localhost', 8080), MockMCPHandler)
print('Mock MCP Server running on http://localhost:8080')
server.serve_forever()
\""
echo ""
echo "3. Start the backend (in a new terminal):"
echo "   cd backend"
echo "   source .venv/bin/activate"
echo "   uvicorn app.main:app --reload --port 8000"
echo ""
echo "4. Start the frontend (in another terminal):"
echo "   cd frontend"
echo "   npm start"
echo ""
echo "5. Open your browser to: http://localhost:3001"
echo ""
echo "🔗 Useful links:"
echo "   - Frontend: http://localhost:3001"
echo "   - Backend API: http://localhost:8000"
echo "   - API Docs: http://localhost:8000/docs"
echo ""
echo "📚 For more information, see README.md and DEPLOYMENT.md" 