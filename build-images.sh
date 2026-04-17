#!/bin/bash
# BrainCell Docker Image Builder and Publisher (Bash version)

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
ACTION=${1:-build}
COMPONENT=${2:-all}
VERSION=${3:-latest}
REGISTRY=${REGISTRY:-docker.io}
REPOSITORY=${REPOSITORY:-itlbraincell}
NO_CACHE=${NO_CACHE:-false}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"

info "BrainCell Docker Image Builder"
info "Registry: $REGISTRY"
info "Repository: $REPOSITORY"
info "Version: $VERSION"
info "Component: $COMPONENT"
echo ""

# Component configurations
declare -A COMPONENTS

# API
COMPONENTS[api_name]="api"
COMPONENTS[api_display]="BrainCell API"
COMPONENTS[api_dockerfile]="src/api/Dockerfile"
COMPONENTS[api_context]="."
COMPONENTS[api_image]="$REGISTRY/$REPOSITORY/api"

# MCP
COMPONENTS[mcp_name]="mcp"
COMPONENTS[mcp_display]="BrainCell MCP Server"
COMPONENTS[mcp_dockerfile]="mcp/Dockerfile"
COMPONENTS[mcp_context]="."
COMPONENTS[mcp_image]="$REGISTRY/$REPOSITORY/mcp"

# Web
COMPONENTS[web_name]="web"
COMPONENTS[web_display]="BrainCell Web Dashboard"
COMPONENTS[web_dockerfile]="src/web/Dockerfile"
COMPONENTS[web_context]="."
COMPONENTS[web_image]="$REGISTRY/$REPOSITORY/web"

# Build Docker image
build_image() {
    local comp=$1
    local display="${COMPONENTS[${comp}_display]}"
    local dockerfile="${COMPONENTS[${comp}_dockerfile]}"
    local context="${COMPONENTS[${comp}_context]}"
    local image="${COMPONENTS[${comp}_image]}"
    local full_tag="${image}:${VERSION}"
    
    info "Building $display..."
    info "  Dockerfile: $dockerfile"
    info "  Context: $context"
    info "  Tag: $full_tag"
    
    local build_args=(
        "build"
        "-f" "$dockerfile"
        "-t" "$full_tag"
    )
    
    if [ "$NO_CACHE" = "true" ]; then
        build_args+=("--no-cache")
    fi
    
    # Add build arguments
    build_args+=(
        "--build-arg" "VERSION=$VERSION"
        "--build-arg" "BUILD_DATE=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
        "--build-arg" "VCS_REF=$(git rev-parse --short HEAD 2>/dev/null || echo 'unknown')"
    )
    
    build_args+=("$context")
    
    if docker "${build_args[@]}"; then
        success "Built: $full_tag"
        return 0
    else
        error "Failed to build: $full_tag"
        return 1
    fi
}

# Push Docker image
push_image() {
    local comp=$1
    local display="${COMPONENTS[${comp}_display]}"
    local image="${COMPONENTS[${comp}_image]}"
    local full_tag="${image}:${VERSION}"
    
    info "Pushing $display to $REGISTRY..."
    info "  Tag: $full_tag"
    
    if docker push "$full_tag"; then
        success "Pushed: $full_tag"
        return 0
    else
        error "Failed to push: $full_tag"
        return 1
    fi
}

# Tag Docker image
tag_image() {
    local comp=$1
    local new_tag=$2
    local display="${COMPONENTS[${comp}_display]}"
    local image="${COMPONENTS[${comp}_image]}"
    local source_tag="${image}:${VERSION}"
    local target_tag="${image}:${new_tag}"
    
    info "Tagging $display..."
    info "  From: $source_tag"
    info "  To: $target_tag"
    
    if docker tag "$source_tag" "$target_tag"; then
        success "Tagged: $target_tag"
        return 0
    else
        error "Failed to tag: $target_tag"
        return 1
    fi
}

# Determine components to process
PROCESS_COMPONENTS=()
if [ "$COMPONENT" = "all" ]; then
    PROCESS_COMPONENTS=("api" "mcp" "web")
else
    PROCESS_COMPONENTS=("$COMPONENT")
fi

# Check Docker is running
if ! docker info >/dev/null 2>&1; then
    error "Docker is not running. Please start Docker and try again."
fi

# Check registry authentication for push operations
if [ "$ACTION" = "push" ] || [ "$ACTION" = "build-push" ]; then
    info "Checking registry authentication..."
    
    if ! docker system info 2>&1 | grep -q "Registry:"; then
        warning "You may not be logged in to $REGISTRY"
        info "Run: docker login $REGISTRY"
        
        read -p "Continue anyway? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 0
        fi
    fi
fi

# Main action logic
ALL_SUCCESS=true

case $ACTION in
    build)
        for comp in "${PROCESS_COMPONENTS[@]}"; do
            if ! build_image "$comp"; then
                ALL_SUCCESS=false
            fi
        done
        ;;
        
    push)
        for comp in "${PROCESS_COMPONENTS[@]}"; do
            if ! push_image "$comp"; then
                ALL_SUCCESS=false
            fi
        done
        ;;
        
    build-push)
        for comp in "${PROCESS_COMPONENTS[@]}"; do
            if build_image "$comp"; then
                if ! push_image "$comp"; then
                    ALL_SUCCESS=false
                fi
            else
                ALL_SUCCESS=false
            fi
        done
        ;;
        
    tag)
        read -p "Enter new tag: " NEW_TAG
        for comp in "${PROCESS_COMPONENTS[@]}"; do
            if ! tag_image "$comp" "$NEW_TAG"; then
                ALL_SUCCESS=false
            fi
        done
        ;;
        
    *)
        echo "Usage: $0 {build|push|build-push|tag} [component] [version]"
        echo ""
        echo "Actions:"
        echo "  build       - Build Docker images"
        echo "  push        - Push Docker images to registry"
        echo "  build-push  - Build and push Docker images"
        echo "  tag         - Tag images with new version"
        echo ""
        echo "Components: api, mcp, web, all (default: all)"
        echo "Version: Image tag version (default: latest)"
        echo ""
        echo "Environment variables:"
        echo "  REGISTRY    - Docker registry (default: docker.io)"
        echo "  REPOSITORY  - Repository name (default: itlbraincell)"
        echo "  NO_CACHE    - Build without cache (default: false)"
        exit 1
        ;;
esac

echo ""
if $ALL_SUCCESS; then
    success "All operations completed successfully!"
    
    if [ "$ACTION" = "build" ] || [ "$ACTION" = "build-push" ]; then
        echo ""
        info "Built images:"
        for comp in "${PROCESS_COMPONENTS[@]}"; do
            image="${COMPONENTS[${comp}_image]}"
            info "  - ${image}:${VERSION}"
        done
    fi
    
    if [ "$ACTION" = "push" ] || [ "$ACTION" = "build-push" ]; then
        echo ""
        info "To deploy these images:"
        info "  helm upgrade braincell charts/ITL.Braincell \\"
        info "    --set api.image.tag=$VERSION \\"
        info "    --set mcp.image.tag=$VERSION \\"
        info "    --set web.image.tag=$VERSION"
    fi
else
    error "Some operations failed. Check the output above for details."
fi
