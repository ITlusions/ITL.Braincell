#!/usr/bin/env pwsh
# BrainCell Docker Image Builder and Publisher
# This script builds and pushes Docker images for all BrainCell components

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("build", "push", "build-push", "tag")]
    [string]$Action = "build",
    
    [Parameter(Mandatory=$false)]
    [string]$Registry = "docker.io",
    
    [Parameter(Mandatory=$false)]
    [string]$Repository = "itlbraincell",
    
    [Parameter(Mandatory=$false)]
    [string]$Version = "latest",
    
    [Parameter(Mandatory=$false)]
    [ValidateSet("api", "mcp", "web", "all")]
    [string]$Component = "all",
    
    [Parameter(Mandatory=$false)]
    [switch]$NoCache
)

$ErrorActionPreference = "Stop"

# Color output
function Write-Success { Write-Host "✓ $args" -ForegroundColor Green }
function Write-Info { Write-Host "ℹ $args" -ForegroundColor Cyan }
function Write-Warning { Write-Host "⚠ $args" -ForegroundColor Yellow }
function Write-Error { Write-Host "✗ $args" -ForegroundColor Red }

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = $scriptDir

Write-Info "BrainCell Docker Image Builder"
Write-Info "Registry: $Registry"
Write-Info "Repository: $Repository"
Write-Info "Version: $Version"
Write-Info "Component: $Component"
Write-Info ""

# Component configurations
$components = @{
    "api" = @{
        Name = "api"
        DisplayName = "BrainCell API"
        DockerfilePath = "src/api/Dockerfile"
        Context = "."
        ImageName = "$Registry/$Repository/api"
    }
    "mcp" = @{
        Name = "mcp"
        DisplayName = "BrainCell MCP Server"
        DockerfilePath = "mcp/Dockerfile"
        Context = "."
        ImageName = "$Registry/$Repository/mcp"
    }
    "web" = @{
        Name = "web"
        DisplayName = "BrainCell Web Dashboard"
        DockerfilePath = "src/web/Dockerfile"
        Context = "."
        ImageName = "$Registry/$Repository/web"
    }
}

# Determine which components to process
$componentsToProcess = @()
if ($Component -eq "all") {
    $componentsToProcess = $components.Values
} else {
    $componentsToProcess = @($components[$Component])
}

# Build Docker image
function Build-DockerImage {
    param(
        [hashtable]$ComponentConfig,
        [string]$Tag
    )
    
    $name = $ComponentConfig.DisplayName
    $dockerfile = $ComponentConfig.DockerfilePath
    $context = $ComponentConfig.Context
    $imageName = $ComponentConfig.ImageName
    $fullTag = "${imageName}:${Tag}"
    
    Write-Info "Building $name..."
    Write-Info "  Dockerfile: $dockerfile"
    Write-Info "  Context: $context"
    Write-Info "  Tag: $fullTag"
    
    $buildArgs = @(
        "build",
        "-f", $dockerfile,
        "-t", $fullTag,
        $context
    )
    
    if ($NoCache) {
        $buildArgs += "--no-cache"
    }
    
    # Add build arguments for versioning
    $buildArgs += "--build-arg", "VERSION=$Version"
    $buildArgs += "--build-arg", "BUILD_DATE=$(Get-Date -Format 'yyyy-MM-ddTHH:mm:ssZ')"
    $buildArgs += "--build-arg", "VCS_REF=$(git rev-parse --short HEAD 2>$null)"
    
    try {
        & docker @buildArgs
        
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Built: $fullTag"
            return $true
        } else {
            Write-Error "Failed to build: $fullTag"
            return $false
        }
    } catch {
        Write-Error "Error building $name`: $_"
        return $false
    }
}

# Push Docker image
function Push-DockerImage {
    param(
        [hashtable]$ComponentConfig,
        [string]$Tag
    )
    
    $name = $ComponentConfig.DisplayName
    $imageName = $ComponentConfig.ImageName
    $fullTag = "${imageName}:${Tag}"
    
    Write-Info "Pushing $name to $Registry..."
    Write-Info "  Tag: $fullTag"
    
    try {
        docker push $fullTag
        
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Pushed: $fullTag"
            return $true
        } else {
            Write-Error "Failed to push: $fullTag"
            return $false
        }
    } catch {
        Write-Error "Error pushing $name`: $_"
        return $false
    }
}

# Tag Docker image
function Tag-DockerImage {
    param(
        [hashtable]$ComponentConfig,
        [string]$SourceTag,
        [string]$TargetTag
    )
    
    $name = $ComponentConfig.DisplayName
    $imageName = $ComponentConfig.ImageName
    $sourceFullTag = "${imageName}:${SourceTag}"
    $targetFullTag = "${imageName}:${TargetTag}"
    
    Write-Info "Tagging $name..."
    Write-Info "  From: $sourceFullTag"
    Write-Info "  To: $targetFullTag"
    
    try {
        docker tag $sourceFullTag $targetFullTag
        
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Tagged: $targetFullTag"
            return $true
        } else {
            Write-Error "Failed to tag: $targetFullTag"
            return $false
        }
    } catch {
        Write-Error "Error tagging $name`: $_"
        return $false
    }
}

# Check Docker is running
try {
    docker info | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Docker is not running. Please start Docker and try again."
        exit 1
    }
} catch {
    Write-Error "Docker is not installed or not running"
    exit 1
}

# Check if logged in to registry
if ($Action -eq "push" -or $Action -eq "build-push") {
    Write-Info "Checking registry authentication..."
    
    # Try to get auth info
    $authCheck = docker system info 2>&1 | Select-String "Registry:"
    
    if (-not $authCheck) {
        Write-Warning "You may not be logged in to $Registry"
        Write-Info "Run: docker login $Registry"
        
        $continue = Read-Host "Continue anyway? (y/n)"
        if ($continue -ne "y") {
            exit 0
        }
    }
}

# Main action logic
$allSuccess = $true

switch ($Action) {
    "build" {
        foreach ($comp in $componentsToProcess) {
            $success = Build-DockerImage -ComponentConfig $comp -Tag $Version
            $allSuccess = $allSuccess -and $success
        }
    }
    
    "push" {
        foreach ($comp in $componentsToProcess) {
            $success = Push-DockerImage -ComponentConfig $comp -Tag $Version
            $allSuccess = $allSuccess -and $success
        }
    }
    
    "build-push" {
        foreach ($comp in $componentsToProcess) {
            $buildSuccess = Build-DockerImage -ComponentConfig $comp -Tag $Version
            
            if ($buildSuccess) {
                $pushSuccess = Push-DockerImage -ComponentConfig $comp -Tag $Version
                $allSuccess = $allSuccess -and $pushSuccess
            } else {
                $allSuccess = $false
            }
        }
    }
    
    "tag" {
        $NewTag = Read-Host "Enter new tag"
        
        foreach ($comp in $componentsToProcess) {
            $success = Tag-DockerImage -ComponentConfig $comp -SourceTag $Version -TargetTag $NewTag
            $allSuccess = $allSuccess -and $success
        }
    }
}

Write-Info ""
if ($allSuccess) {
    Write-Success "All operations completed successfully!"
    
    if ($Action -eq "build" -or $Action -eq "build-push") {
        Write-Info ""
        Write-Info "Built images:"
        foreach ($comp in $componentsToProcess) {
            $fullTag = "$($comp.ImageName):$Version"
            Write-Info "  - $fullTag"
        }
    }
    
    if ($Action -eq "push" -or $Action -eq "build-push") {
        Write-Info ""
        Write-Info "To deploy these images:"
        Write-Info "  helm upgrade braincell charts/ITL.Braincell \"
        Write-Info "    --set api.image.tag=$Version \"
        Write-Info "    --set mcp.image.tag=$Version \"
        Write-Info "    --set web.image.tag=$Version"
    }
} else {
    Write-Error "Some operations failed. Check the output above for details."
    exit 1
}
