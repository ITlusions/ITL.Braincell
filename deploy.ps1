#!/usr/bin/env pwsh
# BrainCell Kubernetes Deployment Manager
# Automates deployment of BrainCell to Kubernetes clusters

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("install", "upgrade", "uninstall", "status", "rollback")]
    [string]$Action = "install",
    
    [Parameter(Mandatory=$false)]
    [ValidateSet("development", "staging", "production")]
    [string]$Environment = "development",
    
    [Parameter(Mandatory=$false)]
    [string]$Namespace = "",
    
    [Parameter(Mandatory=$false)]
    [string]$Version = "",
    
    [Parameter(Mandatory=$false)]
    [switch]$DryRun,
    
    [Parameter(Mandatory=$false)]
    [switch]$Wait,
    
    [Parameter(Mandatory=$false)]
    [int]$Timeout = 600
)

$ErrorActionPreference = "Stop"

# Color output
function Write-Success { Write-Host "✓ $args" -ForegroundColor Green }
function Write-Info { Write-Host "ℹ $args" -ForegroundColor Cyan }
function Write-Warning { Write-Host "⚠ $args" -ForegroundColor Yellow }
function Write-Error { Write-Host "✗ $args" -ForegroundColor Red }

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = $scriptDir
$chartsDir = Join-Path $projectRoot "charts\ITL.Braincell"

# Default namespace based on environment
if ([string]::IsNullOrEmpty($Namespace)) {
    $Namespace = switch ($Environment) {
        "production" { "braincell" }
        "staging" { "braincell-staging" }
        "development" { "braincell-dev" }
    }
}

Write-Info "BrainCell Kubernetes Deployment Manager"
Write-Info "Environment: $Environment"
Write-Info "Namespace: $Namespace"
Write-Info "Action: $Action"
if ($DryRun) { Write-Warning "DRY RUN MODE - No changes will be made" }
Write-Info ""

# Check prerequisites
function Test-Prerequisites {
    Write-Info "Checking prerequisites..."
    
    # Check kubectl
    try {
        $kubectlVersion = kubectl version --client --output=json 2>$null | ConvertFrom-Json
        Write-Success "kubectl found: $($kubectlVersion.clientVersion.gitVersion)"
    } catch {
        Write-Error "kubectl not found. Please install kubectl."
        exit 1
    }
    
    # Check Helm
    try {
        $helmVersion = helm version --short 2>$null
        Write-Success "Helm found: $helmVersion"
    } catch {
        Write-Error "Helm not found. Please install Helm 3."
        exit 1
    }
    
    # Check cluster connection
    try {
        $clusterInfo = kubectl cluster-info 2>$null
        Write-Success "Connected to Kubernetes cluster"
    } catch {
        Write-Error "Cannot connect to Kubernetes cluster. Check your kubeconfig."
        exit 1
    }
    
    # Check Helm chart exists
    if (-not (Test-Path $chartsDir)) {
        Write-Error "Helm chart not found at: $chartsDir"
        exit 1
    }
    Write-Success "Helm chart found"
    
    Write-Info ""
}

# Update Helm dependencies
function Update-HelmDependencies {
    Write-Info "Updating Helm dependencies..."
    
    Push-Location $chartsDir
    try {
        # Add required Helm repos
        helm repo add cloudnative-pg https://cloudnative-pg.github.io/charts --force-update
        helm repo add semitechnologies https://weaviate.github.io/weaviate-helm --force-update
        helm repo add traefik https://traefik.github.io/charts --force-update
        helm repo update
        
        # Update dependencies
        helm dependency update
        
        Write-Success "Helm dependencies updated"
    } catch {
        Write-Error "Failed to update Helm dependencies: $_"
        exit 1
    } finally {
        Pop-Location
    }
    
    Write-Info ""
}

# Install or upgrade release
function Deploy-Release {
    param(
        [string]$Action
    )
    
    $releaseName = "braincell"
    $valuesFile = Join-Path $chartsDir "values-$Environment.yaml"
    
    # Check if values file exists
    if (-not (Test-Path $valuesFile)) {
        Write-Warning "Environment-specific values file not found: $valuesFile"
        Write-Info "Using default values.yaml"
        $valuesFile = Join-Path $chartsDir "values.yaml"
    }
    
    # Build Helm command
    $helmArgs = @()
    
    if ($Action -eq "install") {
        $helmArgs += "install", $releaseName
    } else {
        $helmArgs += "upgrade", $releaseName, "--install"
    }
    
    $helmArgs += $chartsDir
    $helmArgs += "--namespace", $Namespace
    $helmArgs += "--create-namespace"
    $helmArgs += "--values", $valuesFile
    
    if (-not [string]::IsNullOrEmpty($Version)) {
        $helmArgs += "--set", "api.image.tag=$Version"
        $helmArgs += "--set", "mcp.image.tag=$Version"
        $helmArgs += "--set", "web.image.tag=$Version"
    }
    
    if ($Wait) {
        $helmArgs += "--wait"
        $helmArgs += "--timeout", "${Timeout}s"
    }
    
    if ($DryRun) {
        $helmArgs += "--dry-run", "--debug"
    }
    
    Write-Info "Deploying BrainCell..."
    Write-Info "Release: $releaseName"
    Write-Info "Chart: $chartsDir"
    Write-Info "Values: $valuesFile"
    
    if (-not [string]::IsNullOrEmpty($Version)) {
        Write-Info "Version: $Version"
    }
    
    Write-Info ""
    Write-Info "Running: helm $($helmArgs -join ' ')"
    Write-Info ""
    
    try {
        & helm @helmArgs
        
        if ($LASTEXITCODE -eq 0) {
            Write-Success ""
            Write-Success "Deployment successful!"
            
            if (-not $DryRun) {
                Write-Info ""
                Write-Info "Check deployment status:"
                Write-Info "  kubectl get pods -n $Namespace"
                Write-Info "  helm status $releaseName -n $Namespace"
            }
        } else {
            Write-Error "Deployment failed!"
            exit 1
        }
    } catch {
        Write-Error "Error during deployment: $_"
        exit 1
    }
}

# Uninstall release
function Remove-Release {
    $releaseName = "braincell"
    
    Write-Warning "Uninstalling BrainCell from namespace: $Namespace"
    Write-Warning "This will remove all resources including data!"
    
    if (-not $DryRun) {
        $confirm = Read-Host "Are you sure? Type 'yes' to continue"
        if ($confirm -ne "yes") {
            Write-Info "Uninstall cancelled"
            exit 0
        }
    }
    
    Write-Info "Uninstalling release: $releaseName"
    
    try {
        if ($DryRun) {
            Write-Info "DRY RUN: Would run: helm uninstall $releaseName -n $Namespace"
        } else {
            helm uninstall $releaseName -n $Namespace
            
            if ($LASTEXITCODE -eq 0) {
                Write-Success "Release uninstalled"
                
                Write-Info ""
                Write-Info "To also remove the namespace:"
                Write-Info "  kubectl delete namespace $Namespace"
            } else {
                Write-Error "Failed to uninstall release"
                exit 1
            }
        }
    } catch {
        Write-Error "Error during uninstall: $_"
        exit 1
    }
}

# Show release status
function Show-Status {
    $releaseName = "braincell"
    
    Write-Info "Getting status for release: $releaseName"
    Write-Info ""
    
    try {
        helm status $releaseName -n $Namespace
        
        Write-Info ""
        Write-Info "Pod status:"
        kubectl get pods -n $Namespace
        
        Write-Info ""
        Write-Info "Services:"
        kubectl get services -n $Namespace
        
        Write-Info ""
        Write-Info "Ingress:"
        kubectl get ingress -n $Namespace
        
    } catch {
        Write-Error "Error getting status: $_"
        Write-Info "Release may not be installed yet"
    }
}

# Rollback release
function Rollback-Release {
    param([int]$Revision)
    
    $releaseName = "braincell"
    
    Write-Warning "Rolling back release: $releaseName"
    
    if ($Revision -eq 0) {
        Write-Info "Getting release history..."
        helm history $releaseName -n $Namespace
        
        $Revision = Read-Host "Enter revision number to rollback to"
    }
    
    Write-Info "Rolling back to revision: $Revision"
    
    try {
        if ($DryRun) {
            Write-Info "DRY RUN: Would run: helm rollback $releaseName $Revision -n $Namespace"
        } else {
            helm rollback $releaseName $Revision -n $Namespace --wait
            
            if ($LASTEXITCODE -eq 0) {
                Write-Success "Rollback successful!"
            } else {
                Write-Error "Rollback failed!"
                exit 1
            }
        }
    } catch {
        Write-Error "Error during rollback: $_"
        exit 1
    }
}

# Main script execution
Test-Prerequisites

switch ($Action) {
    "install" {
        Update-HelmDependencies
        Deploy-Release -Action "install"
    }
    
    "upgrade" {
        Update-HelmDependencies
        Deploy-Release -Action "upgrade"
    }
    
    "uninstall" {
        Remove-Release
    }
    
    "status" {
        Show-Status
    }
    
    "rollback" {
        Rollback-Release -Revision 0
    }
}

Write-Info ""
Write-Success "Done!"
