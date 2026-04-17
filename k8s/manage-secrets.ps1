#!/usr/bin/env pwsh
# BrainCell Kubernetes Secrets Manager
# This script helps generate and apply Kubernetes secrets securely

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("generate", "apply", "delete", "validate")]
    [string]$Action = "generate",
    
    [Parameter(Mandatory=$false)]
    [ValidateSet("development", "staging", "production")]
    [string]$Environment = "development",
    
    [Parameter(Mandatory=$false)]
    [string]$Namespace = "braincell"
)

$ErrorActionPreference = "Stop"

# Color output functions
function Write-Success { Write-Host "✓ $args" -ForegroundColor Green }
function Write-Info { Write-Host "ℹ $args" -ForegroundColor Cyan }
function Write-Warning { Write-Host "⚠ $args" -ForegroundColor Yellow }
function Write-Error { Write-Host "✗ $args" -ForegroundColor Red }

# Generate secure random password
function New-SecurePassword {
    param([int]$Length = 32)
    
    $chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()_+-='
    $password = -join ((1..$Length) | ForEach-Object { $chars[(Get-Random -Maximum $chars.Length)] })
    return $password
}

# Generate secrets file from template
function New-SecretsFile {
    param(
        [string]$TemplatePath,
        [string]$OutputPath
    )
    
    Write-Info "Generating secrets file from template: $TemplatePath"
    
    if (-not (Test-Path $TemplatePath)) {
        Write-Error "Template file not found: $TemplatePath"
        return $false
    }
    
    $content = Get-Content $TemplatePath -Raw
    
    # Replace placeholders with generated passwords
    $replacements = @{
        "CHANGE_ME_STRONG_PASSWORD" = New-SecurePassword -Length 32
        "CHANGE_ME_WEAVIATE_API_KEY" = New-SecurePassword -Length 64
        "CHANGE_ME_OIDC_CLIENT_SECRET" = New-SecurePassword -Length 32
        "CHANGE_ME_JWT_SECRET_KEY_MIN_32_CHARS" = New-SecurePassword -Length 64
        "CHANGE_ME_OPENAI_API_KEY" = "sk-PLACEHOLDER-SET-THIS-MANUALLY"
        "CHANGE_ME_REDIS_PASSWORD" = New-SecurePassword -Length 32
        "CHANGE_ME_AWS_ACCESS_KEY" = "AKIAIOSFODNN7EXAMPLE"
        "CHANGE_ME_AWS_SECRET_KEY" = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
        "CHANGE_ME_AZURE_ACCOUNT" = "youraccountname"
        "CHANGE_ME_AZURE_KEY" = (New-SecurePassword -Length 64)
    }
    
    foreach ($key in $replacements.Keys) {
        $content = $content -replace [regex]::Escape($key), $replacements[$key]
    }
    
    # Update namespace if different
    $content = $content -replace 'namespace: braincell', "namespace: $Namespace"
    
    # Save to output file
    $content | Out-File -FilePath $OutputPath -Encoding UTF8 -NoNewline
    
    Write-Success "Generated secrets file: $OutputPath"
    return $true
}

# Main script logic
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir
$secretsDir = Join-Path $projectRoot "k8s\secrets"
$generatedDir = Join-Path $secretsDir "generated"
$envDir = Join-Path $generatedDir $Environment

Write-Info "BrainCell Kubernetes Secrets Manager"
Write-Info "Environment: $Environment"
Write-Info "Namespace: $Namespace"
Write-Info ""

switch ($Action) {
    "generate" {
        Write-Info "Generating secrets for environment: $Environment"
        
        # Create generated directory
        if (-not (Test-Path $generatedDir)) {
            New-Item -ItemType Directory -Path $generatedDir -Force | Out-Null
        }
        
        if (-not (Test-Path $envDir)) {
            New-Item -ItemType Directory -Path $envDir -Force | Out-Null
        }
        
        # Generate secrets from templates
        $templates = @(
            "postgres-secret.template.yaml",
            "weaviate-secret.template.yaml",
            "api-secret.template.yaml",
            "backup-secret.template.yaml"
        )
        
        foreach ($template in $templates) {
            $templatePath = Join-Path $secretsDir $template
            $outputFile = $template -replace ".template.yaml", ".yaml"
            $outputPath = Join-Path $envDir $outputFile
            
            New-SecretsFile -TemplatePath $templatePath -OutputPath $outputPath
        }
        
        Write-Warning ""
        Write-Warning "IMPORTANT: Review and update the generated secrets before applying!"
        Write-Warning "Location: $envDir"
        Write-Warning "Especially update API keys that cannot be auto-generated."
        Write-Warning ""
        Write-Info "To apply secrets, run: .\manage-secrets.ps1 -Action apply -Environment $Environment"
    }
    
    "apply" {
        Write-Info "Applying secrets to Kubernetes cluster"
        
        if (-not (Test-Path $envDir)) {
            Write-Error "No secrets found for environment: $Environment"
            Write-Info "Run with -Action generate first"
            exit 1
        }
        
        # Check kubectl connection
        try {
            kubectl cluster-info | Out-Null
        } catch {
            Write-Error "Cannot connect to Kubernetes cluster. Check your kubectl configuration."
            exit 1
        }
        
        # Create namespace if it doesn't exist
        Write-Info "Ensuring namespace exists: $Namespace"
        kubectl create namespace $Namespace --dry-run=client -o yaml | kubectl apply -f - | Out-Null
        
        # Apply all secrets
        $secretFiles = Get-ChildItem -Path $envDir -Filter "*.yaml"
        
        foreach ($file in $secretFiles) {
            Write-Info "Applying secret: $($file.Name)"
            kubectl apply -f $file.FullName -n $Namespace
            
            if ($LASTEXITCODE -eq 0) {
                Write-Success "Applied: $($file.Name)"
            } else {
                Write-Error "Failed to apply: $($file.Name)"
            }
        }
        
        Write-Success ""
        Write-Success "All secrets applied successfully!"
    }
    
    "delete" {
        Write-Warning "Deleting all BrainCell secrets from namespace: $Namespace"
        Read-Host "Press Enter to continue or Ctrl+C to cancel"
        
        $secretNames = @(
            "braincell-postgres-secret",
            "braincell-weaviate-secret",
            "braincell-api-secret",
            "s3-backup-credentials"
        )
        
        foreach ($secretName in $secretNames) {
            Write-Info "Deleting secret: $secretName"
            kubectl delete secret $secretName -n $Namespace --ignore-not-found
        }
        
        Write-Success "Secrets deleted"
    }
    
    "validate" {
        Write-Info "Validating secrets in namespace: $Namespace"
        
        $secretNames = @(
            "braincell-postgres-secret",
            "braincell-weaviate-secret",
            "braincell-api-secret"
        )
        
        $allValid = $true
        
        foreach ($secretName in $secretNames) {
            $secret = kubectl get secret $secretName -n $Namespace -o json 2>$null | ConvertFrom-Json
            
            if ($secret) {
                Write-Success "Found: $secretName"
                
                # Validate secret has required keys
                $data = $secret.data
                if ($data.PSObject.Properties.Count -gt 0) {
                    Write-Info "  Keys: $($data.PSObject.Properties.Name -join ', ')"
                } else {
                    Write-Warning "  Secret exists but has no data"
                    $allValid = $false
                }
            } else {
                Write-Error "Missing: $secretName"
                $allValid = $false
            }
        }
        
        if ($allValid) {
            Write-Success ""
            Write-Success "All secrets are valid!"
        } else {
            Write-Warning ""
            Write-Warning "Some secrets are missing or invalid"
        }
    }
}
