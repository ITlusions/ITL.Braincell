# PowerShell cleanup script for BrainCell src/ root folder reorganization
# Run this script to remove old files that have been moved to new locations

Write-Host "🧹 BrainCell Root Folder Cleanup" -ForegroundColor Green
Write-Host "==================================" -ForegroundColor Green
Write-Host ""

Write-Host "OLD FILES TO REMOVE:" -ForegroundColor Yellow
Write-Host "├─ src\models.py           (moved to src\core\models.py)"
Write-Host "├─ src\schemas.py          (moved to src\core\schemas.py)"
Write-Host "├─ src\weaviate_service.py (moved to src\services\weaviate_service.py)"
Write-Host ""

Write-Host "MCP SERVER FILES (TO ORGANIZE):" -ForegroundColor Yellow
Write-Host "├─ src\mcp_server.py       → src\mcp\server.py"
Write-Host "├─ src\mcp_server_http.py  → src\mcp\server_http.py"
Write-Host "├─ src\mcp_server_lean.py  → src\mcp\server_lean.py"
Write-Host "├─ src\mcp_server_stdio.py → src\mcp\server_stdio.py"
Write-Host ""

Write-Host "⚠️  IMPORTANT: Before cleanup:" -ForegroundColor Red
Write-Host "1. Verify imports are updated in database.py and main_new.py"
Write-Host "2. Run: python -c `"from src.core import models, schemas; print('✓ OK')`""
Write-Host "3. Run: python -m uvicorn src.main_new:app --reload (test startup)"
Write-Host ""

$confirm = Read-Host "Proceed with cleanup? (yes/no)"

if ($confirm -eq "yes") {
    Write-Host ""
    Write-Host "🗑️  Removing old files..." -ForegroundColor Cyan
    
    if (Test-Path "src\models.py") {
        Remove-Item "src\models.py" -Force
        Write-Host "✓ Removed src\models.py"
    }
    
    if (Test-Path "src\schemas.py") {
        Remove-Item "src\schemas.py" -Force
        Write-Host "✓ Removed src\schemas.py"
    }
    
    if (Test-Path "src\weaviate_service.py") {
        Remove-Item "src\weaviate_service.py" -Force
        Write-Host "✓ Removed src\weaviate_service.py"
    }
    
    Write-Host ""
    Write-Host "✓ Old duplicate files removed" -ForegroundColor Green
    Write-Host ""
    Write-Host "📦 MCP server files (manual action required):" -ForegroundColor Yellow
    Write-Host "   Move these files to src\mcp\ with these commands:"
    Write-Host "   Move-Item src\mcp_server.py src\mcp\server.py"
    Write-Host "   Move-Item src\mcp_server_http.py src\mcp\server_http.py"
    Write-Host "   Move-Item src\mcp_server_lean.py src\mcp\server_lean.py"
    Write-Host "   Move-Item src\mcp_server_stdio.py src\mcp\server_stdio.py"
    Write-Host ""
    Write-Host "✅ Cleanup complete!" -ForegroundColor Green
} else {
    Write-Host "Cleanup cancelled."
}
