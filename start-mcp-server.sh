#!/bin/bash

# BrainCell MCP Server Quick Start
# This script starts all BrainCell services with the MCP server

set -e

echo "================================"
echo "BrainCell MCP Server Quick Start"
echo "================================"
echo ""

# Check if Docker is running
if ! command -v docker &> /dev/null; then
    echo "❌ Error: Docker is not installed or not in PATH"
    exit 1
fi

# Check if Docker Compose is running
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Error: Docker Compose is not installed or not in PATH"
    exit 1
fi

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "📁 Working directory: $SCRIPT_DIR"
echo ""

# Start services
echo "🚀 Starting BrainCell services with Docker Compose..."
cd "$SCRIPT_DIR"

docker-compose up -d postgres weaviate redis braincell-api braincell-mcp pgadmin

echo ""
echo "⏳ Waiting for services to be healthy..."
echo ""

# Function to wait for a service
wait_for_service() {
    local service=$1
    local url=$2
    local max_attempts=30
    local attempt=1
    
    echo "   Checking $service..."
    while [ $attempt -le $max_attempts ]; do
        if curl -f "$url" > /dev/null 2>&1; then
            echo "   ✓ $service is ready"
            return 0
        fi
        echo "   ⏳ Waiting for $service... (attempt $attempt/$max_attempts)"
        sleep 2
        ((attempt++))
    done
    
    echo "   ⚠ $service did not become ready in time"
    return 1
}

# Wait for all services
wait_for_service "BrainCell API" "http://localhost:9504/health"
wait_for_service "BrainCell MCP Server" "http://localhost:9506/health"
wait_for_service "PostgreSQL" "localhost:9500" || true
wait_for_service "Weaviate" "http://localhost:9501/v1/.well-known/ready"

echo ""
echo "================================"
echo "✅ BrainCell is Ready!"
echo "================================"
echo ""
echo "📍 Service Endpoints:"
echo "   • BrainCell API:      http://localhost:9504"
echo "   • API Docs:           http://localhost:9504/docs"
echo "   • MCP Server:         http://localhost:9506"
echo "   • MCP Tools:          http://localhost:9506/tools"
echo "   • Weaviate Console:   http://localhost:9501"
echo "   • PostgreSQL:         localhost:9500"
echo "   • Redis:              localhost:9503"
echo "   • PgAdmin:            http://localhost:9505"
echo ""
echo "📚 Documentation:"
echo "   • Main README:        ./README.md"
echo "   • MCP Server Guide:   ./MCP_SERVER_GUIDE.md"
echo "   • Quick Start:        ./QUICK_START.md"
echo ""
echo "🧪 Test the MCP Server:"
echo ""
echo "   # List available tools"
echo "   curl http://localhost:9506/tools"
echo ""
echo "   # Check health"
echo "   curl http://localhost:9506/health"
echo ""
echo "   # Search memory"
echo "   curl -X POST http://localhost:9506/tools/search_memory \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"query\": \"your search query\"}'"
echo ""
echo "✋ To stop services:"
echo "   docker-compose down"
echo ""
echo "📖 For more information, see MCP_SERVER_GUIDE.md"
echo ""
