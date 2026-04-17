# Test Execution Script for get_relevant_context Tests
# Usage: .\run_tests.ps1 -TestType functional

param(
    [ValidateSet('functional', 'edge', 'state', 'performance', 'integration', 'critical', 'all', 'coverage', 'clean')]
    [string]$TestType = 'all',
    
    [switch]$Verbose,
    [switch]$KeepVenv
)

# Color functions
function Write-Header {
    param([string]$Message)
    Write-Host "=== $Message ===" -ForegroundColor Cyan
}

function Write-Success {
    param([string]$Message)
    Write-Host "✓ $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "⚠ $Message" -ForegroundColor Yellow
}

function Write-Error-Custom {
    param([string]$Message)
    Write-Host "✗ $Message" -ForegroundColor Red
}

# Test configuration
$TestDir = "tests"
$TestFile = "test_get_relevant_context.py"
$VenvPath = ".venv"
$PythonCmd = "python"

# Check Python installation
try {
    $PythonVersion = & $PythonCmd --version 2>&1
    Write-Success "Python found: $PythonVersion"
} catch {
    Write-Error-Custom "Python not found in PATH"
    exit 1
}

# Create virtual environment if needed
if (-not (Test-Path $VenvPath)) {
    Write-Warning "Virtual environment not found. Creating..."
    & $PythonCmd -m venv $VenvPath
    
    # Activate venv and install requirements
    $ActivateScript = Join-Path $VenvPath "Scripts" "Activate.ps1"
    & $ActivateScript
    pip install -q -r requirements.txt
    Write-Success "Virtual environment created and requirements installed"
} else {
    # Activate existing venv
    $ActivateScript = Join-Path $VenvPath "Scripts" "Activate.ps1"
    & $ActivateScript
}

# Check test file
$TestPath = Join-Path $TestDir $TestFile
if (-not (Test-Path $TestPath)) {
    Write-Error-Custom "Test file not found: $TestPath"
    exit 1
}

# Execute tests based on type
switch ($TestType) {
    "functional" {
        Write-Header "Running Functional Tests"
        pytest -m functional "$TestPath" -v --tb=short
    }
    
    "edge" {
        Write-Header "Running Edge Case Tests"
        pytest -m edge "$TestPath" -v --tb=short
    }
    
    "state" {
        Write-Header "Running Memory State Tests"
        pytest -m state "$TestPath" -v --tb=short
    }
    
    "performance" {
        Write-Header "Running Performance Tests"
        pytest -m performance "$TestPath" -v --tb=short --timeout=60
    }
    
    "integration" {
        Write-Header "Running Integration Tests"
        pytest -m integration "$TestPath" -v --tb=short
    }
    
    "critical" {
        Write-Header "Running Critical Path Tests"
        pytest -m critical "$TestPath" -v --tb=short
    }
    
    "all" {
        Write-Header "Running ALL Tests"
        pytest "$TestPath" -v --tb=short
    }
    
    "coverage" {
        Write-Header "Running Tests with Coverage Report"
        pytest "$TestPath" --cov=src --cov-report=html --cov-report=term-missing
    }
    
    "clean" {
        Write-Header "Cleaning up test artifacts"
        Get-ChildItem -Path . -Name "__pycache__" -Recurse -Directory | ForEach-Object { 
            Remove-Item $_ -Recurse -Force -ErrorAction SilentlyContinue
        }
        Get-ChildItem -Path . -Name ".pytest_cache" -Recurse -Directory | ForEach-Object { 
            Remove-Item $_ -Recurse -Force -ErrorAction SilentlyContinue
        }
        Remove-Item ".coverage" -Force -ErrorAction SilentlyContinue
        Remove-Item "htmlcov" -Recurse -Force -ErrorAction SilentlyContinue
        Remove-Item "report.html" -Force -ErrorAction SilentlyContinue
        Write-Success "Cleanup completed"
        exit 0
    }
}

$ExitCode = $LASTEXITCODE

if ($ExitCode -eq 0) {
    Write-Success "Tests completed successfully!"
} else {
    Write-Error-Custom "Some tests failed! (Exit code: $ExitCode)"
}

if (-not $KeepVenv) {
    deactivate
}

exit $ExitCode
