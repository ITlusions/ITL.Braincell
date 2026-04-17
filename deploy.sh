#!/bin/bash
# BrainCell Kubernetes Deployment Manager (Bash version)

set -e

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

info() { echo -e "${CYAN}ℹ${NC} $*"; }
success() { echo -e "${GREEN}✓${NC} $*"; }
warning() { echo -e "${YELLOW}⚠${NC} $*"; }
error() { echo -e "${RED}✗${NC} $*"; exit 1; }

# Default parameters
ACTION=${1:-install}
ENVIRONMENT=${2:-development}
VERSION=${3:-}
DRY_RUN=${DRY_RUN:-false}
WAIT=${WAIT:-true}
TIMEOUT=${TIMEOUT:-600}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"
CHARTS_DIR="$PROJECT_ROOT/charts/ITL.Braincell"

# Determine namespace
case $ENVIRONMENT in
    production)
        NAMESPACE="braincell"
        ;;
    staging)
        NAMESPACE="braincell-staging"
        ;;
    development)
        NAMESPACE="braincell-dev"
        ;;
    *)
        NAMESPACE="braincell"
        ;;
esac

info "BrainCell Kubernetes Deployment Manager"
info "Environment: $ENVIRONMENT"
info "Namespace: $NAMESPACE"
info "Action: $ACTION"
[ "$DRY_RUN" = "true" ] && warning "DRY RUN MODE - No changes will be made"
echo ""

# Check prerequisites
check_prerequisites() {
    info "Checking prerequisites..."
    
    # Check kubectl
    if command -v kubectl &>/dev/null; then
        KUBECTL_VERSION=$(kubectl version --client --short 2>/dev/null | head -n1)
        success "kubectl found: $KUBECTL_VERSION"
    else
        error "kubectl not found. Please install kubectl."
    fi
    
    # Check Helm
    if command -v helm &>/dev/null; then
        HELM_VERSION=$(helm version --short 2>/dev/null)
        success "Helm found: $HELM_VERSION"
    else
        error "Helm not found. Please install Helm 3."
    fi
    
    # Check cluster connection
    if kubectl cluster-info &>/dev/null; then
        success "Connected to Kubernetes cluster"
    else
        error "Cannot connect to Kubernetes cluster. Check your kubeconfig."
    fi
    
    # Check Helm chart exists
    if [ ! -d "$CHARTS_DIR" ]; then
        error "Helm chart not found at: $CHARTS_DIR"
    fi
    success "Helm chart found"
    
    echo ""
}

# Update Helm dependencies
update_helm_dependencies() {
    info "Updating Helm dependencies..."
    
    cd "$CHARTS_DIR"
    
    # Add required Helm repos
    helm repo add cloudnative-pg https://cloudnative-pg.github.io/charts --force-update
    helm repo add semitechnologies https://weaviate.github.io/weaviate-helm --force-update
    helm repo add traefik https://traefik.github.io/charts --force-update
    helm repo update
    
    # Update dependencies
    helm dependency update
    
    success "Helm dependencies updated"
    cd "$PROJECT_ROOT"
    echo ""
}

# Install or upgrade release
deploy_release() {
    local action=$1
    local release_name="braincell"
    local values_file="$CHARTS_DIR/values-$ENVIRONMENT.yaml"
    
    # Check if values file exists
    if [ ! -f "$values_file" ]; then
        warning "Environment-specific values file not found: $values_file"
        info "Using default values.yaml"
        values_file="$CHARTS_DIR/values.yaml"
    fi
    
    # Build Helm command
    local helm_args=()
    
    if [ "$action" = "install" ]; then
        helm_args+=("install" "$release_name")
    else
        helm_args+=("upgrade" "$release_name" "--install")
    fi
    
    helm_args+=(
        "$CHARTS_DIR"
        "--namespace" "$NAMESPACE"
        "--create-namespace"
        "--values" "$values_file"
    )
    
    if [ -n "$VERSION" ]; then
        helm_args+=(
            "--set" "api.image.tag=$VERSION"
            "--set" "mcp.image.tag=$VERSION"
            "--set" "web.image.tag=$VERSION"
        )
    fi
    
    if [ "$WAIT" = "true" ]; then
        helm_args+=("--wait" "--timeout" "${TIMEOUT}s")
    fi
    
    if [ "$DRY_RUN" = "true" ]; then
        helm_args+=("--dry-run" "--debug")
    fi
    
    info "Deploying BrainCell..."
    info "Release: $release_name"
    info "Chart: $CHARTS_DIR"
    info "Values: $values_file"
    [ -n "$VERSION" ] && info "Version: $VERSION"
    echo ""
    info "Running: helm ${helm_args[*]}"
    echo ""
    
    if helm "${helm_args[@]}"; then
        success ""
        success "Deployment successful!"
        
        if [ "$DRY_RUN" != "true" ]; then
            echo ""
            info "Check deployment status:"
            info "  kubectl get pods -n $NAMESPACE"
            info "  helm status $release_name -n $NAMESPACE"
        fi
    else
        error "Deployment failed!"
    fi
}

# Uninstall release
uninstall_release() {
    local release_name="braincell"
    
    warning "Uninstalling BrainCell from namespace: $NAMESPACE"
    warning "This will remove all resources including data!"
    
    if [ "$DRY_RUN" != "true" ]; then
        read -p "Are you sure? Type 'yes' to continue: " confirm
        if [ "$confirm" != "yes" ]; then
            info "Uninstall cancelled"
            exit 0
        fi
    fi
    
    info "Uninstalling release: $release_name"
    
    if [ "$DRY_RUN" = "true" ]; then
        info "DRY RUN: Would run: helm uninstall $release_name -n $NAMESPACE"
    else
        if helm uninstall "$release_name" -n "$NAMESPACE"; then
            success "Release uninstalled"
            echo ""
            info "To also remove the namespace:"
            info "  kubectl delete namespace $NAMESPACE"
        else
            error "Failed to uninstall release"
        fi
    fi
}

# Show release status
show_status() {
    local release_name="braincell"
    
    info "Getting status for release: $release_name"
    echo ""
    
    if helm status "$release_name" -n "$NAMESPACE" 2>/dev/null; then
        echo ""
        info "Pod status:"
        kubectl get pods -n "$NAMESPACE"
        
        echo ""
        info "Services:"
        kubectl get services -n "$NAMESPACE"
        
        echo ""
        info "Ingress:"
        kubectl get ingress -n "$NAMESPACE" 2>/dev/null || info "No ingress found"
    else
        warning "Release may not be installed yet"
    fi
}

# Rollback release
rollback_release() {
    local release_name="braincell"
    local revision=$1
    
    warning "Rolling back release: $release_name"
    
    if [ -z "$revision" ]; then
        info "Getting release history..."
        helm history "$release_name" -n "$NAMESPACE"
        
        read -p "Enter revision number to rollback to: " revision
    fi
    
    info "Rolling back to revision: $revision"
    
    if [ "$DRY_RUN" = "true" ]; then
        info "DRY RUN: Would run: helm rollback $release_name $revision -n $NAMESPACE"
    else
        if helm rollback "$release_name" "$revision" -n "$NAMESPACE" --wait; then
            success "Rollback successful!"
        else
            error "Rollback failed!"
        fi
    fi
}

# Main script execution
check_prerequisites

case $ACTION in
    install)
        update_helm_dependencies
        deploy_release "install"
        ;;
        
    upgrade)
        update_helm_dependencies
        deploy_release "upgrade"
        ;;
        
    uninstall)
        uninstall_release
        ;;
        
    status)
        show_status
        ;;
        
    rollback)
        rollback_release "${VERSION}"
        ;;
        
    *)
        echo "Usage: $0 {install|upgrade|uninstall|status|rollback} [environment] [version]"
        echo ""
        echo "Actions:"
        echo "  install    - Install BrainCell to Kubernetes"
        echo "  upgrade    - Upgrade existing installation"
        echo "  uninstall  - Remove BrainCell from Kubernetes"
        echo "  status     - Show deployment status"
        echo "  rollback   - Rollback to previous version"
        echo ""
        echo "Environments: development, staging, production (default: development)"
        echo "Version: Image tag version (optional)"
        echo ""
        echo "Environment variables:"
        echo "  DRY_RUN - Set to 'true' for dry run"
        echo "  WAIT    - Set to 'false' to not wait for deployment"
        echo "  TIMEOUT - Deployment timeout in seconds (default: 600)"
        exit 1
        ;;
esac

echo ""
success "Done!"
