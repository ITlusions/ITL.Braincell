# BrainCell Setup Script for Local Development (Windows PowerShell)

Write-Host "🧠 BrainCell Local Setup" -ForegroundColor Cyan
Write-Host "========================" -ForegroundColor Cyan

# Check Python version
Write-Host "Checking Python version..." -ForegroundColor Yellow
$python_version = (python --version 2>&1) -replace "Python ", ""
Write-Host "Found Python $python_version"

# Create virtual environment
Write-Host "Creating virtual environment..." -ForegroundColor Yellow
if (-not (Test-Path "venv")) {
    python -m venv venv
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& .\venv\Scripts\Activate.ps1

# Install dependencies
Write-Host "Installing dependencies..." -ForegroundColor Yellow
python -m pip install --upgrade pip
pip install -r requirements.txt

# Create .env if not exists
if (-not (Test-Path ".env")) {
    Write-Host "Creating .env file..." -ForegroundColor Yellow
    Copy-Item .env.example .env
    Write-Host "✅ Created .env file (update with your settings)"
}

Write-Host ""
Write-Host "✅ Setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Make sure PostgreSQL, Weaviate, and Redis are running locally"
Write-Host "2. Update .env with your local configuration"
Write-Host "3. Run: python -m uvicorn src.main:app --reload"
Write-Host "4. Or run: docker-compose up -d (for full Docker setup)"
Write-Host ""
