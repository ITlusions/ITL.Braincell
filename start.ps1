@echo off
REM BrainCell Startup Script - Separate API and Dashboard

echo.
echo ==========================================
echo   BrainCell - API ^& Dashboard Startup
echo ==========================================
echo.

REM Check Docker
where docker-compose >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo 💥 docker-compose not found. Please install Docker Desktop.
    exit /b 1
)

echo Checking Docker services...
echo.

REM Start services
echo Starting services...
docker-compose down >nul 2>nul
docker-compose up -d --build

REM Wait for services
echo.
echo ⏳ Waiting for services to be healthy...
timeout /t 30 /nobreak

REM Check status
echo.
docker-compose ps

echo.
echo ==========================================
echo   Services Running
echo ==========================================
echo.
echo 📡 BrainCell REST API
echo    URL: http://localhost:9504
echo    Base: http://localhost:9504/api/v1
echo    Health: http://localhost:9504/health
echo.
echo 🌐 BrainCell Dashboard
echo    URL: http://localhost:9507
echo    Main: http://localhost:9507/dashboard
echo.
echo 📊 Database
echo    PostgreSQL: localhost:9500 (braincell / braincell_dev_password)
echo    PgAdmin: http://localhost:9505
echo.
echo 🔍 Vector Database
echo    Weaviate: http://localhost:9501
echo.
echo 💾 Cache
echo    Redis: localhost:9503
echo.
echo 🔧 MCP Server
echo    HTTP: http://localhost:9506
echo.
echo ==========================================
echo.
echo Logs for API:
echo   docker-compose logs -f braincell-api
echo.
echo Logs for Dashboard:
echo   docker-compose logs -f braincell-dashboard
echo.
echo Stop services:
echo   docker-compose down
echo.
pause
