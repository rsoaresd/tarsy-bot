# SRE AI Agent - Deployment Guide

This guide will help you deploy and run the SRE AI Agent in your environment.

## Prerequisites

### Required Software
- **Python 3.11+** with uv package manager
- **Node.js 18+** with npm
- **Docker & Docker Compose** (for containerized deployment)
- **Kubernetes MCP Server** (see MCP Setup section)

### Required API Keys
- **LLM Provider API Key** (at least one):
  - Gemini API key from Google AI Studio
  - OpenAI API key 
  - Grok API key from X.AI
- **GitHub Token** (for private runbooks)

## Quick Start (Development)

### 1. Clone and Setup Environment

```bash
# Copy environment template
cp .env.example backend/.env

# Edit the environment file with your API keys
vim backend/.env
```

### 2. Configure Environment Variables

Edit `backend/.env`:

```env
# LLM API Keys (at least one required)
GEMINI_API_KEY=your_gemini_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
GROK_API_KEY=your_grok_api_key_here

# GitHub Configuration
GITHUB_TOKEN=your_github_token_here

# MCP Server Configuration
KUBERNETES_MCP_URL=http://localhost:8080

# Application Settings
DEFAULT_LLM_PROVIDER=gemini
LOG_LEVEL=INFO
HOST=0.0.0.0
PORT=8000
CORS_ORIGINS=http://localhost:3001,http://127.0.0.1:3001
```

### 3. Start Backend

```bash
cd backend

# Create virtual environment
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
uv pip install -r requirements.txt

# Run the FastAPI server
uvicorn app.main:app --reload --port 8000
```

### 4. Start Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm start
```

### 5. Access the Application

- **Frontend**: http://localhost:3001
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## MCP Server Setup

### Kubernetes MCP Server

The application requires a Kubernetes MCP Server to gather system information. 

#### Option 1: Use the Reference Implementation

```bash
# Clone the Kubernetes MCP server
git clone https://github.com/manusa/kubernetes-mcp-server
cd kubernetes-mcp-server

# Follow the setup instructions in that repository
# Ensure it's running on localhost:8080
```

#### Option 2: Mock MCP Server (Testing)

For testing without a real Kubernetes cluster:

```bash
# Run a simple mock server
python -c "
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
"
```

## Docker Deployment

### 1. Build and Run with Docker Compose

```bash
# Build all services
docker-compose build

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f
```

### 2. Individual Service Deployment

#### Backend Docker

```bash
cd backend

# Create Dockerfile
cat > Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# Install uv
RUN pip install uv

# Copy requirements
COPY requirements.txt .
RUN uv pip install --system -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
EOF

# Build and run
docker build -t sre-ai-agent-backend .
docker run -p 8000:8000 --env-file .env sre-ai-agent-backend
```

#### Frontend Docker

```bash
cd frontend

# Create Dockerfile
cat > Dockerfile << 'EOF'
FROM node:18-alpine as builder

WORKDIR /app
COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
EOF

# Create nginx.conf
cat > nginx.conf << 'EOF'
server {
    listen 80;
    location / {
        root /usr/share/nginx/html;
        index index.html index.htm;
        try_files $uri $uri/ /index.html;
    }
    
    location /api {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
EOF

# Build and run
docker build -t sre-ai-agent-frontend .
docker run -p 3000:80 sre-ai-agent-frontend
```

## Production Deployment

### 1. Environment Setup

```bash
# Create production environment file
cp .env.example .env.prod

# Set production values
vim .env.prod
```

### 2. Security Considerations

- **API Keys**: Store in secure key management system
- **CORS**: Configure proper CORS origins for production domain
- **HTTPS**: Enable SSL/TLS for all communications
- **Authentication**: Add authentication layer for production use
- **Rate Limiting**: Implement rate limiting for API endpoints

### 3. Kubernetes Deployment

Create Kubernetes manifests:

```yaml
# backend-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: sre-ai-agent-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: sre-ai-agent-backend
  template:
    metadata:
      labels:
        app: sre-ai-agent-backend
    spec:
      containers:
      - name: backend
        image: sre-ai-agent-backend:latest
        ports:
        - containerPort: 8000
        envFrom:
        - secretRef:
            name: sre-ai-agent-secrets
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
---
apiVersion: v1
kind: Service
metadata:
  name: sre-ai-agent-backend-service
spec:
  selector:
    app: sre-ai-agent-backend
  ports:
  - port: 8000
    targetPort: 8000
  type: ClusterIP
```

## Testing the Deployment

### 1. Health Check

```bash
# Backend health
curl http://localhost:8000/health

# Expected response:
# {"status": "healthy", "service": "sre-ai-agent"}
```

### 2. Test Alert Submission

```bash
# Submit a test alert
curl -X POST http://localhost:8000/alerts \
  -H "Content-Type: application/json" \
  -d '{
    "alert": "Namespace is stuck in Terminating",
    "severity": "warning",
    "environment": "production",
    "cluster": "https://api.test-cluster.example.com:6443",
    "namespace": "test-namespace",
    "message": "namespace is stuck in Terminating phase",
    "runbook": "https://github.com/codeready-toolchain/sandbox-sre/blob/master/runbooks/namespace-terminating.md"
  }'

# Expected response:
# {"alert_id": "uuid-here", "status": "queued", "message": "Alert submitted for processing"}
```

### 3. Monitor Processing

```bash
# Check processing status
curl http://localhost:8000/processing-status/{alert_id}

# Or connect to WebSocket for real-time updates
# ws://localhost:8000/ws/{alert_id}
```

## Troubleshooting

### Common Issues

1. **Backend fails to start**
   - Check API keys are set correctly
   - Verify Python dependencies are installed
   - Check port 8000 is available

2. **Frontend can't connect to backend**
   - Verify backend is running on port 8000
   - Check CORS configuration
   - Verify proxy setting in package.json

3. **MCP Server connection failed**
   - Ensure Kubernetes MCP server is running on port 8080
   - Check network connectivity
   - Verify MCP server is responding to health checks

4. **LLM API errors**
   - Verify API keys are valid and have sufficient quota
   - Check internet connectivity
   - Try different LLM provider

### Logs

```bash
# Backend logs
tail -f backend/logs/app.log

# Docker logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Check specific service
docker logs sre-ai-agent-backend
```

## Monitoring

### Health Endpoints

- `GET /health` - Backend health status
- `GET /` - Basic service status
- `GET /alert-types` - Supported alert types

### Metrics

Consider implementing:
- Processing time metrics
- Success/failure rates
- LLM token usage
- WebSocket connection counts

## Support

For issues and questions:
1. Check the logs for error messages
2. Verify all prerequisites are met
3. Test with a simple alert submission
4. Check MCP server connectivity

The SRE AI Agent is now ready for deployment and use! 