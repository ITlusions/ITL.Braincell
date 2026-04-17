#!/bin/bash
# BrainCell Kubernetes Secrets Manager (Bash version)

set -e

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

info() { echo -e "${CYAN}ℹ${NC} $*"; }
success() { echo -e "${GREEN}✓${NC} $*"; }
warning() { echo -e "${YELLOW}⚠${NC} $*"; }
error() { echo -e "${RED}✗${NC} $*"; exit 1; }

# Generate secure random password
generate_password() {
    local length=${1:-32}
    openssl rand -base64 $((length * 3 / 4)) | tr -d '\n' | head -c $length
}

# Parse arguments
ACTION=${1:-generate}
ENVIRONMENT=${2:-development}
NAMESPACE=${3:-braincell}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
SECRETS_DIR="$SCRIPT_DIR/secrets"
GENERATED_DIR="$SECRETS_DIR/generated"
ENV_DIR="$GENERATED_DIR/$ENVIRONMENT"

info "BrainCell Kubernetes Secrets Manager"
info "Environment: $ENVIRONMENT"
info "Namespace: $NAMESPACE"
echo ""

case $ACTION in
    generate)
        info "Generating secrets for environment: $ENVIRONMENT"
        
        mkdir -p "$ENV_DIR"
        
        # Generate passwords
        POSTGRES_PASSWORD=$(generate_password 32)
        WEAVIATE_API_KEY=$(generate_password 64)
        OIDC_SECRET=$(generate_password 32)
        JWT_SECRET=$(generate_password 64)
        REDIS_PASSWORD=$(generate_password 32)
        AZURE_KEY=$(generate_password 64)
        
        # Generate postgres secret
        cat > "$ENV_DIR/postgres-secret.yaml" <<EOF
apiVersion: v1
kind: Secret
metadata:
  name: braincell-postgres-secret
  namespace: $NAMESPACE
type: Opaque
stringData:
  password: "$POSTGRES_PASSWORD"
  username: "braincell"
  database: "braincell"
  connectionString: "postgresql://braincell:$POSTGRES_PASSWORD@braincell-postgres:5432/braincell"
EOF
        success "Generated: postgres-secret.yaml"
        
        # Generate weaviate secret
        cat > "$ENV_DIR/weaviate-secret.yaml" <<EOF
apiVersion: v1
kind: Secret
metadata:
  name: braincell-weaviate-secret
  namespace: $NAMESPACE
type: Opaque
stringData:
  api-key: "$WEAVIATE_API_KEY"
  oidc-client-secret: "$OIDC_SECRET"
EOF
        success "Generated: weaviate-secret.yaml"
        
        # Generate API secret
        cat > "$ENV_DIR/api-secret.yaml" <<EOF
apiVersion: v1
kind: Secret
metadata:
  name: braincell-api-secret
  namespace: $NAMESPACE
type: Opaque
stringData:
  jwt-secret: "$JWT_SECRET"
  openai-api-key: "sk-PLACEHOLDER-SET-THIS-MANUALLY"
  redis-password: "$REDIS_PASSWORD"
EOF
        success "Generated: api-secret.yaml"
        
        # Generate backup secret
        cat > "$ENV_DIR/backup-secret.yaml" <<EOF
apiVersion: v1
kind: Secret
metadata:
  name: s3-backup-credentials
  namespace: $NAMESPACE
type: Opaque
stringData:
  aws-access-key-id: "AKIAIOSFODNN7EXAMPLE"
  aws-secret-access-key: "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
  azure-storage-account: "youraccountname"
  azure-storage-key: "$AZURE_KEY"
EOF
        success "Generated: backup-secret.yaml"
        
        echo ""
        warning "IMPORTANT: Review and update the generated secrets before applying!"
        warning "Location: $ENV_DIR"
        warning "Especially update API keys that cannot be auto-generated."
        echo ""
        info "To apply secrets, run: ./manage-secrets.sh apply $ENVIRONMENT $NAMESPACE"
        ;;
        
    apply)
        info "Applying secrets to Kubernetes cluster"
        
        if [ ! -d "$ENV_DIR" ]; then
            error "No secrets found for environment: $ENVIRONMENT. Run 'generate' first."
        fi
        
        # Check kubectl connection
        if ! kubectl cluster-info &>/dev/null; then
            error "Cannot connect to Kubernetes cluster. Check your kubectl configuration."
        fi
        
        # Create namespace
        info "Ensuring namespace exists: $NAMESPACE"
        kubectl create namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f - >/dev/null
        
        # Apply all secrets
        for file in "$ENV_DIR"/*.yaml; do
            filename=$(basename "$file")
            info "Applying secret: $filename"
            if kubectl apply -f "$file" -n "$NAMESPACE"; then
                success "Applied: $filename"
            else
                error "Failed to apply: $filename"
            fi
        done
        
        echo ""
        success "All secrets applied successfully!"
        ;;
        
    delete)
        warning "Deleting all BrainCell secrets from namespace: $NAMESPACE"
        read -p "Press Enter to continue or Ctrl+C to cancel"
        
        SECRETS=(
            "braincell-postgres-secret"
            "braincell-weaviate-secret"
            "braincell-api-secret"
            "s3-backup-credentials"
        )
        
        for secret in "${SECRETS[@]}"; do
            info "Deleting secret: $secret"
            kubectl delete secret "$secret" -n "$NAMESPACE" --ignore-not-found
        done
        
        success "Secrets deleted"
        ;;
        
    validate)
        info "Validating secrets in namespace: $NAMESPACE"
        
        SECRETS=(
            "braincell-postgres-secret"
            "braincell-weaviate-secret"
            "braincell-api-secret"
        )
        
        ALL_VALID=true
        
        for secret in "${SECRETS[@]}"; do
            if kubectl get secret "$secret" -n "$NAMESPACE" &>/dev/null; then
                success "Found: $secret"
                keys=$(kubectl get secret "$secret" -n "$NAMESPACE" -o jsonpath='{.data}' | jq -r 'keys[]' 2>/dev/null)
                if [ -n "$keys" ]; then
                    info "  Keys: $(echo $keys | tr '\n' ', ')"
                else
                    warning "  Secret exists but has no data"
                    ALL_VALID=false
                fi
            else
                error "Missing: $secret"
                ALL_VALID=false
            fi
        done
        
        if $ALL_VALID; then
            echo ""
            success "All secrets are valid!"
        else
            echo ""
            warning "Some secrets are missing or invalid"
        fi
        ;;
        
    *)
        echo "Usage: $0 {generate|apply|delete|validate} [environment] [namespace]"
        echo ""
        echo "Actions:"
        echo "  generate  - Generate secrets from templates"
        echo "  apply     - Apply secrets to Kubernetes"
        echo "  delete    - Delete secrets from Kubernetes"
        echo "  validate  - Validate existing secrets"
        echo ""
        echo "Environments: development, staging, production"
        echo "Default namespace: braincell"
        exit 1
        ;;
esac
