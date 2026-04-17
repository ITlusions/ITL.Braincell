#!/bin/bash
# Cleanup script for BrainCell src/ root folder reorganization
# Run this script to remove old files that have been moved to new locations

echo "🧹 BrainCell Root Folder Cleanup"
echo "=================================="
echo ""
echo "This script will remove OLD files that have been moved to new locations."
echo ""

# OLD FILES TO REMOVE (moved to new locations)
echo "FILES TO REMOVE:"
echo "├─ src/models.py           (moved to src/core/models.py)"
echo "├─ src/schemas.py          (moved to src/core/schemas.py)"
echo "├─ src/weaviate_service.py (moved to src/services/weaviate_service.py)"
echo ""

# MCP SERVER FILES (to be organized into src/mcp/)
echo "MCP SERVER FILES (TO ORGANIZE):"
echo "├─ src/mcp_server.py       → src/mcp/server.py"
echo "├─ src/mcp_server_http.py  → src/mcp/server_http.py"
echo "├─ src/mcp_server_lean.py  → src/mcp/server_lean.py"
echo "├─ src/mcp_server_stdio.py → src/mcp/server_stdio.py"
echo ""

echo "⚠️  IMPORTANT: Before cleanup:"
echo "1. Verify imports are updated in database.py and main_new.py"
echo "2. Run: python -c \"from src.core import models, schemas; print('✓ OK')\""
echo "3. Run: python -m uvicorn src.main_new:app --reload (test startup)"
echo ""

# Check if running interactively
if [ -t 0 ]; then
    read -p "Proceed with cleanup? (yes/no): " confirm
    if [ "$confirm" = "yes" ]; then
        echo ""
        echo "🗑️  Removing old files..."
        rm -f src/models.py
        rm -f src/schemas.py
        rm -f src/weaviate_service.py
        echo "✓ Old duplicate files removed"
        echo ""
        echo "📦 MCP server files (action required manually):"
        echo "   Move these files to src/mcp/ with these commands:"
        echo "   mv src/mcp_server.py src/mcp/server.py"
        echo "   mv src/mcp_server_http.py src/mcp/server_http.py"
        echo "   mv src/mcp_server_lean.py src/mcp/server_lean.py"
        echo "   mv src/mcp_server_stdio.py src/mcp/server_stdio.py"
        echo ""
        echo "✅ Cleanup complete!"
    else
        echo "Cleanup cancelled."
    fi
else
    echo "Run interactively to proceed with cleanup."
fi
