#!/bin/bash
# BrainCell Startup Script - Separate API and Dashboard

echo "=========================================="
echo "  BrainCell - API & Dashboard Startup"
echo "=========================================="
echo ""

# Check Docker
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose not found. Please install Docker Desktop."
    exit 1
fi

echo "Checking Docker services..."

# Start services
echo ""
echo "Starting services..."
docker-compose down > /dev/null 2>&1
docker-compose up -d --build

# Wait for services
echo "⏳ Waiting for services to be healthy..."
sleep 30

# Check status
echo ""
docker-compose ps

echo ""
echo "=========================================="
echo "  Services Running"
echo "=========================================="
echo ""
echo "📡 BrainCell REST API"
echo "   URL: http://localhost:9504"
echo "   Base: http://localhost:9504/api/v1"
echo "   Health: http://localhost:9504/health"
echo ""
echo "🌐 BrainCell Dashboard"
echo "   URL: http://localhost:9507"
echo "   Main: http://localhost:9507/dashboard"
echo ""
echo "📊 Database"
echo "   PostgreSQL: localhost:9500 (braincell / braincell_dev_password)"
echo "   PgAdmin: http://localhost:9505"
echo ""
echo "🔍 Vector Database"
echo "   Weaviate: http://localhost:9501"
echo ""
echo "💾 Cache"
echo "   Redis: localhost:9503"
echo ""
echo "🔧 MCP Server"
echo "   HTTP: http://localhost:9506"
echo ""
echo "=========================================="
echo ""
echo "Logs for API:"
echo "  docker-compose logs -f braincell-api"
echo ""
echo "Logs for Dashboard:"
echo "  docker-compose logs -f braincell-dashboard"
echo ""
echo "Stop services:"
echo "  docker-compose down"
echo ""
